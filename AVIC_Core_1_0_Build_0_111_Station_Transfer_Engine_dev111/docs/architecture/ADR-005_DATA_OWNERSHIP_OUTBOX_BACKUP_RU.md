# ADR-005 — Data Ownership, Outbox/Inbox и согласованное восстановление

Статус: **PROPOSED**  
Дата: 27.11.2026  
Область: все persistent services AVIC Core, Station Runtime, Edge и Central.

## 1. Принцип

AVIC не обязан хранить всё в одной базе. Раздельные хранилища могут обеспечивать изоляцию нагрузки и отказов. Но у каждого агрегата должен быть один авторитетный владелец записи, один публичный write API и документированная граница транзакции.

Нельзя считать две записи согласованными только потому, что обе находятся на одном компьютере. SQLite транзакция не охватывает две независимые БД, файлы конфигурации, outbox и удалённый Edge.

## 2. Правила владения

| Данные | Source of Truth / владелец | Потребители |
|---|---|---|
| Engineering objects и Point Definition | Object/Engineering Service | Drivers, Runtime, HMI, SDK |
| Point State и Sample acceptance | Station Point Runtime (ADR-001) | FBD, HMI, Alarms, Historian, Analytics |
| Historical samples/rollups | Historian | Trends, reports, analytics |
| Alarm lifecycle и transition journal | Alarm Manager | Event projection, notifications, analytics |
| General operational events | Event Service | UI, reports, analytics |
| Audit security/action trail | Audit Service | Security analytics, compliance |
| Notification routes/outbox | Notification Service | Email/Telegram/Push/Webhook adapters |
| Engineering dependencies | Dependency Service + relation registry | Delete/transfer/publish planners |
| Time policy and device sync permission | Time Manager | Station Runtime, BACnet adapter, scheduler |
| Configuration revisions | Configuration/Engineering Lifecycle | Runtime deployment |
| Deployment/transfer package | Deployment/Station Transfer | Target Station Runtime |
| License entitlement and usage | Licensing Service | Engineering, Runtime, point usage ledger |

Проекции, кэши, индексы и read models не являются дополнительными владельцами записи.

## 3. Transactional outbox/inbox

Для каждой межсервисной операции определить:
- aggregate owner;
- event_id и schema_version;
- outbox, записываемый в той же транзакции, что и изменение агрегата;
- delivery state, attempts, next_attempt_at, lease_until;
- consumer inbox/idempotency key;
- retry/backoff и poison-message policy;
- reconciliation job и измеримый backlog;
- поведение при заполнении диска.

Гарантия — at-least-once delivery с идемпотентными consumers, а не недоказуемое exactly-once между разными БД.

### Пример

Alarm transition:
1. В одной Alarm DB транзакции обновляется alarm state, добавляется transition event и outbox row.
2. После commit dispatcher отправляет event в Event Service / Notification Service.
3. Потребитель фиксирует event_id в своей inbox вместе с собственной записью.
4. Повторная доставка не создаёт повторную запись/уведомление.
5. Ошибка доставки оставляет outbox pending и видна в диагностике.

Текущий AlarmService уже реализует локальный transition journal + durable outbox — этот паттерн следует сохранить и стандартизировать.

## 4. Проблемы, обнаруженные в текущем коде

- CoreApplication открывает отдельные БД для objects, point_views, audit, events, dependencies, analytics, notifications, time_management, history, alarms, schedules и engineering_lifecycle.
- HistoryService отдельно хранит history_bindings и сверяет их с Point usage ledger Core при старте. Сам код называет это repair protocol, а не cross-database ACID.
- AlarmService имеет собственный transition journal и outbox.
- NotificationService имеет durable outbox и route registry, но transport sender требует отдельного adapter и фактически не реализован.
- ConfigurationManager хранит versioned JSON envelopes в файлах и lock DB; ProjectTransaction отдельно журналирует файловые и DB операции.
- В generic domain models существуют Alarm/Event/HistoryRecord, параллельно с persistent моделями специализированных сервисов. Их роль (canonical, DTO или legacy) должна быть установлена через поиск всех read/write/import/transfer paths.

