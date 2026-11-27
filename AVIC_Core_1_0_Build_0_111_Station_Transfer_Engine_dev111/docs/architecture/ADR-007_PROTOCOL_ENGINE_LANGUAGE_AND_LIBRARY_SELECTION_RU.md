# ADR-007 — Выбор языка и библиотек для Protocol Engine

Статус: **PROPOSED — требуется сравнительный прототип**  
Дата: 27.11.2026  
Область: Modbus TCP/RTU, BACnet/IP, BACnet MS/TP, BACnet/SC, KNXnet/IP и будущие протоколы.

## 1. Решение, которое требуется принять

Не назначать Rust или C++ единственным языком коммуникационного слоя до проверки библиотек. Выбирать реализацию отдельно для каждого протокола, но требовать один AVIC Driver Contract и один IPC/API контракт для всех реализаций.

Основной критерий — не синтаксис языка и не benchmark «пустого сокета», а готовность проверенного стека закрыть нужный профиль протокола, лицензия, сопровождение, безопасность, Windows/Linux, нагрузка, диагностика и стоимость поддержки.

## 2. Предварительная оценка экосистемы

### Modbus

- **C/C++:** libmodbus — зрелая C-библиотека, которую можно интегрировать в C++ worker; покрывает Modbus TCP и последовательные варианты. Лицензия LGPL-2.1-or-later требует отдельного юридического решения для способа распространения и линковки.
- **Rust:** tokio-modbus — самостоятельная реализация Rust, но не следует считать её функционально эквивалентной libmodbus без тестов.
- **Python:** текущая реализация AVIC полезна как reference/compatibility oracle и инженерный fallback, но текущий Rust pilot уже показал, что одно чтение на binding — плохая архитектура независимо от языка.

Вывод: Modbus — лучший кандидат для сравнительного C/C++ прототипа на базе libmodbus против текущего Rust worker. Проверить persistent sessions, grouping contiguous registers, sparse ranges, max registers, retries, reconnect, exception handling, endianness/scaling и десятки тысяч bindings.

### BACnet

- Открытый BACnet Stack (C) предоставляет application/network/MAC layers, примеры client/server и платформы Windows/Linux/embedded. Перед включением в коммерческий продукт требуется проверить точные условия лицензии и все зависимости.
- Коммерческие C/C++ стеки, например CAS BACnet Stack, заявляют BACnet/IP, MS/TP и BACnet/SC, client/server и готовые платформенные сборки; это вариант закупки, а не предположение о бесплатности.
- Rust-реализация должна оцениваться по фактическому охвату BACnet services, object/property coverage, RPM, COV, BBMD/Foreign Device, segmentation, routing, MS/TP и BACnet/SC, а не только по успешному ReadProperty.

Вывод: BACnet имеет самый высокий риск неполного самописного стека. Сначала составить обязательный BACnet feature matrix и проверить open-source stack и коммерческий SDK на реальных контроллерах.

### KNX

- KNX Association публикует Falcon .NET SDK; публичная версия доступна через NuGet, а производительская редакция имеет отдельные условия доступа. Это сильный официальный кандидат для Windows/.NET worker, но не C++ библиотека.
- В C++ экосистеме встречаются knxd/linknx и embedded-oriented реализации; часть проектов имеет GPL-лицензии и/или предназначена для KNX device firmware, а не для полноценного KNXnet/IP client/router в AVIC.
- KNX Secure, tunnelling, routing, ETS project import, DPT catalogue и manufacturer-specific datapoint types должны быть отдельными пунктами оценки.

Вывод: нельзя утверждать, что C++ уже имеет лучший готовый KNX stack. Falcon .NET и зрелые KNXnet/IP реализации на других языках должны участвовать в сравнении наряду с C++.

## 3. Предлагаемая архитектура

AVIC Core (Python на текущем этапе) остаётся владельцем:
- проекта, станций, устройств, точек и инженерной модели;
- Point Definition / Point State / Sample;
- качества, времени, масштабирования и provenance;
- RBAC, лицензий, SecretStore и Command Gateway;
- alarm/history/event lifecycle, FBD, graphics и publish workflow.

Protocol Worker (C/C++, Rust или .NET по обоснованному выбору) отвечает только за:
- транспорт и протокольный стек;
- соединения, discovery в разрешённом профиле, polling, subscriptions/COV;
- protocol-native decoding до типизированного результата;
- диагностику транспорта и протокола.

Ни один worker не пишет в Point DB напрямую и не решает самостоятельно, разрешена ли команда. Все данные идут через версионированный IPC/Driver Contract; все записи — только через AVIC Command Gateway.

## 4. Единый Driver Contract — обязательные свойства

- capability manifest: protocol, role (client/server/router), services, transport, platform, security modes, library version/license;
- immutable instance scope: installation/project/station/driver instance;
- worker_id + generation + correlation_id + sequence;
- explicit connect/disconnect/health/reconfigure lifecycle;
- batch read/write requests with per-item result; batch is not an atomicity promise;
- subscription/COV support where protocol permits;
- source timestamp, received timestamp, protocol status, raw diagnostic and canonical AVIC quality;
- bounded queues, backpressure, cancellation, timeout and reconnect policy;
- secrets passed by reference/short-lived secure channel, never embedded in config/logs;
- no direct database, FBD, alarm, license or user management access;
- writes disabled unless capability, Principal, lease, interlocks and Command Gateway all authorize them.

