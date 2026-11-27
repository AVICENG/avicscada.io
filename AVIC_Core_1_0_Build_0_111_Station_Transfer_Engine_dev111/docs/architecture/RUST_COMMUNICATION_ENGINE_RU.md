# AVIC Rust Communication Engine — архитектура и пилот Modbus TCP

Дата: 27.11.2026  
Статус: DEV208 — первый Rust pilot, требуется полный CI и аппаратные испытания.

## 1. Разделение ответственности

- **AVIC Core (Python)** остаётся владельцем инженерной модели, Station/Device/Point, RBAC, лицензирования, Audit, конфигурации, Point Runtime, Historian, FBD и UI/API.
- **Rust Communication Engine** — отдельный процесс для сетевого I/O и протокольного разбора. Он не получает доступ к SQLite, лицензиям, SecretStore или внутренним объектам Core.
- Обмен между Core и движком выполняется через JSON Lines по stdin/stdout. Один запрос — одна строка JSON, один ответ — одна строка JSON с обязательным request_id.
- Стандартный stderr движка не смешивается с IPC stdout. Core запускает бинарный файл без shell и контролирует процесс.
- При тайм-ауте/аварии IPC процесс завершается и ошибка передаётся Driver Manager. Автоматического скрытого перехода на Python нет: резервный backend выбирается явно в конфигурации драйвера.

## 2. DEV208 — Modbus TCP pilot

Добавлен crate `rust/communication-engine` и executable `avic-communication-engine`.

Поддержанный IPC контракт:
- `health` — версия/идентификатор движка и список возможностей;
- `modbus_read` — Modbus TCP FC 1, 2, 3, 4;
- `shutdown` — контролируемое завершение процесса.

Транспортный контракт:
- literal IP address; TCP connect/read/write timeout 100–10 000 ms;
- проверка MBAP transaction ID, protocol ID, length и unit ID;
- проверка функции, byte count и длины payload;
- обработка Modbus exception response;
- чтение coils/discrete inputs и holding/input registers;
- никаких FC 5/6/15/16/22/23 и иных write/control запросов;
- Python Modbus adapter по-прежнему отвечает за типизацию регистров, scale/offset, station-owned DriverInstance и публикацию в Point Runtime.

## 3. Включение

Сначала соберите бинарный файл в каталоге `rust/communication-engine`:

```powershell
cargo test
cargo build --release
```

Windows executable:
`target\release\avic-communication-engine.exe`

Linux executable:
`target/release/avic-communication-engine`

В конфигурации DriverInstance Modbus TCP:
- `engine_backend = "rust"`
- `engine_binary = абсолютный путь к собранному executable`

Для контрольного Python backend:
- `engine_backend = "python"` или поле можно не указывать.

Не заданный/нерабочий Rust executable приводит к явной ошибке старта. Python fallback автоматически не включается, чтобы ошибка Rust-движка не маскировалась.

## 4. Безопасность

- Пилот строго READ-ONLY. В Rust engine реализованы только функции чтения Modbus 1–4.
- Движок не может напрямую публиковать значения в Core: он возвращает сырые регистры/биты; Python adapter декодирует и выполняет проверку владельца точки перед записью в Point Runtime.
- Не передаются пароли и секреты. Host/port/unit/address/count являются параметрами запроса.
- Процесс изолирован от Core-хранилища и не получает привилегий на управление оборудованием.
- Существующий Python backend остаётся доступен как явный резервный режим.

## 5. Проверки и границы готовности

CI включает Rust tests/build на Ubuntu и Windows. Python full matrix продолжает тестировать Core и адаптеры.

Пока не подтверждены:
- полное сравнение производительности Python/Rust на одинаковых 1k/10k точках;
- длительный soak test, reconnect storm, packet loss, malformed peer и process crash recovery на реальной сети;
- аппаратная проверка с Trend Modbus TCP контроллером;
- BACnet/IP Rust engine. BACnet остаётся Python READ-ONLY до отдельного пилота и parity tests.

Нельзя считать Rust Modbus production-ready только по факту компиляции или unit tests. Нужны Linux/Windows CI, functional parity, load/fault tests и реальный контроллер.
