# ADR-004 — Command Contract, arbitration и единственная граница полевой записи

Статус: **PROPOSED — физические записи остаются отключёнными**  
Дата: 27.11.2026  
Область: операторские команды, расписания, FBD, remote supervisor, драйверы, Edge и контроллеры.

## 1. Цель и правило безопасности

Любая команда, меняющая физическое состояние оборудования, проходит один Command Gateway. Ни UI, ни FBD, ни Scheduler, ни API, ни AI не вызывают write-функцию драйвера напрямую.

AVIC не заменяет независимые safety interlocks/защитные функции PLC. AVIC оценивает разрешение на команду и отправляет её только в пределах подтверждённых возможностей устройства и политики проекта.

До принятия ADR и завершения acceptance tests текущий режим остаётся SIMULATION_ONLY; реальная запись запрещена.

## 2. Источники intent

Единый Command Gateway принимает intent от:
- оператора Workbench/HMI;
- локального расписания;
- FBD/автоматизации;
- remote supervisor/Central;
- сервисного workflow;
- AI Engineering Assistant — только как предложение, требующее подтверждения человеком.

Intent не является разрешением на запись. Наличие точки OUTPUT, активной Access Lease или роли Engineer по отдельности недостаточно.

## 3. Канонический Command Contract

| Поле | Назначение |
|---|---|
| `command_id` | UUID, создаётся один раз и не меняется при retry |
| `idempotency_key` | Защита от повторного исполнения |
| `target_point_id` / `target_device_id` | Явная цель |
| `station_id` | Область исполнения |
| `requested_value` | Типизированное желаемое значение |
| `intent_source` | OPERATOR / SCHEDULE / FBD / SUPERVISOR / SERVICE |
| `principal` | Authenticated user/service identity; actor_id из payload не доверяется |
| `reason` | Причина и/или change reference |
| `priority` | Source-defined priority из утверждённой политики |
| `created_at`, `expires_at` | Срок действия и защита от старых команд |
| `runtime_epoch` | Fencing token текущего владельца Station Runtime |
| `definition_revision` | Версия Point Definition |
| `lease_id` | Временное право на Control, если применимо |
| `correlation_id` | Сквозная диагностика |
| `interlock_evidence` | Проверенные условия и их sample/event references |
| `policy_revision` | Версия правил, по которым команда разрешена |

## 4. Этапы обработки

1. **Receive** — принять intent, проверить схему и idempotency key.
2. **Authenticate** — получить Principal или service identity из доверенного контекста.
3. **Authorize** — проверить permission, installation/project/station scope, license capability и режим Monitoring/Engineering/Control.
4. **Lease** — проверить временный Access Lease и его владельца/срок действия для операторского Control.
5. **Resolve** — проверить Point Definition, station/device/driver ownership, направление, тип и write capability.
6. **Freshness** — проверить актуальность Point State и Quality; UNCERTAIN/BAD/STALE/COMM_LOST не разрешают автоматическое действие.
7. **Interlocks** — проверить обязательные разрешающие условия, их качество, freshness и область станции.
8. **Arbitrate** — определить конфликт с уже активной командой и конкурирующими источниками.
9. **Dispatch** — передать команду единственному protocol executor с timeout и idempotency context.
10. **Protocol ACK** — сохранить подтверждение транспорта/протокола, не считать его подтверждением физического результата.
11. **Observed feedback** — отдельно дождаться фактического состояния от входной точки/обратной связи.
12. **Complete/Fail** — зафиксировать финальное состояние, причины отказа, before/after и audit trail.

Каждый этап имеет явный статус и timeout. Сбой/timeout не маскируется как успешное исполнение.

## 5. Arbitration policy

Приоритеты не кодируются случайным порядком прихода. Для каждого класса оборудования задаётся policy:
- local hardwired safety/interlock — вне AVIC command arbitration и имеет безусловное преимущество;
- локальная аварийная остановка — отдельная разрешённая команда/состояние согласно проектной политике;
- ручная команда оператора;
- расписание;
- FBD/automatic strategy;
- remote supervisor;
- сервисный workflow.

Это исходный список источников, а не окончательный универсальный рейтинг. Для конкретного оборудования политика определяет:
- допустимые источники;
- приоритет и preemption;
- разрешение/запрет параллельных команд;
- debounce/minimum run/stop time;
- rate limit и cooldown;
- ручной override и его TTL;
- поведение при потере связи;
- восстановление после restart.

