# DEV113 — аудит сетевых драйверов Trend / BACnet / Modbus

Дата: 2026-11-25  
Основа: DEV112, ветка `dev113-network-drivers`  
Статус: аудит исходников и доступной документации; полевые испытания не проводились.

## 1. Целевая архитектура AVIC

В AVIC остаются три самостоятельных протокольных драйвера:

1. **Trend IP / IQ Network** — собственный драйвер Trend через TCP vCNC. Это не BACnet-обёртка.
2. **BACnet/IP** — универсальный BACnet-драйвер для Trend и оборудования других производителей, если устройство поддерживает BACnet.
3. **Modbus TCP** — универсальный Modbus TCP-драйвер с инженерной картой регистров.

Trend IQ3 BACnet не должен отображаться как четвёртый/отдельный драйвер. Trend-специфические BACnet профили могут оставаться вспомогательными профилями/правилами классификации внутри общего BACnet-драйвера.

Все драйверы публикуют значения в общий `PointRuntimeService`. Протокольные адреса и свойства остаются в адаптерах; FBD, мнемосхемы, тревоги и архивы используют единый внутренний UID точки.

## 2. Что подтверждено документацией

### 2.1 Trend IP / vCNC

Из IQVISION Configuration Manual TE201382 и курса IQVISION Module 3 (Manual Discovery):

- соединение с Trend Site выполняется через Ethernet-enabled устройство с включённым vCNC;
- конфигурация начального подключения содержит IP/hostname и TCP port vCNC;
- в руководстве IQVISION приведён пример порта 10024; фактический порт задаётся в контроллере и не должен быть жёстко зашит в AVIC;
- IQVISION задаёт timeout, reconnect delay, retry count и permanent/temporary connection;
- discovery сначала показывает найденные устройства, затем инженер выбирает, какие добавить в базу;
- при импорте устройства автоматически распределяются по LAN;
- point folders создаются автоматически; точки можно добавлять выборочно или группами;
- отдельно обнаруживаются расписания и plots/histories;
- курс описывает импортированные Trend schedules как read-only; доступность записи/корректировки должна определяться поколением устройства, типом модуля и подтверждёнными возможностями, а не предполагаться для всех контроллеров;
- User Defined Points требуют Trend parameter code;
- предусмотрена отдельная проверка количества используемых точек.

IQVISION Configuration Manual v2.60 и более поздняя документация Trend N4 описывают несколько vCNC соединений на Site, включая primary/secondary для отказоустойчивости и распределения нагрузки. Это следует заложить в модель соединений AVIC, но включать параллельные каналы только после проверки ограничений конкретной сети/поколения контроллеров.

Современные IQ4/IQ5 могут иметь Secure vCNC. Наличие TCP порта само по себе не означает поддержку secure handshake. Без опубликованной спецификации secure-протокола нельзя заявлять совместимость или пытаться обойти аутентификацию.

### 2.2 SET / Migration

Курс IQVISION Module 4 подтверждает следующий workflow:

- SET экспортирует Site в XML;
- XML помещается в файловую область станции;
- Trend Migration Service читает XML;
- импорт устройств выполняется отдельными этапами с проверкой количества и итоговым отчётом;
- перенос схем можно выполнять отдельно от переноса устройств;
- курс указывает перенос точек, расписаний и историй.

Существующий `avic_core/trend_tsite.py` — только безопасный read-only parser TSOM XML и preview инвентаря. Он не создаёт устройства/точки, не переносит расписания и истории и не является SET Migration.

В AVIC нужен отдельный импортный pipeline: upload → format/version detection → parse → preview → mapping → validation → duplicate/conflict report → explicit commit → audit → rollback/reconciliation. Импорт не должен подключаться к контроллерам или выполнять команды.

### 2.3 BACnet/IP

Курс IQVISION Module 5 (BACnet Driver) подтверждает:

