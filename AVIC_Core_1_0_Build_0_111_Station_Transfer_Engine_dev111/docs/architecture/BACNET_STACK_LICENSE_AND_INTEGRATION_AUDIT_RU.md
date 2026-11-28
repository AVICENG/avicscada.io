# BACnet Stack — лицензионный и интеграционный аудит

Дата аудита: 27.11.2026  
Исследуемый upstream: https://github.com/bacnet-stack/bacnet-stack  
Зафиксированная ревизия для воспроизводимой оценки: `45f9831996f1a17504a790da91a4113f2974595c` (ветка master на момент аудита; до внедрения требуется отдельная повторная проверка pin).

## Предварительное решение

**Steve Karg BACnet Stack — основной кандидат для BACnet C Worker POC.** Лицензия не блокирует закрытый AVIC Core сама по себе: upstream README прямо описывает GPL with exception и разрешает связывать библиотеку с проприетарным кодом без распространения GPL на proprietary application. Но это не разрешение игнорировать лицензии отдельных файлов: при изменении GPL-covered файлов распространяемые изменения должны оставаться под соответствующими условиями GPL. Все использованные исходники и порты должны пройти file-level SPDX audit.

Это инженерная оценка, не юридическое заключение. Перед коммерческим релизом — повторная проверка SPDX/SBOM и юридическая проверка дистрибуции.

## Лицензионные наблюдения upstream

- Основной код стека использует `GPL-2.0-or-later WITH GCC-exception-2.0`.
- Upstream `license/readme.txt` поясняет, что изменения core-кода, которые распространяются, должны быть опубликованы в соответствии с GPL; саму библиотеку разрешено связывать с proprietary code без превращения proprietary code в GPL.
- В репозитории также встречаются `MIT` и `Apache-2.0` файлы, в том числе приложения/примеры и отдельные platform helpers.
- Следовательно, запрещено маркировать весь upstream как «MIT», «Apache» или как одну общую лицензию. Для каждой закреплённой ревизии нужен SPDX-отчёт по реально компилируемому source set.

## Проверенные platform files

| Файл | SPDX в заголовке |
|---|---|
| `src/bacnet/datalink/bvlc.c` | GPL-2.0-or-later WITH GCC-exception-2.0 |
| `src/bacnet/datalink/datalink.c` | GPL-2.0-or-later WITH GCC-exception-2.0 |
| `ports/linux/bip-init.c` | GPL-2.0-or-later WITH GCC-exception-2.0 |
| `ports/linux/datetime-init.c` | GPL-2.0-or-later WITH GCC-exception-2.0 |
| `ports/linux/dlmstp.c` | GPL-2.0-or-later WITH GCC-exception-2.0 |
| `ports/linux/rs485.c` | GPL-2.0-or-later WITH GCC-exception-2.0 |
| `ports/win32/bip-init.c` | GPL-2.0-or-later WITH GCC-exception-2.0 |
| `ports/win32/datetime-init.c` | GPL-2.0-or-later WITH GCC-exception-2.0 |
| `ports/win32/dlmstp.c` | MIT |
| `ports/win32/rs485.c` | GPL-2.0-or-later WITH GCC-exception-2.0 |
| `ports/linux/mstimer-init.c` | MIT |
| `ports/win32/mstimer-init.c` | MIT |
| `ports/posix/bacfile-posix.c` | MIT |

Это выборочная проверка platform files, а не полный SBOM всего target. Перед сборкой production worker требуется автоматический отчёт по полному списку source files, полученному из CMake.

## Техническая пригодность

Upstream — переносимая C-библиотека для Windows, Linux, macOS и BSD; содержит application/network/media-access слои, BACnet/IP, MS/TP и BACnet/SC. Upstream CMake позволяет включать и выключать BACnet/IP, IPv6, MS/TP и BACnet/SC отдельно. В репозитории есть клиентские примеры `bacdiscover` и `bacpoll`, а upstream CI собирает проекты на Windows и Linux.

## Порядок внедрения

