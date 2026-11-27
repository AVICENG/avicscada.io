# AVIC Core — полный проход по основной девятке протоколов DEV248

Дата: 27.11.2026
Ветка: `drivers/protocol-roundtrip-dev248`
База: DEV247 `af497c80d044d40705adf50e90b249b4e42a4ef0`

## Назначение

Этот документ фиксирует фактическое состояние всех девяти согласованных направлений. Он не объявляет протокол готовым по наличию библиотеки, отдельному probe или старому тесту. Изменения реализации принимаются только после Windows/Linux CI и сохранения прежних результатов.

## Цветовая шкала

- 🟦 **Синий** — подтверждено на реальном оборудовании; в журнале есть модель, firmware, конфигурация и результат.
- 🟩 **Зелёный** — заявленный программный объём реализован и целевые автоматические тесты прошли на Windows и Linux.
- 🟨 **Жёлтый** — частичная AVIC интеграция или ограниченный read-only runtime.
- 🟧 **Оранжевый** — нативная библиотека/probe/POC собраны, но полноценного AVIC Worker нет.
- 🟥 **Красный** — актуальный тест или CI завершился ошибкой.
- ⬜ **Серый** — не реализовано или не проверено.

Цвет присваивается отдельно протоколу и каждому acceptance gate. Исторический зелёный результат не означает, что новый commit уже проверен.

## Итоговая карта

| Направление | Целевой движок | Текущий код | Цвет |
|---|---|---|---|
| Modbus TCP | libmodbus, C | C Worker; read-only FC01/02/03/04; IPC framing, simulator smoke | 🟩 программный базовый объём |
| Modbus RTU | libmodbus, C | C Worker RTU transport не реализован; serial configuration/ownership отсутствуют | ⬜ |
| BACnet/IP | Steve Karg BACnet Stack, C | Python read-only discovery/ReadProperty + отдельный C stack probe; C IPC Worker отсутствует | 🟨 |
| BACnet MS/TP | Steve Karg BACnet Stack, C | stack probe не подтверждает MS/TP worker; serial/token lifecycle и hardware acceptance отсутствуют | 🟧 |
| Siemens S7 / S7comm | Только C | S7 отключён в каталоге; Rust/Python protocol paths выведены из целевого runtime; C Worker отсутствует | ⬜ |
| MQTT | Eclipse Paho MQTT C | Python subscribe runtime; Paho C Worker и SecretStore credential handoff отсутствуют | 🟨 |
| OPC UA Client | open62541, C | C native secure read/Browse probe; AVIC IPC Worker, Browse paging, subscriptions/reconnect отсутствуют | 🟧 |
| Wired M-Bus | libmbus, C | спецификация и catalog entry; Worker отсутствует | ⬜ |
| KNXnet/IP | XKNX, Python | текущий самописный Python tunnelling/cEMI runtime и тесты; XKNX не интегрирован | 🟨 |

Синей аппаратной отметки пока нет ни у одного из девяти направлений: в рассмотренных CI и журналах нет полного подтверждения реального оборудования для этой девятки.

## Протоколы: обязательный следующий объём

### 1. Modbus TCP — libmodbus C

Сохранять существующий Worker и IPC. Не создавать второй Modbus runtime.

Уже заявленный объём: FC01/02/03/04 read-only, проверка диапазонов, ограничение размера чтения, simulator IPC smoke. DEV247 добавил тестовые сценарии для FC01/02/04 и oversized reads; они должны пройти в новом CI.

Дальше:
- проверить корректность framing, malformed JSON, duplicate keys, EOF и частичный frame;
- проверить reconnect после socket reset, timeout и Modbus exception;
- исключить зависание/неограниченное выделение памяти при некорректном вводе;
- проверить batch planner и границы PDU;
- добавить long-running soak и benchmark на одинаковой конфигурации Windows/Linux;
- после этого подключать управляемый polling и map import отдельными этапами.

### 2. Modbus RTU — libmodbus C

Расширить тот же C Worker, но с отдельной transport configuration. Не смешивать TCP host/port и RTU serial parameters.

