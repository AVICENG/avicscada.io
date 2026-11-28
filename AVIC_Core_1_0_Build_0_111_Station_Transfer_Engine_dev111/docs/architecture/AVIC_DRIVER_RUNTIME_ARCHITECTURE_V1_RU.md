# AVIC Core — архитектура драйверов и коммуникационного Runtime v1

Статус: зафиксированное архитектурное решение  
Дата: 28.11.2026  
Область: AVIC Core 1.0, Drivers, Communication Engine, Point Runtime

## 1. Выбранная архитектура

AVIC использует смешанную архитектуру C + Python + Rust. Язык выбирается по зрелости конкретного протокольного стека, межплатформенной поддержке и стоимости надёжной эксплуатации, а не ради унификации.

- C — изолированные протокольные Workers для зрелых нативных библиотек и предсказуемого доступа к serial/network API. Приоритет: BACnet/IP на Steve Karg BACnet Stack, Modbus RTU/TCP на libmodbus/текущем C Worker, MQTT на Eclipse Paho C.
- Python — специализированные интеграции, где зрелая библиотека даёт существенное преимущество. KNX — отдельный процесс на xknx; тяжёлые и блокирующие операции не выполняются в его event loop.
- Rust — инфраструктура: управление жизненным циклом Worker, IPC, контроль поколений/последовательностей, bounded queues, отказоустойчивое завершение процессов, сетевые сервисы и inter-station communication.
- AVIC Core Point Runtime — единственный авторитетный владелец текущих значений, качества и времени точек. Ни один Worker и Rust transport cache не создают независимую CVT.

## 2. Границы ответственности

| Уровень | Ответственность | Запрещено |
|---|---|---|
| C/Python Worker | Протокольный обмен, преобразование native payload в IPC, транспортная диагностика | Самостоятельно менять авторитетное состояние Point Runtime |
| Rust Communication Engine | Supervisor, IPC, очереди, generation/sequence fencing, сетевые сервисы | Хранить расходящуюся копию текущих значений точек |
| AVIC Core | Driver Manager, RBAC, лицензия, команды, качество, время, аудит, Point Runtime | Принимать данные без проверки scope/binding/generation |
| Historian/Alarm/Logic | Потребители опубликованных данных Core | Читать внутренние кэши Worker как источник истины |

Транспортный кэш допустим только как ограниченный буфер доставки с владельцем, лимитом, политикой переполнения и метриками.

## 3. IPC Contract v1

Фактическая реализация в avic_core/drivers/ipc.py задаёт контракт avic.driver.ipc версии 1:
- 4-byte unsigned big-endian length prefix;
- UTF-8 JSON envelope;
- максимальный кадр 1 MiB;
- строгая проверка схемы, UUID, UTC timestamp, generation, sequence и object payload.

Это каноническое кадрирование IPC v1. Оно устойчиво к переводам строк внутри JSON-строк и однозначно выявляет неполные кадры. Существующие C Workers с NDJSON временно работают через совместимый адаптер/транспортный профиль; NDJSON и length-prefixed framing нельзя смешивать в одном потоке и нельзя объявлять взаимозаменяемыми. Миграция C Workers выполняется поэтапно с тестами обеих сторон.

Обязательные поля envelope v1: contract, version, message_id, kind, installation_id, project_id, station_id, driver_instance_id, worker_id, generation, sequence, sent_at, correlation_id, payload. Новые обязательные поля не добавляются в v1 без отдельного согласованного расширения; несовместимые изменения требуют версии v2.

Правила:
- UUID для message/worker/correlation; correlation_id=null для unsolicited events.
- generation — положительный номер запуска; старые поколения отбрасываются.
- sequence — монотонный поток; duplicate/regression — protocol fault, gap — диагностируемое событие.
- sent_at — RFC3339 UTC с Z. Monotonic clock применяется для timeout, deadline, duration и backoff.
- Полный scope установки/проекта/станции/драйвера/Worker сверяется Core с конфигурацией.

## 4. Значения и качество точек

Point event payload несёт point/external id, типизированное значение, quality, quality reason и временные сведения источника/приёма.

Семантика:
- GOOD — значение валидно и свежее;
- UNCERTAIN — значение доступно, но достоверность ограничена;
- BAD — значение непригодно для использования/управления.

Причины стандартизируются: INIT, UNKNOWN, COMM_LOST, STALE, CONFIG_ERROR, BAD_DATA, DEVICE_FAULT, ACCESS_DENIED, TIMEOUT, PROTOCOL_ERROR. Последнее известное значение может сохраняться, но при потере связи quality меняется на BAD/COMM_LOST или UNCERTAIN/STALE по политике точки. Нельзя выдавать сохранённое значение за свежее. Timestamp устройства, время получения Worker и время публикации Core хранятся раздельно; отсутствующее время источника не выдумывается.

## 5. Команды и безопасность

Жизненный цикл команды:
1. ACCEPTED — Core проверил права, scope, лицензию, конфигурацию и принял команду.
2. SENT — Worker подтвердил отправку в протокол.
3. CONFIRMED — получено подтверждение протокола или независимая обратная связь по политике устройства.