## 5. Сравнительный прототип — одинаковые условия

Для каждого кандидата:
1. Одинаковые устройства/симуляторы и сценарии.
2. Один и тот же AVIC Driver Contract и одинаковый Python adapter overhead.
3. 1k / 5k / 10k points; contiguous и sparse registers; разное количество устройств.
4. Polling 1s/5s/10s; timeouts, network loss, server restart, slow response, malformed frames.
5. Long soak минимум 72 часа на пилотном этапе; production gate требует более длинного soak на целевом Edge hardware.
6. p50/p95/p99 latency, updates/s, requests/s, CPU, RSS, threads, handles/sockets, queue depth, missed deadlines, reconnect time, data loss/duplicates/out-of-order.
7. Проверка точности значений, signed/unsigned, float word/byte order, bit fields, status flags, timestamps и canonical quality.
8. Windows x64 и Linux x64; ARM64 Edge — отдельная проверка.
9. Проверка supply-chain: SBOM, CVE policy, reproducible build, binary signing, dependency pinning.
10. Полный license review для каждой библиотеки и каждого бинарного артефакта.

Не сравнивать голый throughput библиотек. Сравнивать end-to-end путь: socket → protocol stack → typed result → IPC → AVIC adapter → Point Runtime.

## 6. Критерии допуска библиотеки

- активное сопровождение или договорная поддержка;
- документированное покрытие необходимых protocol services;
- известная и совместимая лицензия;
- fuzzing/negative tests и корректная обработка malformed traffic;
- отсутствие неограниченного роста памяти/очередей;
- безопасный shutdown/reconnect;
- Windows/Linux deployment;
- совместимость с AVIC versioned contract;
- воспроизводимая сборка и проверка происхождения бинарника.

Популярность, звёзды GitHub и заявленная производительность сами по себе не являются критерием допуска.

## 7. Сравнение с тремя системами

### Niagara
Сохраняем driver/device/point abstraction и расширяемость модулей. Язык протокольного worker не должен просачиваться в инженерную модель. Как и у зрелой платформы, драйвер обязан предоставлять единый lifecycle, диагностику, facets/metadata и predictable point semantics.

### Trend IQVision
Сохраняем простоту инженерного опыта: инженер выбирает сеть, устройство и точки; batching, sessions, COV и особенности стека остаются внутренней реализацией. Никакого отдельного ручного управления worker для обычной настройки.

### Siemens Desigo CC
Учитываем широту протоколов и роли системной интеграции. Нужны capability profiles, безопасная эксплуатация и поддерживаемые версии стеков; протоколы с Secure Connect и vendor SDK не имитируются частичной самописной реализацией.

### AVIC
Один Core, один проект, одна модель точек, одна модель безопасности, один Command Gateway. Несколько языков допустимы только на границе изолированных workers и только при одинаковом контракте, тестах и диагностике.

## 8. Предварительная рекомендация

- Не переписывать всё на C++ и не удалять текущий Rust pilot.
- Создать C/C++ benchmark worker для Modbus на базе libmodbus и сравнить его с Rust pilot.
- Для BACnet провести отдельный proof-of-coverage открытого C stack против коммерческого стека; оценить не только BACnet/IP, но и требуемый roadmap BACnet/SC.
- Для KNX отдельно сравнить Falcon .NET, C++ варианты и текущие Rust кандидаты; не предполагать, что C++ здесь автоматически выигрывает.
- Python оставить reference implementation и orchestration layer до тех пор, пока измерения не докажут необходимость переносить его функции.

## 9. Условия принятия ADR

ADR не переводится в ACCEPTED, пока не получены:
- юридически проверенная матрица лицензий;
- feature matrix каждого протокола;
- runnable proof-of-concept каждого выбранного стека;
- parity tests с Python reference и реальными устройствами;
- end-to-end нагрузочные результаты;
- Windows/Linux/Edge deployment evidence;
- threat model, SBOM и signed artifact pipeline.

## 10. Источники для первичной проверки

- libmodbus ecosystem / protocol stack landscape: https://otfabric.io/blog/industrial-protocol-stack-landscape/
- Open-source BACnet stack: https://bacnet.sourceforge.net/
- CAS BACnet Stack: https://www.bacnetstack.com/
- BACnet stack comparison: https://www.bacnetstack.com/compare/
- KNX Falcon SDK (официально): https://support.knx.org/hc/en-us/articles/4410819043986-What-is-the-Falcon-NET-SDK
- KNX technology and official SDKs: https://knx.org/knx-technology
- KNX protocol implementation landscape: https://otfabric.io/ecosystem/implementations/

Сведения о функциях и лицензиях библиотек должны быть перепроверены по upstream release и license files на момент включения в поставку.
