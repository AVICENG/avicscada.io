# AVIC Core — подготовка BACnet/IP C Worker, DEV250

Дата: 27.11.2026  
База аудита: DEV249 `a92778c29302371df27aab5257480f01cff9a090`  
Ветка: `drivers/bacnet-ip-prep-dev250`  
Назначение: подготовительный аудит следующего драйвера. Это не реализация и не результат CI.

## 1. Решение по библиотеке

Основной кандидат остаётся **Steve Karg BACnet Stack** — открытая переносимая библиотека на C. В AVIC уже закреплена ревизия:

`45f9831996f1a17504a790da91a4113f2974595c`

Текущий CMake POC использует FetchContent, отключает demo apps, включает BACnet/IP и отключает MS/TP, BACnet/SC, IPv6 и другие datalink. Для первой реализации это правильное разделение: BACnet/IP и MS/TP должны иметь отдельные транспортные профили и acceptance gates.

Upstream README описывает проект как C protocol stack для Linux, Windows, macOS и BSD и указывает автоматизированные CMake build/test workflows. Upstream FAQ и примеры содержат клиентские приложения `readprop`, `readpropm`, `whois`, а developer guide перечисляет обработчики ReadProperty и ReadPropertyMultiple. Источники:
- https://github.com/bacnet-stack/bacnet-stack
- https://github.com/bacnet-stack/bacnet-stack/blob/master/doc/README.faq
- https://github.com/bacnet-stack/bacnet-stack/blob/master/doc/README.developer

Лицензия не должна описываться как единая MIT/Apache. В основном коде встречается `GPL-2.0-or-later WITH GCC-exception-2.0`, а отдельные файлы имеют MIT/Apache-2.0. Существующий выборочный аудит сохранён в `docs/architecture/BACNET_STACK_LICENSE_AND_INTEGRATION_AUDIT_RU.md`. Перед выпуском нужен SPDX/SBOM по фактическому source set целевого CMake target и повторная юридическая проверка дистрибуции.

## 2. Текущее состояние AVIC

| Компонент | Что реально найдено | Оценка |
|---|---|---|
| Python BACnet/IP client | Собственный BVLC/NPDU/APDU codec, Who-Is/I-Am, ReadProperty, Object_List, RPM, диагностика пакетов | 🟨 |
| Python Point Adapter | Одноразовый polling через общий Point Runtime; сейчас читает Present_Value | 🟨 |
| BACnet property reader / inspector | Чтение metadata, Object_List, point/schedule snapshots; изолирует отдельные ошибки свойств | 🟨 |
| Steve Karg CMake POC | Собирает upstream target и запускает только проверку версии/имени Device object | 🟧 |
| Rust BACnet client | Экспериментальный read-only клиент на bacnet-rs; не целевой runtime | 🟧 |
| Полноценный AVIC C IPC Worker | Не найден | ⬜ |
| Реальное оборудование в acceptance-журнале | В этой ветке не подтверждено | ⬜ |

### Важное замечание по качеству данных

Текущий `BacnetIpPointAdapter.poll_once()` публикует успешное чтение Present_Value как `GOOD`. Отдельный `BacnetObjectReader` уже умеет читать Reliability и Status_Flags и определять flagged/unreliable состояние, но этот путь не связан с обычным polling adapter. При переходе на C Worker нельзя автоматически присваивать GOOD только потому, что APDU успешно получен. Нужно отдельно передавать и интерпретировать BACnet Reliability, Status_Flags, Out_Of_Service, возраст значения и communication state; отсутствие необязательного свойства не должно превращаться в выдуманное значение.

## 3. Что сохранить из существующего AVIC

Существующие тесты и контракты не выбрасывать. Их нужно перенести на C Worker и оставить в регрессии:

- `tests/test_bacnet_ip_client.py`: BVLC/NPDU, Who-Is/I-Am, forwarded NPDU, сетевые адреса, диагностика пакетов, реальный захват Trend IQ3.
- `tests/test_bacnet_rpm_dev224.py`: ReadPropertyMultiple, per-property Error, несовпадение object identity, duplicate/unbounded request и malformed response.
- `tests/test_bacnet_property_reader.py`: object metadata, независимые ошибки отдельных свойств, schedule property set, консервативная классификация.
- `tests/test_bacnet_device_inspector_dev33.py`: Device identity, Object_List, object names и snapshots.
- `tests/test_bacnet_ip_point_adapter_dev115.py`: Point Runtime, scaling, сохранение последнего значения при потере связи, driver ownership.
- `tests/test_modbus_bacnet_adapter_regression_dev223.py`: общая регрессия адаптеров.

Python и Rust реализации после миграции остаются только как временные compatibility/reference paths. Удалять их можно после доказанной parity, Windows/Linux CI, simulator и аппаратного acceptance. Не создавать второй собственный BACnet codec.

## 4. Целевая архитектура

```
AVIC Core / Driver Manager
        |
        | AVIC Driver Worker IPC Contract
        v
BACnet/IP C Worker
        |
        | Steve Karg BACnet Stack (pinned SHA)
        v
BACnet/IP UDP datalink
        |
        v
BACnet devices
```

Обязанности разделяются так:

- Steve Karg Stack: BACnet encoding/decoding, transaction state, invoke ID, confirmed/unconfirmed services, BVLC/NPDU/APDU и datalink.
- C Worker: безопасная конфигурация интерфейса/UDP, lifecycle, bounded request queue, correlation IPC request ↔ BACnet transaction, timeout/retry policy, mapping stack responses в AVIC-neutral payload.
- AVIC Core: station/device ownership, лицензирование точек, identity resolver, data quality, timestamps, Point Runtime, audit и дальнейшая передача данных в HMI/FBD.
- Никаких прямых записей из Worker в Point Runtime и никаких WriteProperty в первом read-only scope.

Не передавать секреты через обычный JSON IPC, argv, environment или логи. BACnet/IP discovery/read-only в первом этапе не требует credentials; BACnet/SC сертификаты и trust lifecycle — отдельный протокол/этап.

## 5. Этапы реализации BACnet/IP после закрытия Modbus

1. **C Worker skeleton:** pinned stack, reproducible CMake, Windows/Linux, IPC framing, lifecycle, configuration validation, graceful shutdown.
2. **Discovery:** Who-Is/I-Am, bounded scan, source address, Device Instance, Max APDU, segmentation capability, vendor ID. Vendor name/model/firmware хранить отдельно с источником и уровнем достоверности; не угадывать.
3. **ReadProperty:** invoke ID correlation, response source validation, ACK/Error/Reject/Abort, timeout, retry/backoff, property decoding.
4. **Object_List:** array index 0 для длины, bounded element reads, максимальный размер и защита от чрезмерных/циклических запросов.
5. **ReadPropertyMultiple:** bounded property count и APDU size, per-property errors, fallback на ReadProperty при ограничениях устройства, без потери частичных результатов.
6. **Segmentation:** учитывать Max APDU и segmentation объявленные устройством; явно сообщать unsupported/abort/too-big, не зависать и не усекать ответ.
7. **AVIC adapter parity:** native object identity, типы/units, source timestamp, quality, ownership, license point accounting, stale/communication state.
8. **Network diagnostics:** unicast/broadcast, interface selection, subnet scope, packet loss, duplicate I-Am, forwarded NPDU. BBMD/Foreign Device — отдельная контролируемая функция, не включать скрыто.
9. **Regression and soak:** Windows/Linux, simulator, fuzz malformed BVLC/NPDU/APDU, memory/queue bounds, latency p95/p99, reconnect and long-running soak.
10. **Hardware acceptance:** Trend controller пользователя плюс минимум один сторонний BACnet controller; записывать модели, firmware, интерфейс, конфигурацию, захваты и журнал тестов.

## 6. Минимальный acceptance matrix

| Группа | Обязательные сценарии |
|---|---|
| Build | Linux GCC/Clang; Windows MSVC или согласованный MinGW toolchain; warnings-as-errors |
| IPC | configure/start/read/shutdown; oversized frame; malformed JSON; wrong generation/identity; sequence mismatch |
| Discovery | I-Am unicast/broadcast/forwarded; self packet; duplicate device instance; wrong source; timeout |
| ReadProperty | ACK; Error; Reject; Abort; wrong invoke ID; wrong source; malformed tags; truncated/trailing bytes |
| Object_List | array length; empty list; large list; invalid object ID; timeout midway; bounded limit |
| RPM | multiple properties; per-property Error; unsupported RPM; too-large response; partial result; object mismatch |
| Segmentation | no segmentation; segmented response supported; segment timeout/duplicate/out-of-order; abort |
| Network | wrong subnet/interface; unicast; broadcast; packet loss; duplicate/reordered packets; reconnect |
| Safety | read-only enforced; no WriteProperty/Reinitialize/TimeSynchronization; no secret leakage |
| Runtime | GOOD only with valid quality evidence; unreliable/flags/out-of-service/stale/communication loss mapped conservatively |
| Load | many devices/objects; bounded queues; cancellation/shutdown; soak; latency p95/p99 |

Зелёный статус можно присвоить только после полной целевой software matrix на Windows и Linux. Синий — только после физического acceptance с журналом оборудования. POC build сам по себе не является доказательством готовности драйвера.

## 7. Текущее решение и ограничения

- BACnet/IP C Worker пока не реализован.
- CMake probe пока не проверяет ни один BACnet request/response.
- Текущий Python stack нельзя удалять до parity.
- Экспериментальный Rust BACnet не является целевой реализацией.
- BACnet MS/TP не включать в этот Worker scope: для него отдельный serial/token/RS-485 lifecycle и отдельные аппаратные тесты.
- BACnet/SC не включать: TLS, WebSocket, X.509 trust, certificate rotation/revocation и fail-closed поведение требуют отдельного проектирования.
- Никакие новые тесты BACnet этим документом не объявляются пройденными.

## 8. Порядок относительно Modbus

Эта ветка содержит только подготовительный документ. Изменения BACnet runtime не начинаются до закрытия Modbus TCP/RTU. После получения завершённого CI DEV249 работа сначала возвращается в Modbus: исправления, RTU negative tests, serial ownership и повторная регрессия. Только затем этот подготовительный план становится рабочим scope BACnet/IP.