SENT не доказывает физическое исполнение. Для критичных команд нужны durable journal/outbox, deadline, correlation/idempotency key и политика восстановления. Нельзя безусловно повторять toggle/reset/start/stop после неопределённого результата. Exactly-once исполнение физическим устройством не обещается; используются дедупликация, безопасные повторяемые операции и сверка состояния.

Любая команда проходит RBAC, ownership/lease, interlock и безопасную политику драйвера. Discovery и чтение по умолчанию безопасны; запись — отдельная разрешённая операция.

## 6. Отказоустойчивость

- Все очереди ограничены и имеют метрики depth/overflow/drop/reject.
- Потеря IPC, malformed frame, sequence regression, identity mismatch и критическое переполнение немедленно fenced.
- Worker завершается по bounded escalation: terminate → wait → kill → wait.
- Перезапуск создаёт новое generation; старые события не перезаписывают новые данные.
- Coalescing/drop разрешён только явно заменяемой телеметрии. Команды, аварии, discovery и lifecycle events нельзя молча терять.
- Retry/backoff зависит от протокола; агрессивный общий retry-loop запрещён.

## 7. Время

UTC wall-clock timestamp используется для обмена и аудита; monotonic clock — для таймаутов и длительностей. Время устройства хранится отдельно от локального времени приёма. BACnet clock synchronization — явная функция Core Time Manager и отдельное разрешение на каждом устройстве; драйвер не синхронизирует часы скрытно.

## 8. Протокольная стратегия

### BACnet/IP — C Worker
Steve Karg BACnet Stack — базовая C-библиотека. Этапы: Who-Is/I-Am, ReadProperty, затем ReadPropertyMultiple, типы/единицы/статусы, error/quality mapping, rate limits и simulator. RPM применяется только если устройство поддерживает сервис и корректно отвечает; fallback на RP ограничен и диагностируем. MS/TP — отдельный этап после устойчивого BACnet/IP.

### Modbus RTU/TCP — C Worker
C/libmodbus — основной протокольный путь. RTU требует эксклюзивного serial ownership, явной настройки baud/parity/data/stop bits, тестов CRC/short frame/timeout/wrong slave, безопасного reconnect и Windows COM namespace. PTY/virtual COM — программная приёмка, не hardware acceptance.

### MQTT — C Worker
Eclipse Paho C. Сначала MQTT 3.1.1 TCP, затем TLS и SecretStore credentials, ACL/QoS/reconnect/retained/LWT policy и soak. Payload становится точкой только после mapping и проверки качества в Core.

### KNX — Python xknx Worker
Изолированный процесс/event loop с явной привязкой к local IP/interface. Routing и Tunneling — разные режимы; route_back не считается универсальной настройкой Routing. IP forwarding/bridge между сетевыми зонами автоматически не включается. GroupValueRead учитывает read flags устройств, приоритеты и rate limits; отсутствие ответа означает unknown/stale, не ноль.

OPC UA, S7 и будущие драйверы используют ту же модель владения и проходят те же gates. Язык выбирается по зрелой библиотеке и доказанным требованиям, а не по общему лозунгу C-only.

## 9. Сборка и выпуск

Релиз содержит manifest совместимости Core ↔ IPC contract ↔ Worker ↔ native library. Несовместимый Worker не запускается. Обновление атомарное, с health check, rollback и контролируемой миграцией конфигурации. Windows x64, Linux x86_64 и ARM64 тестируются отдельными матрицами; успех одной платформы не доказывает успех другой.

## 10. Условия готовности драйвера

Компиляция и loopback не означают готовность. Обязательные gates: unit/codec; positive и negative round-trip; timeout/late reply/malformed/short frame/disconnect/reconnect; generation/sequence/identity fencing; bounded queues/backpressure; Windows/Linux/ARM64 CI; Driver Manager + Point Runtime; RBAC/audit/quality; soak; физическое оборудование и документированная приёмка. Симулятор не заменяет hardware acceptance.

## 11. Порядок внедрения

1. Укрепить Rust Worker Supervisor и Modbus TCP fault recovery.
2. Закрыть Modbus RTU Windows COM и serial ownership.
3. Довести BACnet C Worker: discovery, RP/RPM, datatype/unit mapping, quality/error mapping, simulator, Driver Manager → Point Runtime.
4. Довести MQTT C Worker: state synchronization, TLS/credentials, QoS/ACL и soak.
5. Создать KNX xknx Worker по контракту v1.
6. Унифицировать запуск, health, diagnostics, package manifest и управление C/Python/Rust Workers.
7. Удалять прежние реализации только после acceptance нового пути.

## Источники и ориентиры

- Steve Karg BACnet Stack: https://github.com/bacnet-stack/bacnet-stack
- BACnet Stack FAQ: https://github.com/bacnet-stack/bacnet-stack/blob/master/doc/README.faq
- BACnet services overview: https://bacnet.org/wp-content/uploads/sites/4/2022/06/The-Language-of-BACnet.pdf
- XKNX: https://github.com/XKNX/xknx
- Eclipse Paho MQTT C: https://github.com/eclipse-paho/paho.mqtt.c
- libmodbus: https://github.com/stephane/libmodbus