Нельзя автоматически перезаписывать ручной режим следующей командой расписания или FBD. Override должен иметь видимый источник, автора, причину и срок окончания.

## 6. Access Lease и режимы доступа

- Monitoring — чтение, без управления.
- Engineering — изменение конфигурации и подготовка staged publish; не означает Control.
- Control — временное право на управление в конкретной станции.
- Lease ограничен сроком, scope, Principal, reason и может быть отозван.
- Наличие Lease не обходит RBAC, interlocks, quality, policy или лицензирование.
- Lease нельзя получить только передачей actor_id из HTTP body.
- Потеря соединения/сессии, logout, revocation или истечение срока блокируют новые команды.
- Уже отправленная команда имеет отдельный lifecycle; её нельзя считать отменённой только из-за истечения Lease.

## 7. Retry, timeout и неизвестный результат

- Один command_id сохраняется при повторной доставке.
- Повторная команда с тем же idempotency key не создаёт второе физическое действие.
- Если transport timeout произошёл после отправки, результат считается UNKNOWN/UNCONFIRMED до reconciliation/readback; автоматический retry опасной команды запрещён, пока протокол не докажет безопасную идемпотентность.
- Команда с истёкшим TTL, старым runtime_epoch или definition_revision отклоняется.
- Protocol ACK не равен equipment feedback.
- При потере связи состояние команды становится UNKNOWN/COMMUNICATION_LOST, а не SUCCESS.
- Все решения арбитража и причины отказа журналируются.

## 8. Драйверный контракт

Write-capable driver реализует capability interface, но не предоставляет UI/SDK прямой метод обхода Command Gateway. Контракт включает:
- device identity и supported write types/ranges;
- encode/dispatch с command_id/idempotency;
- protocol acknowledgement;
- cancellation semantics (если протокол поддерживает);
- readback/feedback mapping;
- timeout/retry semantics;
- diagnostics и безопасное поведение при disconnect.

Read-only driver не получает write capability. Обнаружение writable object в BACnet/Modbus не означает, что AVIC автоматически разрешает его запись.

## 9. AI и автоматизация

- AI может анализировать alarms/trends/documents и предлагать change set или команду.
- AI не получает Principal оператора, Control Lease или прямой driver capability.
- AI-generated logic/configuration проходит validation, simulation, approval и staged publish.
- AI не может обходить interlocks, изменять safety policy или автоматически выдавать себе Control.
- FBD и Scheduler создают intent, а не исполняют физическую запись самостоятельно.

## 10. Acceptance tests

- нет прямых protocol write вызовов вне Command Gateway/executor (architecture test);
- actor_id из payload не может подменить Principal;
- RBAC/scope/license/lease независимо проверяются;
- команды из другой станции и другой definition revision отклоняются;
- UNCERTAIN/BAD/STALE/COMM_LOST interlock блокирует действие;
- неактуальный interlock sample блокирует действие;
- expiry/runtime_epoch fencing отклоняет replay;
- повторный idempotency key не выполняет второй write;
- transport ACK без feedback не становится SUCCESS;
- timeout после отправки приводит к UNKNOWN и reconciliation;
- конфликт Operator vs Schedule vs FBD обрабатывается по явной policy;
- manual override имеет TTL и не сбрасывается скрыто;
- stop/start rate limits и minimum run/stop timers проверяются;
- driver capability и object write support подтверждены протокольными тестами;
- отказ/потеря связи/рестарт не создают автоматический повтор команды;
- все разрешения, отказы, ACK, feedback и override записаны в audit;
- физические записи по умолчанию выключены в тестовых и коммерческих профилях до отдельной acceptance sign-off.

## 11. Проверка по трём системам

- **Niagara:** сохраняем контролируемые action/command semantics и инженерные права на уровне станции/объектов.
- **Trend IQVision:** проверяем понятную инженеру ручную команду, override, feedback и диагностику в графике/точке.
- **Siemens Desigo CC:** учитываем advanced event management, reaction logic, distributed operations и дисциплину системной интеграции.
- **AVIC:** единый арбитраж для всех источников, строгая изоляция станции, доказуемая авторизация, idempotency и отсутствие скрытого обхода безопасности.

## 12. Критерий принятия

ADR принимается после единого Command Contract, работающего policy/arbitration engine, authenticated Principal integration, Access Lease enforcement, idempotent executor interface, readback semantics и полной fault-injection test suite. Физическая запись включается отдельно для конкретного протокола/устройства после acceptance; не глобальным переключателем «разрешить всё».