1. Зафиксировать commit SHA, сохранить upstream license files и сгенерировать SPDX manifest только для выбранного build target.
2. Добавить upstream CMake как pinned dependency, выключить demo apps и ненужные data links; собрать библиотеку на Windows/Linux.
3. Первый worker scope — BACnet/IP client: Who-Is/I-Am discovery, Device object identity, ReadProperty и ReadPropertyMultiple.
4. Discovery и чтение остаются read-only. WriteProperty не включать до интеграции через AVIC Command Gateway, RBAC, freshness/quality checks и audit.
5. Добавить BBMD configuration отдельно, без автоматического изменения сетевых настроек оборудования.
6. MS/TP включать после отдельной проверки serial port ownership, baud/parity/stop bits, MAC address, token timing и RS-485 адаптеров на реальном оборудовании.
7. BACnet/SC — отдельный этап: TLS 1.3, WebSocket transport, X.509 lifecycle, trust store, rotation/revocation и fail-closed certificate validation.
8. Проверить с Trend controller пользователя: Who-Is/I-Am, object list, vendor/model identity, Analog/Binary/Multi-state points, ReadPropertyMultiple, segmentation, timeout и reconnect. Никаких предположений о поддержке свойств без ответа устройства.

## Архитектурная граница AVIC

- Stack отвечает за BACnet encoding/decoding, transactions и data link.
- AVIC worker адаптирует ответы к IPC contract, но не публикует значения напрямую в HMI/FBD.
- Core валидирует scope, generation, device/object/property bindings, quality, timestamps и лицензирование, затем передаёт sample в Point Runtime.
- Любые физические записи остаются за Command Gateway; discovery/scan не выполняют WriteProperty.
- Vendor ID / vendor name, model, firmware и источник/достоверность хранятся раздельно; отсутствующие свойства не угадываются.

## Acceptance gates

- Windows/Linux compile с одинаковыми включёнными BACDL options.
- Unit tests upstream и AVIC worker contract tests.
- Локальный BACnet/IP simulator: Who-Is/I-Am, ReadProperty, ReadPropertyMultiple, error APDU, timeout, duplicate invoke ID, segmentation.
- Network tests: BBMD/unicast/broadcast, subnet boundary, packet loss, reconnect.
- Реальный Trend controller и хотя бы один сторонний BACnet controller.
- Никаких write tests до отдельного разрешённого Command Gateway сценария.


## DEV252 — нативная проверка BACnet I-Am codec

В C probe добавлен вызов именно API Steve Karg Stack, а не AVIC-самописного декодера:

- encode/decode I-Am payload с проверкой Device Instance, Max APDU, Segmentation и Vendor ID;
- перебор всех усечённых длин payload — каждая неполная форма должна отклоняться;
- проверка отклонения I-Am payload, содержащего не Device Object Identifier;
- strict compiler warnings для собственного C probe: `-Wall -Wextra -Wpedantic -Werror` или MSVC `/W4 /WX`.

Это повышает проверку native BACnet dependency, но **не является BACnet/IP Worker и не подтверждает сетевой обмен**. Текущий статус остаётся 🟧. Следующий этап — C Worker с BACnet/IP datalink, Who-Is/I-Am discovery, transaction correlation и ReadProperty; затем ReadPropertyMultiple, IPC contract, simulator и Windows/Linux acceptance.


## DEV253 — расширение negative-тестов I-Am и Windows CI

Добавлены отрицательные проверки:
- Segmentation enum за пределами `MAX_BACNET_SEGMENTATION`;
- Vendor ID больше 65535;
- ранее добавленные усечённые payload и неверный тип объекта.

CI run `46057725369` выявил:
- Linux BACnet Stack POC — passed;
- Windows BACnet Stack POC — failed только при компиляции AVIC probe: MSVC C4996 на upstream `getenv()` из `platform.h`; upstream static library собралась.
- Исправление в CMake: `_CRT_SECURE_NO_WARNINGS` определён только для AVIC probe target на MSVC, строгие `/W4 /WX` сохранены. Требуется подтверждение следующим CI run после изменения.

## Сводка регрессии DEV253

- Modbus C Worker: native Linux и Windows jobs в run `46057725369` — passed. Это подтверждает сборку и тесты конкретного CI набора, но не аппаратную приёмку RTU.
- Python full-suite на Linux: 31513 passed, 8 skipped, 1 failed (повторяется на Python 3.11/3.12/3.13). Единственный failure: `tests/test_driver_manager_dev57.py::test_stop_instance_close_failure_keeps_session`; assertion ожидает удаление session, фактически session остаётся в `_sessions`. Это не BACnet/Modbus C Worker test; выделено как отдельная регрессия менеджера драйверов.
- Windows Python jobs ещё выполнялись на момент проверки.
- BACnet статус остаётся 🟧 до подтверждения Windows/Linux POC, реализации AVIC BACnet/IP Worker, IPC и сетевого симулятора.


