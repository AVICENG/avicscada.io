# Матрица выбора промышленных протокольных стеков AVIC

Дата: 27.11.2026  
Статус: **ENGINEERING DECISION — выбор кандидатов для PoC; не означает production acceptance**

## 1. Принцип

Драйвер — сменный транспортный адаптер, а не часть ядра. AVIC Core владеет инженерной моделью, Point Definition/State/Sample, canonical Quality/Time, безопасностью, лицензиями, Command Gateway, FBD, тревогами, архивом и publish lifecycle. Внешний стек владеет только реализацией протокола, сетевыми сессиями, пакетированием запросов, subscriptions/COV, протокольным декодированием и диагностикой.

Любая библиотека работает внутри отдельного worker процесса либо изолированного runtime host. Ни одна библиотека не получает прямой доступ к Object Repository, Point DB, RBAC, SecretStore или физическим командам.

## 2. Выбранные кандидаты

| Протокол | Первый кандидат | Резерв / контрольный кандидат | Решение на текущем этапе |
|---|---|---|---|
| Modbus TCP/RTU | **libmodbus 3.2.x (C)** | текущий Rust worker / tokio-modbus | libmodbus — первый C-worker PoC; Rust не удалять до parity и soak |
| BACnet/IP + MS/TP | **Steve Karg BACnet Stack (C)** | **CAS BACnet Stack (C/C++)** | Karg — open-source PoC; CAS — коммерческий кандидат для поддержки и расширенного профиля |
| BACnet/SC | **CAS BACnet Stack** | отдельный сертифицированный коммерческий SDK после RFP | Не обещать BACnet/SC на базе текущего Rust/Python пилота; подтвердить профиль, hub/CA и BTL evidence у поставщика |
| KNXnet/IP / KNX Secure | **KNX Falcon 6 .NET SDK** | существующий AVIC/Rust codec как тестовый reference | Официальный SDK — первый PoC через отдельный .NET worker; проверить фактическую поддержку режимов и платформ |
| OPC UA Client | **open62541 (C)** | Eclipse Milo (Java) | open62541 — первый native worker PoC; Milo оставить альтернативой, если feature coverage/CTT окажутся лучше |
| Trend IP / vCNC | Только документированный/лицензированный Trend интерфейс | BACnet для устройств, которые действительно предоставляют BACnet | Не писать закрытый wire protocol по догадкам и не считать BACnet заменой Trend IP |

## 3. Обоснование и ограничения

### 3.1 Modbus — libmodbus

Плюсы:
- зрелая C-библиотека с Modbus TCP и serial RTU;
- upstream документирует Linux и Windows, включая Visual Studio;
- нет обязательного внешнего runtime;
- актуальная upstream-линия 3.2.0 содержит исправления валидации длины запросов и целочисленных операций;
- небольшой и понятный API подходит для изолированного worker.

Ограничения:
- LGPL-2.1-or-later — до коммерческого распространения требуется юридическое решение по dynamic linking/замене/коммерческой лицензии;
- библиотека не заменяет AVIC scheduler, register-map importer, batching planner, quality mapping, retry/backoff и Command Gateway;
- корректность конкретных устройств, endian/word order, vendor register maps и serial adapters подтверждается отдельно.

Решение: собрать C worker с libmodbus как изолированный executable. Сравнивать с Rust worker на одном AVIC IPC и одном наборе сценариев. Не встраивать native DLL непосредственно в Python Core.

### 3.2 BACnet — Karg и CAS

Steve Karg BACnet Stack:
- portable C, application/network/MAC layers;
- исходный проект заявляет Windows/Linux/macOS/BSD и embedded build;
- есть unit tests, CI/static analysis и примеры;
- хороший кандидат для открытого PoC и контроля протокольного поведения.

CAS BACnet Stack:
- коммерческий C/C++ stack с исходным кодом и готовыми сборками Windows/Linux/ARM;
- поставщик заявляет BACnet/IP, MS/TP и BACnet/SC, а также client/server API и адаптеры для разных языков;
- предоставляет более прямой путь к vendor support, но условия лицензии, support SLA, BTL profiles, BACnet/SC Hub/CA и ограничения redistribution должны быть получены письменно.

Критически важно: «BACnet supported» не означает одинаковый охват ReadPropertyMultiple, segmentation, COV, alarms/events, schedules, trend logs, BBMD/Foreign Device, routing, MS/TP и BACnet/SC. Для каждого сервиса нужна feature matrix и тест-вектор.

Решение: начать PoC с Karg для BACnet/IP и MS/TP; параллельно запросить CAS evaluation package и коммерческие условия. Для BACnet/SC не делать собственный production stack до сравнительного теста и письменного подтверждения поддержки.

### 3.3 KNX — Falcon 6

KNX Association предоставляет Falcon 6 .NET SDK через NuGet. Официальные требования указывают .NET 5+ на Windows/Linux/macOS; некоторые функции зависят от платформы и аппаратуры. Публичный SDK и manufacturer SDK имеют разные условия и доступность.

Решение: отдельный .NET worker, без зависимости Core от .NET. Проверить KNXnet/IP tunnelling/routing, secure tunnelling, group monitor, DPT catalogue, ETS project import, USB/IP interface support, reconnect и длительную работу. Не считать доступ к KNX bus автоматическим доказательством полного ETS engineering import.

### 3.4 OPC UA — open62541

open62541 — переносимый C99 OPC UA stack с клиентским и серверным SDK, plugin-based platform layer и MPL-2.0. Security stack включает SecureChannel, Session, certificates/trust и pluggable crypto backend. Нужно проверять точные OPC UA profiles, security policies, subscriptions, monitored items, events, methods, history и CTT для нужной роли клиента.

