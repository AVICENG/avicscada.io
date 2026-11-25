# AVIC Station Transfer — DEV111

## Назначение

DEV111 добавляет отдельный сервис `StationTransferManager` для переноса одной инженерной Station между двумя независимыми экземплярами AVIC Core. Это отдельный формат `.avicstation`; он не заменяет универсальный `.avicpkg` DEV110 и не смешивается с полным Backup/Restore.

Реализованный workflow:

1. `export_station(core, station_id, package_path, source_core_version=...)` формирует пакет из Station и данных, явно относящихся к ней.
2. `inspect_package(...)` проверяет формат, состав, корневую Station, размер и SHA-256.
3. `stage_import(...)` помещает проверенные данные в отдельную staging-папку с состоянием `STAGED_NOT_ACTIVATED`.
4. `commit_import(...)` проверяет выбранный целевой Project, коллизии ID и ссылки, затем записывает конфигурацию в целевой Core. Импортированная Station остаётся `NOT_ACTIVATED`.

Пример:

```python
from avic_core.application.container import CoreApplication

with CoreApplication(r"C:\AVIC\source-data") as source:
    package = source.station_transfer.export_station(
        source, "<station-uuid>", r"D:\Transfer\AHU-01.avicstation",
        source_core_version="1.0.0.dev111",
    )

with CoreApplication(r"C:\AVIC\target-data") as target:
    preview = target.station_transfer.inspect_package(
        package, target_core_version="1.0.0.dev111"
    )
    if not preview.compatible:
        raise RuntimeError(preview.warnings)
    stage = target.station_transfer.stage_import(
        package, target.paths.root / "staging",
        expected_package_id=preview.package_id,
        target_core_version="1.0.0.dev111",
    )
    result = target.station_transfer.commit_import(
        target, stage, expected_package_id=preview.package_id,
        target_project_id="<target-project-uuid>",
    )
```

## Состав и сохранение идентификаторов

- В пакет включаются корневая Station и записи репозитория, у которых `station_id` относится к этой Station.
- Дочерние объекты FBD и графики включаются по документным ссылкам: `GraphicElement`, `PointBinding`, `LogicNode`, `LogicLink`, `StrategyPage`, `StrategyConnective`, `LogicGraphicsBinding`.
- Web Pages включаются по `station_id`, включая иерархию страниц и назначения мнемосхем.
- `Point` включается через ссылку `Point.device_id` на устройство этой Station: индекс `station_id` у Point в репозитории отсутствует.
- Сохраняются ID инженерных объектов. При импорте меняется только `Station.project_id`, чтобы привязать Station к выбранному проекту назначения.
- Дополнительные конфигурационные таблицы, включённые явным allow-list: пользовательские SVG; рёбра зависимостей; политика времени и разрешения синхронизации; расписания и их постоянные weekly/special events и point bindings; теги и иерархия точек.
- Временные `schedule_overrides` не переносятся.

## Site binding и fail-safe поведение

Пакет не должен переносить готовую сетевую привязку с исходной площадки:

- у Device очищаются `address` и `native_identity`;
- у PhysicalNetwork очищаются физический интерфейс, IPv4, маска, адрес станции, gateway и DNS; режим адресации возвращается к `auto`;
- ProtocolChannel импортируется выключенным и в режиме `read_only`;
- DriverInstance переводится в `STOPPED`, а чувствительные поля его configuration очищаются;
- из свободного HTML/CSS/JavaScript и других текстовых полей блокируется экспорт при обнаружении типовых credential patterns и частных IPv4-адресов;
- RuntimeInstance переводится в `STOPPED`, generation обнуляется, worker ID очищается;
- Point value и timestamp очищаются, quality устанавливается `UNCERTAIN`;
- Alarm возвращается в `NORMAL`, подтверждение очищается;
- NTP выключается и серверы времени очищаются;
- разрешения синхронизации часов устройств сбрасываются в запрещённые и требуют повторного одобрения на целевой установке.

Секреты, пользователи, роли, лицензии, аудит, оперативные события, история, уведомления/outbox и пользовательские избранные точки не входят в пакет. Перенос прав доступа, секретов и истории должен быть отдельным явно утверждённым процессом.

## Проверки безопасности

