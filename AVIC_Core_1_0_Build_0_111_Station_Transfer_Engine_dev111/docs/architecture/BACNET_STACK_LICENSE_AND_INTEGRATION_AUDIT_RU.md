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