Это не основание немедленно объединять БД. Это основание назначить владельцев и проверить границы согласованности.

## 5. Backup/restore: системная операция

System Backup должен фиксировать не только набор файлов, но и consistency manifest:
- backup_id, installation_id, Core schema/version и формат backup;
- snapshot barrier / время и состояние каждого владельца;
- список файлов и БД с размерами и SHA-256;
- версии схем, migration heads и совместимость;
- включённые станции, конфигурации, драйверы и модули;
- лицензия и правила переноса Host-ID (секреты/ключи не экспортируются без отдельного безопасного механизма);
- состояние outbox/inbox и незавершённых операций;
- retention/compaction metadata.

Требования:
1. Backup не создаётся как несогласованная копия открытых SQLite файлов.
2. Snapshot barrier координирует writers или использует штатный online backup/WAL checkpoint механизм каждого владельца.
3. Для multi-store snapshot фиксируется единый logical cut; если добиться его нельзя, backup явно помечается как crash-consistent и требует reconciliation.
4. Restore сначала выполняется в изолированную staging область.
5. Проверяются хэши, схема, совместимость, целостность журналов, foreign references, outbox/inbox и license binding.
6. Только после успешной проверки выполняется controlled activation с rollback.
7. После восстановления запускаются reconciliation jobs; они должны быть идемпотентными и давать отчёт о каждой коррекции.
8. Для Edge автономное состояние и несинхронизированные события должны быть представлены в backup manifest.

## 6. Retention, compaction и дисковое пространство

Каждый владелец задаёт:
- retention по типам данных;
- максимальный объём и скорость роста;
- archive/export policy;
- compaction/checkpoint policy;
- минимальный свободный резерв диска;
- предупреждение и критическое состояние;
- реакцию на disk full.

Нельзя автоматически удалять audit/security events, незавершённые alarm transitions или несинхронизированные Edge события без явной политики и следа аудита.

## 7. Архитектурные запреты

- Никаких прямых SQL writes в чужую БД.
- Никакого cross-database "сначала записали здесь, потом там" без компенсации/reconciliation.
- Никакого изменения generic entity, если за агрегат отвечает специализированный service.
- Никакой доставки события только in-memory callback без durable recovery для критических событий.
- Никакого backup/restore, который сообщает SUCCESS до проверки целостности и восстановления.
- Никакого удаления объекта до проверяемого dependency/change plan.
- Никакой зависимости Edge Runtime от доступности Central для локальной работы.

## 8. Acceptance tests

- каталог владельцев агрегатов существует и покрывает все таблицы/файловые хранилища;
- архитектурный тест запрещает чужие direct writes;
- outbox и aggregate commit атомарны;
- consumer inbox обеспечивает идемпотентность при повторной доставке;
- crash injection после каждого шага межсервисной операции;
- recovery/reconciliation безопасно повторяется;
- NotificationService показывает честный QUEUED_NO_TRANSPORT до подключения sender;
- backup при активных writes восстанавливается в согласованное состояние;
- corrupted hash/schema/partial file restore блокирует activation;
- backup restore round-trip подтверждает counts, revisions, references, event chains и pending outbox;
- disk-full и outbox backlog переводят сервис в явный degraded mode;
- миграция generic Alarm/Event/HistoryRecord не теряет transfer/API compatibility.

## 9. Проверка по трём системам

- **Niagara:** сохраняем согласованную объектную модель, локальное владение станцией и надёжные lifecycle операции.
- **Trend IQVision:** инженерные операции backup/restore, архивы и диагностика должны быть доступны и понятны эксплуатационному персоналу.
- **Siemens Desigo CC:** ориентируемся на распределённую серверную эксплуатацию, интеграции, долговременные данные, аудит и контролируемое восстановление.
- **AVIC:** автономная Edge станция, один writer на агрегат, доказуемая согласованность, восстановление после потери Central/питания и перенос без скрытой потери данных.

## 10. Критерий принятия

ADR принимается после полной inventory таблиц/файловых хранилищ, назначения владельца для каждого агрегата, реализации durable outbox/inbox для критических потоков, consistency manifest, crash-injection tests и restore acceptance на Windows и Linux.
