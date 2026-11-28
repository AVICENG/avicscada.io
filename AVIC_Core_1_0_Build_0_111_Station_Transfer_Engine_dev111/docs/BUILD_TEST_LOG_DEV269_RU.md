# AVIC Core — журнал DEV269 (driver CI review и IPC stress-test hardening)

Дата: 28.11.2026  
PR: #11 — drivers/modbus-rtu-c-worker-dev249  
Проверяемый CI run: [46153350062](https://github.com/AVICENG/avicscada.io/actions/runs/46153350062)  
Проверяемый branch HEAD: `8ee1832040d251a44aa8219fc63b780d97da2229`

## Подтверждённые результаты run 46153350062

- Modbus C Worker / Linux: **10 passed**, включая RTU PTY FC03 round-trip с CRC.
- Modbus C Worker / Windows UCRT64: **9 passed, 1 skipped**. Пропущен только Linux PTY-only сценарий. Windows C Worker успешно собран.
- BACnet Stack POC: Windows и Linux build/CTest jobs — **success**. Linux upstream `bacserv` integration подтвердила ReadProperty ACK и Error; I-Am/ReadProperty codec и malformed-input rejection прошли.
- Paho MQTT C Worker: Linux Mosquitto и Windows MSVC/Mosquitto — **по 7 passed**. В набор входят IPC handshake/shutdown, invalid configuration rejection, broker reconnect/resubscribe и broker-to-Point-Runtime round-trip.
- Полная Python matrix: Linux Python 3.11/3.12/3.13 — success; Windows Python 3.11 и 3.13 — success.

## Найденная регрессия общего IPC stress-test

Windows Python 3.12 завершился с **1 failed, 31548 passed, 18 skipped**. Единственный failure:

`tests/test_rust_driver_worker_supervisor_dev218.py::test_async_event_queue_overflow_drops_only_replaceable_samples_and_counts_them`

Тест отправляет 300 последовательных IPC event frames, а использовал общий двухсекундный timeout. На Windows runner чтение/декодирование всей пачки не уложилось в этот лимит; тест завершился тайм-аутом ожидания read response. В Python 3.11 и 3.13 этот тест прошёл.

## Изменение DEV269

- Для этого конкретного искусственного stress-test timeout увеличен с 2 до 10 секунд.
- Production `RustDriverWorker.timeout_seconds`, IPC semantics, queue capacity, drop policy и fail-closed поведение не менялись.
- Все проверки количества событий, overflow count и queue depth сохранены.
- Это устранение нестабильного лимита тестового стенда, а не объявление проблемы решённой. Требуется повторный CI на новом HEAD.

## Статусы драйверов после анализа

- Modbus TCP/RTU — 🟨; Windows virtual COM и hardware acceptance остаются открыты.
- BACnet/IP — 🟧; POC и simulator ACK/Error подтверждены, AVIC IPC Worker ещё не реализован.
- MQTT — 🟨; нативный Worker и broker round-trip/reconnect прошли на Windows/Linux, но TLS, SecretStore credentials и MQTT 5 не входят в текущий scope.
- OPC UA — 🟧; native probe, но не полный AVIC IPC Worker.
- BACnet MS/TP, Siemens S7 и Wired M-Bus — ⬜ до реализации соответствующих Workers.

## Следующий цикл

1. Повторить полный Windows/Linux Python matrix после DEV269.
2. Продолжить BACnet/IP: AVIC C Worker поверх Steve Karg Stack, единый IPC, discovery, ReadProperty/ReadPropertyMultiple и Point Runtime.
3. Вернуться к Modbus RTU COM normalizer unit tests и Windows virtual-COM round-trip.
4. Усилить MQTT TLS/SecretStore и эксплуатационные fault/soak gates.
5. Переходить к OPC UA, BACnet MS/TP, Wired M-Bus и техническому решению по чистому C S7 engine.

Ни один протокол не считается аппаратно принятым без реального контроллера/шлюза и отдельного журнала испытаний.