- настройку BACnet communication до discovery;
- Device Instance и диапазоны discovery;
- отдельные Point / Alarm / Schedule / History области;
- распознавание Numeric, Boolean, Enumerated и String;
- Tuning Policy влияет на автоматические записи при Start / Up / Enabled.

В AVIC безопасный default — read-only. Автоматические Write-on-Start/Up/Enabled запрещены. Команда в контроллер должна проходить через отдельный Command Manager с RBAC, разрешением на точку/устройство, пределами значения, interlock/quality check, подтверждением по политике, read-back и audit.

BACnet discovery по локальному broadcast не равно межсетевому discovery. Для удалённых сегментов требуется явная маршрутизация/BBMD/Foreign Device Registration, если это поддерживает целевая сеть.

### 2.4 Modbus TCP

В доступном курсе IQVISION отдельного руководства по Modbus-драйверу не найдено. В материалах 963 есть Modbus LAN/device обозначения, но это не спецификация Modbus TCP. Для реализации используем официальные Modbus Organization Application Protocol V1.1b3 и Modbus Messaging on TCP/IP Implementation Guide V1.0b.

Для Modbus TCP не следует обещать универсальное автоматическое обнаружение точек: обычно нужна инженерная карта регистров (CSV/JSON/профиль производителя). MEI 0x2B/0x0E Device Identification — опциональная идентификация устройства, а не полный каталог измерений.

## 3. Фактическое состояние исходников DEV112

| Область | Реально найдено | Вывод |
|---|---|---|
| Driver Catalog | BACnet/IP, Trend IQ3 BACnet profile, Modbus TCP | Каталог неверно представляет Trend IQ3 BACnet как отдельный драйвер; нужен Trend IP entry |
| Driver Manager | Создание и хранение остановленного DriverInstance | Это inventory/lifecycle foundation; реального start/stop адаптеров пока нет |
| BACnet/IP transport | Who-Is/I-Am, ReadProperty, Object_List, базовый decode, device identity | Рабочая read-only основа; не полный production driver |
| BACnet object reader | Чтение части свойств и point-like объектов / schedules | Нет полноценного polling/COV, RPM/segmentation и полного декодирования сложных расписаний |
| Modbus TCP | FC01/02/03/04 reads, MBAP validation, MEI 0x0E, базовые типы регистров | Read-only transport; нет polling, register map import и публикации в Point Runtime |
| Trend IQ3 | BACnet read-only profile | Не является Trend IP / IQ Network |
| Trend TSITE | Read-only XML inventory parser | Не является миграцией SET |
| Point Runtime | Единый UID, value/type/quality/timestamp, subscriptions | Контракт готов к адаптерам, но транспортные клиенты не подключены к publish |
| FBD | Исполняемый runtime и виртуальные точки существуют | Полевые точки драйверов ещё не подаются в runtime сквозным путём |

## 4. Исправить в BACnet/IP

1. Разделить transport, session/request correlation, device discovery, object catalog, point adapter и lifecycle.
2. Проверять адрес/порт источника, invoke ID, service choice и корректность ACK; обрабатывать Error/Reject/Abort, timeout и retry без принятия чужих/устаревших ответов.
3. Реализовать корректное декодирование application/context tags и constructed values, включая расписания, даты/время, priority arrays, status flags, reliability, units и enumerations.
4. Добавить ReadPropertyMultiple, где устройство поддерживает; fallback на ReadProperty с лимитами.
5. Добавить BACnet segmentation/APDU negotiation и корректные пределы размера; не считать наличие max_apdu поддержкой всех сегментаций.
6. Реализовать явную модель BBMD/Foreign Device Registration и routed discovery; не выполнять регистрацию автоматически без подтверждения инженера.
7. Добавить polling scheduler, jitter, per-device concurrency limits, backoff, stale/COMM_LOST quality и reconnect.
8. Добавить COV subscriptions как оптимизацию с lease/renewal/fallback polling, не полагаться на COV как единственный источник.
9. Добавить read-only импорт точек с типом, facets, units, object identity, source/confidence и duplicate checks.
10. Ввести отдельный Command Manager; до его готовности все записи остаются недоступны.
11. Проверить generic vendor/model resolution: Vendor ID подтверждает производителя, но не всегда модель; неизвестную модель не угадывать.
12. Добавить реальные BACnet/IP simulator tests и hardware acceptance, включая медленные устройства и маршрутизируемые сети.