## DEV254 — первый сетевой путь BACnet/IP через upstream Stack

В native C probe добавлен отдельный режим `--discover-ms 100..30000`:
- инициализация BACnet Device и datalink через upstream `dlenv_init()`;
- регистрация upstream `handler_i_am_add` на I-Am;
- отправка Who-Is через `Send_WhoIs_To_Network()`;
- приём кадров через `datalink_receive()` и обработка `npdu_handler()`;
- периодическое обслуживание datalink и ограниченный таймаут;
- вывод найденных Device Instance, Max APDU, MAC length и BACnet network number.

Это уже использует сетевые datalink/NPDU/APDU механизмы Steve Karg Stack, но пока остаётся отдельным диагностическим probe: не AVIC IPC Worker, не полноценный AVIC discovery result model, не ReadProperty и не runtime polling. Режим требует BACnet/IP интерфейс и сеть, поэтому аппаратно-сетевое подтверждение отдельно от обычного CI.


## DEV256 — ReadProperty codec через Steve Karg Stack

В BACnet native probe добавлен offline round-trip для ReadProperty request:
- кодирование Analog Input / instance 42 / Present Value;
- декодирование штатным `rp_decode_service_request()`;
- проверка полного совпадения object type, instance, property и array index;
- проверка отклонения всех усечённых вариантов.

Проверка валидирует именно upstream ReadProperty service codec. Она ещё не отправляет подтверждённый запрос устройству и не проверяет APDU transaction state/timeout. Следующий шаг — transaction lifecycle через `Send_Read_Property_Request()`, `apdu_set_confirmed_ack_handler()`, TSM invoke ID и контролируемый ответ в simulator.


## DEV257 — подтверждённая ReadProperty transaction path (CI ожидается)

В C probe добавлен отдельный диагностический режим:

`avic-bacnet-stack-probe --read-property DEVICE_ID OBJECT_TYPE OBJECT_INSTANCE PROPERTY TIMEOUT_MS`

Режим использует upstream API Steve Karg Stack:
- `Send_WhoIs()` и штатную address binding table для обнаружения/привязки устройства;
- `Send_Read_Property_Request()` для формирования и отправки confirmed ReadProperty request;
- `apdu_set_confirmed_ack_handler()` + `rp_ack_decode_service_request()` для обработки ACK;
- штатные Error, Abort и Reject handlers с проверкой source address и invoke ID;
- TSM transaction state, invoke ID allocation/release и timeout через `tsm_invoke_id_failed()`;
- ограничение времени операции и размера копируемого application payload.

Вывод пока диагностический: application-data выдаётся в hex, а не преобразуется в типизированное AVIC Point Value. Команда не выполняет WriteProperty. Она не является AVIC Worker и пока не подключена к IPC/Driver Manager/Point Runtime.

**Проверки, которые ещё обязательны:**
1. Windows/Linux строгая сборка и CTest на новом HEAD.
2. Интеграционный тест с BACnet/IP simulator, собранным на том же upstream Stack: успешный ACK, BACnet Error, Reject, Abort, отсутствие ответа/TSM timeout, неверный invoke/source и повреждённый ACK.
3. Только после этого — AVIC IPC Worker, bounded queue, cancellation, quality/status mapping и reconnect.
4. Реальный контроллер: модель, firmware, network configuration и полный журнал.

Статус BACnet/IP остаётся 🟧 до завершения перечисленных gates. Сам факт наличия transaction path в исходнике не означает, что он уже собран, протестирован с simulator или принят на оборудовании.

## DEV258 — интеграционный тест ReadProperty на upstream BACnet Server

Добавлен тестовый стенд на официальном серверном примере Steve Karg Stack:
- CI собирает `apps/server/main.c` как `bacserv` из того же pinned upstream revision `45f9831996f1a17504a790da91a4113f2974595c`, что и AVIC probe;
- сервер запускается как Device Instance 123;
- AVIC probe использует отдельный UDP port 47809, сервер — 47808; broadcast destination клиента направлен на порт сервера;
- тест проверяет успешный ReadProperty ACK для Analog Input 0 / Present Value;
- затем проверяет BACnet Error для заведомо неподдерживаемого Property ID 511;
- протокольные кадры, Who-Is/I-Am, NPDU/APDU, ReadProperty request/response обрабатываются upstream Stack, отдельная самописная реализация BACnet в тесте не используется.