Решение: native C worker на open62541; Eclipse Milo — резервный Java-кандидат. Выбор окончательно фиксируется только после client-side CTT и тестов с разными vendor servers.

## 4. Общий AVIC Driver Contract

Все workers обязаны предоставлять одинаковые операции:
- manifest/capabilities/version/platform/license;
- initialize → validate → configure → start → status/diagnostics → stop → shutdown;
- immutable installation/project/station/driver_instance scope;
- bounded batch read с индивидуальным результатом каждого item;
- subscriptions/COV как capability, с polling fallback;
- cancellation, deadlines, backpressure, bounded queues, reconnect/backoff;
- typed values + raw protocol status + source timestamp + receive timestamp;
- worker identity, generation fencing, sequence и correlation ID;
- безопасная передача секретов через краткоживущий защищённый канал/secret reference;
- write capability по умолчанию выключена; физическая запись только через AVIC Command Gateway.

Batch — оптимизация транспорта, а не обещание атомарности группы регистров/объектов.

## 5. План внедрения по этапам

### Этап A — воспроизводимый стенд
1. Закрепить версии upstream по tag/commit и сохранить SBOM/license notices.
2. Собрать workers отдельно для Windows x64 и Linux x64.
3. Создать одинаковые simulators/test servers и golden test vectors.
4. Сравнить Python reference, Rust pilot и выбранный native SDK через одинаковый IPC.
5. Включить malformed frames, timeout, reconnect, server restart, partial response, duplicate/out-of-order, queue saturation и process crash.

### Этап B — read-only acceptance
- BACnet/IP: Who-Is/I-Am, ReadProperty, ReadPropertyMultiple, segmentation, errors/reject/abort, BBMD/Foreign Device по явной конфигурации, COV lease/renew/fallback.
- Modbus: FC01/02/03/04, MEI 0x0E, limits, grouped reads, sparse maps, exception responses, transaction IDs, persistent sessions, TCP/RTU.
- KNX: tunnelling/routing, cEMI, group monitor, DPT conversion, secure modes, reconnect.
- OPC UA: discovery, endpoint selection, certificates, browse, read, subscriptions, monitored item status, reconnect.
- Все значения проходят один и тот же AVIC Sample/Quality/Time contract.

### Этап C — отказоустойчивость и производительность
- 1k / 5k / 10k points; 1s/5s/10s polling profiles;
- 72-hour pilot soak, затем более длительный soak на целевом Edge hardware;
- p50/p95/p99 latency, update rate, CPU, RSS, queue depth, missed deadlines, reconnect time, duplicates, drops, data loss;
- Windows x64, Linux x64; ARM64 Edge — отдельный acceptance;
- fuzzing/negative tests, ASan/UBSan для native code, static analysis, reproducible builds, signed artifacts.

### Этап D — ограниченная запись
Разрешать только после:
1. SecurityGateway/Principal + RBAC + license + station scope;
2. Access Lease / interlock / freshness / quality policy;
3. единый Command Gateway с idempotency и audit;
4. протокольное подтверждение и отдельный read-back фактического состояния;
5. hardware acceptance для каждого write profile.

До выполнения этих условий все workers остаются read-only.

## 6. Сравнение с Niagara / Trend IQVision / Siemens Desigo CC

- Niagara: повторяем driver/device/point abstraction, сменные модули и фасеты возможностей; внутренний язык стека не попадает в инженерную модель.
- Trend IQVision: скрываем сложность соединений, batching, retry и протокольных особенностей от обычного инженера; импорт/выбор точек остаётся управляемым workflow.
- Siemens Desigo CC: ориентируемся на широкий набор интеграций, отдельные protocol drivers, SDK и распределённую эксплуатацию; не заявляем поддержку профиля без подтверждения.
- AVIC: единая модель точек, единый контракт данных, единая безопасность и единая команда независимо от языка worker.

## 7. Запреты и критерии production

Запрещено:
- объявлять драйвер production-ready по unit tests codec-only;
- считать наличие протокольной библиотеки подтверждением поддержки всех сервисов;
- добавлять native library в Core process без необходимости и threat review;
- включать физические writes по умолчанию;
- угадывать Trend proprietary protocol или модель устройства;
- удалять Rust/Python implementation до parity, soak и rollback evidence.

Production gate:
- feature matrix с доказательствами;
- юридически проверенная лицензия и redistribution;
- реальные контроллеры минимум нескольких производителей;
- conformance/interoperability tests, если применимы;
- 72-hour minimum pilot soak без утечек/необъяснимых пропусков;
- Windows/Linux/Edge deployment;
- SBOM, CVE monitoring, signed artifacts;
- отчёт с измеренными latency/throughput/recovery;
- документированный rollback на предыдущий worker.

## 8. Официальные источники

- libmodbus: https://libmodbus.org/ ; https://github.com/stephane/libmodbus
- libmodbus 3.2.0 release notes: https://github.com/stephane/libmodbus/releases
- Steve Karg BACnet Stack: https://github.com/bacnet-stack/bacnet-stack
- CAS BACnet Stack: https://www.bacnetstack.com/ ; https://www.bacnetstack.com/documentation/
- KNX Falcon 6 requirements: https://support.knx.org/hc/en-us/articles/4410825434642-Requirements
- KNX Falcon 6 release: https://support.knx.org/hc/en-us/articles/31860216353426-Falcon-6-NET-SDK-v6-4-0
- open62541: https://open62541.org/doc/v1.5.7/ ; https://github.com/open62541/open62541
- Eclipse Milo: https://github.com/eclipse-milo/milo

**Юридическое замечание:** эта матрица не является юридическим заключением. Для каждой версии необходимо сохранять фактический LICENSE/NOTICE из upstream source archive и проверять условия распространения в составе коммерческого AVIC installer.
