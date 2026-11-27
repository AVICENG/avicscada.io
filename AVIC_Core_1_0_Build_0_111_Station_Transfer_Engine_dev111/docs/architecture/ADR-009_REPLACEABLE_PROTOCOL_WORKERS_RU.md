# ADR-009 — Принцип сменных Protocol Workers и выбор проверенных стеков

Статус: **ACCEPTED AS ARCHITECTURAL POLICY / CANDIDATE STACKS REQUIRE PoC ACCEPTANCE**  
Дата: 27.11.2026  
Область: AVIC Core, AVIC Edge Runtime, Driver Manager, Driver SDK, protocol workers.

## Контекст

Текущий AVIC содержит собственные read-only transport/codec реализации BACnet/IP, Modbus TCP и KNXnet/IP, а также экспериментальный Rust worker. Они полезны как reference implementations и тестовые эталоны, но пока не дают доказательств полного промышленного покрытия протоколов. В каталоге AVIC прямо указано отсутствие полного polling/COV/commands, а Trend IP/vCNC и OPC UA остаются planned.

Самописная реализация каждого протокола создаёт неоправданный риск: неполные сервисы, ошибки обработки malformed frames, segmentation, reconnect, security, serial timing, vendor interoperability и годы сопровождения.

## Решение

1. **Protocol Driver — сменный адаптер доставки, не часть AVIC Core domain model.**
2. AVIC Core владеет объектами, точками, quality/time/provenance, безопасностью, лицензиями, командами, тревогами, архивами, FBD, graphics и deployment.
3. Protocol Worker владеет только transport/session/protocol services/decoding/diagnostics.
4. Все workers используют один версионированный Driver SDK/IPC contract и один Sample contract.
5. По умолчанию workers read-only. Любая физическая запись только через Core Command Gateway.
6. Выбор языка делается по протоколу, а не единым правилом «всё C++» или «всё Rust».
7. Предварительно выбраны стеки для PoC: libmodbus (Modbus), Steve Karg + CAS (BACnet), KNX Falcon 6 (KNX), open62541 (OPC UA).
8. Текущий Rust worker и Python implementations сохраняются как reference/fallback до достижения parity, нагрузочных и полевых критериев. Запрещено удалять рабочий путь только ради смены языка.
9. Native/.NET workers работают отдельными процессами с подписанным manifest, ограниченным IPC, scope/generation fencing, bounded queues и supervisor lifecycle. Не загружать сторонние native stacks внутрь Core без отдельного ADR.

## Обоснование

- libmodbus — зрелая C-библиотека для TCP и RTU с официальной документацией Windows/Linux. LGPL-2.1-or-later требует юридически корректного способа распространения или коммерческой лицензии.
- Steve Karg BACnet Stack — переносимый C stack с тестами и примерами для Windows/Linux/embedded; подходит для открытого PoC. Его сервисное покрытие и BACnet/SC должны быть проверены, а не предположены.
- CAS BACnet Stack — коммерческий кандидат с заявленной поддержкой BACnet/IP, MS/TP и BACnet/SC, Windows/Linux/ARM и vendor support; требуется evaluation, письменное подтверждение профилей и условий.
- KNX Falcon 6 — официальный SDK KNX Association; .NET 5+ поддерживается на Windows/Linux/macOS, однако набор функций зависит от платформы и hardware.
- open62541 — C99 OPC UA stack, переносимый, с security stack и MPL-2.0; точные client profiles и CTT подтверждаются PoC.
- Eclipse Milo остаётся альтернативой, но Java worker не выбирается без измеренного преимущества.

## Последствия

Положительные:
- меньше собственного протокольного кода;
- замена стека не меняет проект и engineering model;
- протоколы могут использовать оптимальный runtime/язык;
- ошибки native stack изолируются процессом;
- проще обновлять и откатывать driver packages независимо от Core.

Отрицательные/затраты:
- несколько toolchains (C/C++, Rust, .NET) и supply-chain manifests;
- IPC serialization и supervisor lifecycle требуют надёжной реализации;
- лицензии и commercial SDK требуют отдельного контроля;
- разные версии стека могут иметь разное покрытие функций и диагностик.

## Условия внедрения

ADR фиксирует архитектурную политику и кандидатов, но не объявляет production acceptance. Для каждого выбранного стека обязательны:
- точная upstream version/tag и сохранённый source/license/SBOM;
- runnable worker и capability manifest;
- parity tests с текущим AVIC implementation;
- тесты с реальными контроллерами разных производителей;
- malformed traffic, timeouts, reconnect, crash/restart, backpressure, soak;
- Windows/Linux и целевой Edge hardware;
- performance и recovery отчёт;
- security review, signed artifacts и rollback plan.

Для Modbus первым PoC является libmodbus C worker. Для BACnet сначала выполняется сравнительный PoC Karg/CAS; при требовании BACnet/SC и vendor support CAS становится приоритетным коммерческим кандидатом. Для KNX первым PoC является Falcon 6 .NET worker. Для OPC UA — open62541.

Физические записи остаются выключенными до готовности Core Command Gateway, authenticated Principal/RBAC, Access Lease, interlocks, freshness, audit и hardware acceptance.

## Сравнение платформ

- Niagara: driver/device/point abstraction и модульность без утечки языка драйвера в модель инженерии.
- Trend IQVision: сложность polling, batching, retry и соединений скрыта за понятным инженерным workflow.
- Siemens Desigo CC: отдельные интеграционные драйверы, широкая protocol ecosystem и SDK; не заявлять неподтверждённые профили.
- AVIC: единая Core model, Driver Contract, Point Sample, security и command path для всех реализаций.

## Ссылки

См. `DRIVER_ENGINE_SELECTION_MATRIX_RU.md` — сравнительная матрица, ограничения, PoC-план, acceptance и официальные upstream источники.