## 5. Исправить в Modbus TCP

1. Оставить явную карту точек: Unit ID, register/coil area, zero-based address, function code, count, data type, byte order, word order, scale, offset, units, read interval, writable flag.
2. Ввести безопасный CSV/JSON import с preview, validation, duplicate detection и тестом адресного смещения 0/1.
3. Расширить типы: bool/bit, int16/uint16, int32/uint32, float32, int64/uint64, float64; варианты byte/word order; scale/offset и качество decode.
4. Обрабатывать exception codes отдельно от сетевых ошибок; проверять transaction ID, protocol ID, length, Unit ID, function и byte count.
5. Исправить конкурентность transaction ID и определить безопасную модель одного соединения: сериализованный request/response либо пул с независимыми сокетами.
6. Добавить persistent connection/controlled reconnect или измеренно обоснованный короткоживущий режим; не открывать новый TCP socket для каждого point при массовом polling.
7. Добавить scheduler с объединением соседних регистров в допустимые блоки, соблюдением лимитов функций, rate limits и fairness между Unit ID.
8. Добавить Device Identification как опциональную capability; отсутствие MEI не должно означать неисправность устройства.
9. Подключить samples к PointRuntime с качеством GOOD/UNCERTAIN/BAD/STALE/COMM_LOST, timestamp и provenance.
10. Запись FC05/06/15/16/22/23 не включать до появления общего Command Manager и явного разрешения на конкретные точки.

## 6. Реализация Trend IP Driver — обязательные подсистемы

1. Site/vCNC endpoint model: hostname/IP, port, vCNC outstation, device type, LAN, label, security mode reference, primary/secondary role.
2. TCP connection manager: connect timeout, response timeout, retry/backoff, heartbeat/health, reconnect, graceful close, connection ownership and diagnostics.
3. Trend frame codec — только по разрешённой протокольной спецификации и проверенным тестовым векторам. Не выдумывать формат по имени DLL/JAR и не использовать декомпиляцию закрытых драйверов.
4. Session/request scheduler: correlation, serialization/concurrency constraints, response matching, timeout/cancel, bounded queues.
5. Site/LAN/device discovery; device identity сохраняет Trend LAN/outstation/type/firmware и evidence.
6. Point discovery/import: Sensor, Knob, Switch, Digital Input, Driver, user-defined parameter codes; mapping к AVIC point type/direction/facets.
7. Trend alarms: отдельный ingress и parser, source identity, alarm class, state transitions, ack policy, dedupe and audit. Listener/port настраивается явно.
8. Trend schedules: read-only baseline; write/edit capability включается только для подтверждённых типов устройств/версий.
9. Trend plots/histories: импорт конфигурации и чтение исторических данных, контролируемые окна/скорость, checkpoint/resume.
10. Multi-vCNC primary/secondary failover и распределение нагрузок — после проверки ограничений сети.
11. SET XML migration и 963 schematic migration — отдельные безопасные import pipelines.
12. Никакой синхронизации времени, записи параметров или перепрограммирования контроллера автоматически.

## 7. Архитектурные изменения общего уровня

- Driver SDK должен поддерживать lifecycle initialize/configure/validate/start/stop/shutdown и capabilities.
- Driver Manager должен управлять реальными экземплярами, но никогда не обходить RBAC и не хранить секреты в config JSON.
- Общие Device/Point Registry и identity resolver для всех протоколов.
- Point adapter публикует только в существующий UID и проверяет владельца driver_instance_id.
- Все consumers (FBD, graphics, alarm, history) читают один PointRuntime.
- Последнее значение сохраняется при потере связи, но quality становится STALE/COMM_LOST; BAD/COMM_LOST не допускается к управляющей логике.
- Polling/transport не блокирует UI/API/event loop.
- Отдельные per-device diagnostics, raw sanitized traces, counters, latency, retry, last success/failure.
- Секреты secure vCNC и credentials хранятся в SecretStore; не писать их в журнал/trace.