- Только два ожидаемых ZIP entries: manifest и payload.
- Проверяются формат/версия, пути, symlink, размер, длина payload и SHA-256.
- Перед commit проверяется hash staging-файла.
- Повторяющиеся ID запрещены; любые ID-коллизии на target блокируют импорт.
- Целевой Project должен существовать и иметь тип Project.
- Проверяются граф ссылок CoreObjectService, FBD/Graphics/Web Pages child references, custom SVG references, сетевые ссылки, Point → Device, schedule bindings, dependencies и device-time permissions.
- Для вспомогательных БД перед изменениями создаются SQLite backup snapshots; при ошибке выполняется компенсационное восстановление и удаление вставленных repository entities. Ошибка компенсации отдельно сообщается.
- Все успешные export/import операции фиксируются в EventService и AuditService.

## Важные ограничения DEV111

1. **Это не полная промышленная Station Copier.** Нет Workbench/UI и удалённого deployment transport.
2. **Нет активации.** Commit создаёт инженерную конфигурацию и оставляет её `NOT_ACTIVATED`. Запуск драйверов, runtime, publish и физическое управление не выполняются.
3. **Нет rollback уже активной Station.** Импорт не перезаписывает существующие ID; при конфликте он блокируется. Отдельный жизненный цикл активной версии ещё предстоит.
4. **Нет цифровой подписи издателя.** SHA-256 обнаруживает повреждение payload, но не подтверждает автора пакета.
5. **Межверсионная миграция не реализована.** При несовпадении Core version импорт блокируется.
6. **Согласованность нескольких SQLite-файлов не является единым crash-atomic snapshot.** Каждый вспомогательный файл читается согласованно в своей SQLite read transaction, но глобального write barrier для всех сервисов Core пока нет. Перед экспортом следует остановить инженерные изменения и не менять конфигурацию Station.
7. **Компенсация импорта не эквивалентна транзакции, устойчивой к аварийному отключению питания в любой инструкции.** Она покрывает обнаруженную ошибку в рамках живого процесса; crash-recovery journal и автоматический startup recovery будут отдельной задачей.
8. **Сопоставление устройств не автоматизировано.** Сетевые поля очищаются; после импорта инженер должен выполнить site binding, проверить BACnet/Modbus адреса и разрешить каналы только после commissioning.
9. **Схема auxiliary allow-list ограничена перечисленными таблицами.** Новые таблицы и типы объектов не переносятся автоматически; перед добавлением необходимо определить их семантику и политику безопасности.
10. Проверка свободного текста ловит типовые шаблоны секретов и частные IPv4, но не является DLP и не может гарантированно распознать произвольный пароль, публичный IP или hostname. Перед передачей пакета нужен просмотр содержимого инженером.
11. История и runtime event data намеренно исключены из Station package; для них требуется отдельная политика Backup/Restore.

## Сравнение с изученными модулями Niagara

Изученные `backup-rt`, `backup-wb`, `platform-rt`, `platform-wb`, `migration-rt` и `migrator-wb` подтверждают разделение резервирования, платформенных операций, миграции и копирования Station. DEV111 использует этот архитектурный принцип. Наличие соответствующих классов Niagara не означает, что AVIC уже имеет эквивалентный полный набор функций.

## DEV112 — надёжная доставка событий и аудита

DEV112 добавляет локальный transactional outbox для результата импорта Station:

- запись операции и её статус PREPARED создаются в той же транзакции objects.sqlite3, что и инженерные сущности;
- после успешной записи всех auxiliary stores операция переводится в JOURNAL_PENDING;
- события и аудит получают стабильные ID, поэтому повторная доставка после частичного сбоя не создаёт дубликаты;
- операция становится COMPLETE только после успешной записи и EventService, и AuditService;
- сбой EventService/AuditService после фиксации инженерных данных больше не превращается в ложное сообщение об откате импорта: commit_import возвращает journal_status=PENDING_RETRY и operation_id;
- при запуске Core автоматически повторяет операции JOURNAL_PENDING;
- операция, оставшаяся в PREPARED после аварийного завершения процесса, переводится в NEEDS_RECONCILIATION. Она не объявляется успешной и не публикует ложное событие импорта, поскольку DEV112 не может доказать, что все отдельные auxiliary SQLite-файлы успели зафиксироваться.

EventService.record(..., event_id=...) и AuditService.append(..., event_id=..., occurred_at=...) поддерживают идемпотентный повтор. Повтор с тем же ID и другим содержимым отклоняется.

### Ограничение и эксплуатационное правило

Outbox устраняет потерю/дублирование журналирования после подтверждённого commit всех хранилищ и позволяет восстановить доставку после перезапуска. Он не превращает несколько отдельных SQLite-файлов в одну физическую атомарную транзакцию. Состояние NEEDS_RECONCILIATION требует проверки сущностей и вспомогательных записей администратором; автоматическая догадка или автоматическое объявление успеха запрещены.