Обязательные поля: serial port, baud, parity, data bits, stop bits, unit ID, response timeout, inter-frame policy. Нужен единый Serial Port Manager с эксклюзивным владением портом и диагностикой конфликтов.

Тесты: pseudo-terminal/виртуальный COM, CRC failure, short frame, timeout, late response, wrong slave ID, reconnect, serial unplug/replug, bus contention. Физические RS-485 адаптеры и реальные устройства — отдельный acceptance gate. Никаких записей в первом релизе.

### 3. BACnet/IP — Steve Karg BACnet Stack C

Существующий Python runtime не считать целевым движком. C probe не считать Worker.

Сначала повторить file-level SPDX audit на pinned commit и на точном CMake source set. Предыдущий аудит выявил GPL-2.0-or-later WITH GCC-exception-2.0, MIT и Apache-2.0 в разных файлах. Для коммерческого пакета сохранять список реально включённых файлов, license texts и notices.

C Worker scope: Who-Is/I-Am, Device identity, ReadProperty, bounded ReadPropertyMultiple, segmentation limits, invoke-ID lifecycle, timeout/retry, network-interface selection, broadcast policy, BBMD/foreign-device только отдельными настройками. В AVIC каталог переводить в C-worker maturity только после IPC contract tests и удаления старого Python transport path.

### 4. BACnet MS/TP — Steve Karg BACnet Stack C

Отдельный transport mode того же BACnet Worker, не отдельная протокольная реализация.

Необходимо: serial ownership, baud/parity/stop bits, MAC, max-master, max-info-frames, token passing, frame timing, retry policy, RS-485 direction control при необходимости, bus diagnostics и защита от нескольких masters. Тесты на виртуальном serial bus не заменяют испытания с несколькими физическими устройствами. Не включать MS/TP в каталог как работающий транспорт до hardware acceptance.

### 5. Siemens S7 — только C

DEV247 корректно перевёл S7 в PLANNED и удалил прежний Rust S7 route и Python S7 extras. Это сохраняется. Не возвращать Rust/Python fallback.

Snap7 — C API поверх C++ codebase/toolchain, поэтому не соответствует строгому условию pure-C реализации без отдельного согласования. libnodave — C, но upstream прямо предупреждает о beta-статусе и рисках; не принимать его в промышленную сборку без полного аудита, hardening, fuzzing и аппаратных испытаний.

Следующий шаг — технический spike по Snap7 C ABI/C++ core и независимая оценка чисто C вариантов. До положительного решения S7 остаётся выключенным. Не писать собственный стек вместо библиотеки без отдельного решения и спецификации. Разделить classic S7comm и S7CommPlus capabilities; не заявлять TLS/optimized DB/symbolic browsing без фактической поддержки и испытаний.

### 6. MQTT — Eclipse Paho MQTT C

Официальный Paho C поддерживает Windows/Linux, синхронный и асинхронный API, MQTT 3.1/3.1.1/5.0, TLS, automatic reconnect и persistence. Для AVIC выбрать asynchronous API и один Paho C Worker.

Первый scope: subscribe-only, topic filters, QoS 0/1/2, retained message semantics, payload bounds, JSON/raw decode, reconnect/backoff, TLS CA/hostname verification. Секреты не передавать в обычном JSON IPC или DriverInstance config; спроектировать SecretStore handoff без argv/env/log leakage.

Тесты с Mosquitto/EMQX: broker restart, QoS duplicates, retained, malformed payload, oversized payload, TLS invalid CA/hostname, reconnect storm, slow consumer/backpressure, persistent session. Удалять Python MQTT protocol adapter только после полной замены и регрессии.

### 7. OPC UA Client — open62541 C

Сохранить DEV227 secure native probe как проверенную основу, но не маркировать её как готовый драйвер.

Worker scope: endpoint discovery; security policy Sign/SignAndEncrypt only; certificate validation fail-closed; SecretStore key handoff; namespace URI mapping; paginated Browse/BrowseNext; Read; DataChange subscriptions; reconnect/session renewal; type/status mapping; bounded queues; generation fencing.

