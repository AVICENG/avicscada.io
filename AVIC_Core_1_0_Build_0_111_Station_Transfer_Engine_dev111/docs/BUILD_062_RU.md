# AVIC Core 1.0 — DEV62 Integrated Engineering Workflows

## Назначение

DEV62 объединяет существующие инженерные сервисы DEV57 и предыдущих сборок в одну версию и добавляет недостающие сквозные элементы для Discovery, импорта, FBD и Platform diagnostics. Это интеграционная сборка, а не заявление о полной промышленной готовности всех разделов IQVISION.

## Новое в DEV62

1. **Журнал Discovery** (`DiscoveryHistory`): отдельная SQLite-база, сохранение завершённых read-only BACnet/IP-сеансов, найденных устройств и ограниченного набора диагностических данных. История переживает перезапуск. Секреты из device payload не сохраняются.
2. **Предпросмотр импорта** (`DeviceImportService.preview_bacnet`): показывает уже существующее устройство, новые точки, дубликаты и неизвестные выбранные native ID. Предпросмотр не изменяет БД и не связывается с полевым оборудованием.
3. **Расширение FBD**: блоки `LIMIT`, `SCALE`, `COMPARE_LT`; типизированные порты, проверка некорректного диапазона и офлайн-симуляция.
4. **Platform Status API** (`GET /api/platform/status`): версия, количества сохранённых объектов, состояние зарегистрированных Runtime-станций, перечень локальных backup-архивов и явные safety flags.
5. Версия API и пакета обновлена до `1.0.0.dev62`; статус FBD в каталоге модулей изменён с interface на partial.

## Использование новых API

- `GET /api/network/discovery-sessions?limit=100` — последние завершённые сеансы.
- `GET /api/network/discovery-sessions/{session_id}` — состав и диагностика сеанса.
- `POST /api/stations/{station_id}/devices/import-preview` — тело `{ "inspection": {...}, "selected_native_ids": [...], "import_all": false }`.
- `GET /api/platform/status` — текущее состояние платформы и безопасные режимы.
- `GET /api/fbd/library` — библиотека блоков, включая LIMIT/SCALE/COMPARE_LT.

`/api/network/bacnet/discover` остаётся явным действием инженера. Discovery не запускается при старте приложения. Импорт точек сохраняет качество `UNCERTAIN` до подтверждённого чтения. FBD исполняется только в симуляторе.

## Что включено из предыдущих сборок

- Workbench, проекты/станции, инженерное дерево, физические сети и каналы.
- BACnet/IP Discovery/inspect/import и Modbus TCP read-only foundations.
- Driver Manager: каталог и остановленные экземпляры драйверов.
- Graphics Workbench: документы, символы HVAC, привязки к точкам и FBD.
- FBD/Wiresheet: постоянные документы, типизированные блоки/связи, защита от циклов, симуляция.
- Scheduler: недельные события, специальные даты, копирование дней, вычисление, привязки и overrides.
- Alarm Service: жизненный цикл, подтверждения, заметки и журнал переходов.
- History/Event/Audit, Backup archive/preview/restore primitives, security/authentication primitives.

## Матрица готовности

| Область | Статус DEV62 | Что ещё не закрыто |
|---|---|---|
| Discovery / Point Import | Частично реализовано | Нет общего multi-protocol discovery job manager; Modbus inventory import и массовое сопоставление требуют завершения |
| Driver Manager | Частично реализовано | Нет внешней установки/подписи пакетов, SDK, reconnect, polling/subscriptions и производственного lifecycle |
| Graphics / PX | Частично реализовано | Нет полного набора PX-виджетов, custom SVG palette manager, всех динамических анимаций, runtime dashboards и операторских команд |
| FBD / Wiresheet | Частично реализовано | Есть редактор/валидация/симуляция; нет циклического production runtime, online watch, scheduler execution, publish/rollback и полевых выходов |
| Scheduler | Частично реализовано | Есть API/сервис расписаний; нет завершённого визуального календарного редактора и принятого runtime исполнения |
| Alarm / History | Частично реализовано | Сервисы и API существуют; полная операторская консоль, routing/escalation delivery и графики требуют завершения |
| Security | Частично реализовано | Есть auth/RBAC/MFA primitives; они не интегрированы как обязательная серверная защита каждого Workbench API |
| Backup / Restore | Частично реализовано | Есть архив/проверка/restore primitives; нет принятого полного DR-процесса и UI восстановления станции |
| Platform Manager | Частично реализовано | Нет полноценного Windows service/installer, upgrade/uninstall/rollback и полного service manager |
| TONN / AVIC Linux Controller Agent | Запланировано | Протокол/агент, provisioning, update, secure channel и field runtime не реализованы |
| Trend IQ3 | Необязательная интеграция | Не является условием готовности AVIC; миграция Trend Site не входит в приоритет этой сборки |

## Безопасность

- Автозапуск драйверов выключен.
- Полевые записи выключены.
- Discovery выполняется только по явному запросу и в read-only режиме.
- FBD simulation offline-only.
- Неизвестные производители/модели не угадываются; источник и уверенность идентификации остаются отдельными полями.

## Ограничения приёмки

DEV62 не прошла Windows acceptance на пользовательском ПК, браузерную интерактивную приёмку, проверку на реальных BACnet/Modbus устройствах, TONN hardware acceptance или промышленную эксплуатационную приёмку. Полный единый `pytest -q` не завершён в лимите времени. Подтверждены отдельные регрессионные группы и целевые сценарии; детали приведены в `BUILD_TEST_LOG_DEV62_RU.md`.