Файл теста: `tools/bacnet_stack_server_integration.py`.
CI: job `BACnet Stack POC / ubuntu-latest`; Windows продолжает проверять строгую native-сборку и codec tests.

**Статус на момент добавления:** интеграционный gate добавлен, но ещё не подтверждён CI. До успешного выполнения нельзя считать ACK/Error simulator tests пройденными. Следующие обязательные проверки: Reject, Abort, TSM timeout/retry, неверные invoke/source, повреждённый ACK, затем AVIC IPC Worker и read-only Point Runtime.


## DEV259 — исправление BACnet simulator interface binding

CI run `46121086036` завершился со следующими результатами:
- BACnet Stack POC / Windows — passed (native build/codec scope);
- BACnet Stack POC / Ubuntu — failed на старте `bacserv`;
- все Python matrix jobs Windows/Linux — passed;
- Modbus C Worker Windows/Linux, OPC UA native probe Windows/Linux, MQTT Paho C probe Windows/Linux, Rust Communication Engine Windows/Linux и S7 C-only policy Windows/Linux — passed в этом run.

Причина BACnet failure установлена по логу и upstream Linux port: тестовый скрипт передавал IPv4-адрес `10.1.0.182` в `BACNET_IFACE`, тогда как Steve Karg `bip-init.c` трактует переменную как **имя сетевого интерфейса** и использует её как `ifr_name` в ioctl. Поэтому `bacserv` сообщал `Failed to get an IP address from 10.1.0.182`.

Исправление DEV259:
- интерфейс выбирается из `ip -o route get 192.0.2.1` по токену `dev`;
- затем проверяется наличие корректного IPv4 на выбранном интерфейсе через `ip -o -4 addr show dev INTERFACE`;
- в `BACNET_IFACE` обоих процессов передаётся имя интерфейса, а не IPv4;
- IPv4 сохраняется только для диагностики;
- сообщения об ошибках startup/ACK/Error используют реальные переводы строк, а не буквальные последовательности `\\n`;
- добавлены unit tests для route parsing, отсутствующего интерфейса/IPv4 и ошибок команд.

**Статус проверки DEV259:** код и тесты добавлены в ветку; новый CI ещё не выполнен. ACK и BACnet Error через simulator остаются неподтверждёнными до успешного нового Ubuntu job. Hardware acceptance не выполнялась.


## DEV261 — unicast ReadProperty separation from discovery

DEV260 CI run `46122912454` completed on all matrix jobs. Linux Python 3.11/3.12/3.13: 31 524 passed, 8 skipped each. Windows Python 3.11/3.12/3.13: 31 521 passed, 11 skipped each. Native BACnet Windows build/codec passed; Ubuntu simulator integration failed with `BACnet ReadProperty overall timeout device_id=123` after the corrected interface name was successfully selected and `bacserv` remained running.

The next diagnostic separates two independent protocol paths:
1. direct BACnet/IP unicast ReadProperty to the known simulator endpoint (validates UDP endpoint, NPDU/APDU, TSM invoke ID, ACK/Error handlers and source-address match);
2. Who-Is/I-Am broadcast discovery (still a separate unresolved network gate).

The new probe option `--read-property-at` adds a static address-cache entry for the known device and bypasses Who-Is. It does not claim discovery success. The integration script targets local runner IPv4 → simulator UDP 47808, while client listens on 47809. It validates a Present_Value ACK and a deliberately unsupported property Error. Debug output is captured for diagnosis.

Additional parser self-tests cover IPv4 octet bounds, malformed address, trailing characters and invalid UDP port. The seven old C diagnostic strings with escaped literal backslash-n were corrected to emit line breaks.

**DEV261 is not yet compiled or CI-tested.** Do not promote BACnet/IP to green or blue from this diagnostic patch. If direct unicast succeeds, retain broadcast discovery as an explicit open gate; if it fails, use BIP trace and server logs to isolate addressing/port/NPDU/TSM behavior.