Тесты: OPC UA server simulator, certificate rotation/revocation, invalid hostname/trust chain, server restart, subscription overflow, bad status codes, namespace index changes, continuation points, malformed NodeId, load/soak. Запись запрещена в read-only этапе. Hardware acceptance — отдельный gate.

### 8. Wired M-Bus — libmbus C

Реализовать отдельный C Worker на libmbus. В scope только wired M-Bus через serial master/converter и TCP gateway. Wireless M-Bus не включать.

Тесты: primary/secondary addressing, scan collision, long/short frames, checksum, variable data records, DIF/DIFE, VIF/VIFE, manufacturer identification, units/multipliers, tariffs, timestamps, malformed telegrams, timeout/reconnect, gateway disconnect. Сохранять raw telegram trace для диагностики с удалением чувствительных данных. Физические счётчики и разные конвертеры обязательны для синего статуса.

### 9. KNXnet/IP — XKNX Python

Пользовательское правило C-first допускает Python, если зрелой подходящей C-библиотеки нет. XKNX выбран как целевая поддерживаемая библиотека; текущий самописный tunnelling/cEMI код — переходный legacy path.

Сначала проверить XKNX на поддерживаемой версии Python AVIC, включая фактический Python 3.15.2. Интегрировать через отдельный Python Worker с тем же AVIC IPC Contract, не через прямые вызовы из Core.

Сохранить AVIC point bindings и DPT mapping, если они корректны; заменить только protocol transport/codec. Проверить tunnelling, routing, reconnect, IP Secure/Data Secure, group monitor, DPT encode/decode, duplicate telegrams, sequence/ACK, multiple sessions, ETS import compatibility. Удалять самописный KNX transport и экспериментальный Rust KNX только после parity tests и hardware acceptance.

## Исторические результаты, которые нельзя терять

По DEV247 ledger, для базового DEV245 commit:
- C libmodbus Worker build + IPC smoke: Ubuntu — Passed; Windows UCRT64 — Passed.
- BACnet Stack POC build/probe: Ubuntu и Windows — Passed; это только POC.
- open62541 native probe: Ubuntu и Windows UCRT64 — Passed; это только POC.
- Rust Communication Engine tests и synthetic benchmark: Ubuntu и Windows — Passed; не считать подтверждением S7.
- Полная Python-регрессия DEV245 имела по одному отказу на завершённых matrix jobs из-за устаревших ожиданий каталога (16 вместо 17; затем ожидание S7 как read-capable). DEV247 изменил эти тесты, но окончательный результат нового CI на DEV247 пока не получен.

Точные старые числа из DEV247 ledger:
- Linux Python 3.11/3.12/3.13: 31,493 passed / 1 failed / 5 skipped на каждом завершённом matrix job.
- Windows Python 3.11 и 3.13: 31,492 passed / 1 failed / 6 skipped; результат Windows Python 3.12 не переносить из других матриц.

## Общие acceptance gates для каждого Worker

1. Pinned upstream commit, license inventory, notices, SBOM и воспроизводимая сборка.
2. Windows и Linux build в чистом CI окружении.
3. AVIC IPC contract: framing, version, scope, generation, sequence, bounded payloads, malformed input, orderly shutdown.
4. Protocol simulator/emulator tests и negative tests.
5. Timeout, reconnect, backoff, stale quality invalidation, bounded memory/queues.
6. Security: no secrets in config/argv/env/logs; certificate validation fail-closed; no protocol writes in read-only build.
7. Load/soak tests с опубликованными latency/throughput/p95/p99 и ресурсными метриками.
8. Hardware acceptance с точной моделью, firmware, конфигурацией, сетевой схемой и журналом.
9. Только затем менять Driver Catalog lifecycle и удалять старые реализации.

## Ограничение DEV248

DEV248 на этом этапе — архитектурный и кодовый аудит девяти направлений. Он не объявляет новые Worker реализованными. Следующий кодовый цикл должен закрывать конкретные acceptance gates, начиная с расширения существующего libmodbus C Worker до RTU и подготовки BACnet C Worker. CI DEV247 остаётся ожидающим отдельного результата и не переобозначается как Passed.