## 8. План DEV113+

| Этап | Результат | Критерий завершения |
|---|---|---|
| DEV113-A | Нормализация каталога и Driver SDK contracts | Только три драйвера; capability/status правдивы; tests |
| DEV113-B | BACnet hardening + polling adapter | Simulator integration → PointRuntime; fault/quality/reconnect tests |
| DEV113-C | Modbus map + polling adapter | Import preview → polling → PointRuntime; register simulator |
| DEV113-D | Trend TCP connection + codec | Codec vectors и соединение с тестовым vCNC; протокол подтверждён |
| DEV113-E | Trend discovery + point import | Реальный Site/LAN/device/point inventory без записей |
| DEV113-F | Trend alarms/schedules/histories | Раздельные acceptance tests по каждому типу данных |
| DEV113-G | SET/963 migration | Preview, mapping, commit, rollback, отчёт |
| DEV113-H | Unified command layer | RBAC, limits, interlocks, read-back, audit; отдельная приёмка |

## 9. Блокирующие входные данные для реального Trend протокола

Публичные руководства подтверждают TCP vCNC endpoint, параметры подключения, модели объектов и инженерные сценарии, но не дают достаточной полной спецификации всех Trend wire frames, session negotiation, response correlation, secure vCNC handshake, point read/write payloads и plot/alarm payloads.

Для production Trend IP codec нужен один из следующих разрешённых источников:
- официальная протокольная спецификация/SDK от Trend Controls;
- письменное разрешение и документированный интерфейс для независимой интеграции;
- предоставленный владельцем проекта тестовый vCNC/контроллер и разрешённый read-only acceptance interface с известными test vectors.

До получения спецификации нельзя заявлять, что Trend IP Driver реализован, и нельзя заменять его BACnet. Secure vCNC нельзя считать поддержанным по одному факту доступности TCP порта.

## 10. Ссылки на использованные материалы

- IQVISION Configuration Manual TE201382: https://autorem.fr/Docs/Trend/IqVision/En_Conf_IQVISION.pdf
- IQVISION Data Sheet: https://autorem.fr/Docs/Trend/IqVision/En_ds_IQVISION.pdf
- Trend IQ4 Configuration Manual TE201263: https://prod-edam.honeywell.com/content/dam/honeywell-edam/hbt/en-us/documents/manuals-and-guides/user-manuals/trends-110725/hon-ba-bms-en-te201263-uk8pr1223r.pdf
- Trend IP Tool Manual TE200638: https://device.report/m/ccc7d5e3ac5218e93e7ec1a82477e1a1ea29745af2cff46896df658ae6678b99
- Modbus specifications: https://www.modbus.org/modbus-specifications
- Modbus TCP Messaging Guide V1.0b: https://www.modbus.org/docs/Modbus_Messaging_Implementation_Guide_V1_0b.pdf
- IQVISION/Niagara reference inventory and licensing review: `docs/NIAGARA_REFERENCE_REVIEW_RU.md` (DEV112).

## 11. Проверки и ограничения

- Исходники и документация просмотрены через GitHub; материалы IQVISION курса ZIP инвентаризированы (204 элемента) и слайды по Manual Discovery, BACnet Driver, SET Migration извлечены для анализа.
- Unit tests / CI для DEV113 на момент создания документа **не запускались**.
- Нет подтверждённого подключения к реальному Trend vCNC, BACnet сети или Modbus TCP устройству в рамках этого аудита.
- Наличие документа, тестового simulator или transport client не считается подтверждением field acceptance.
- Niagara JAR не декомпилировались и не использовались как исходный код. Функциональные требования формируются независимо.
