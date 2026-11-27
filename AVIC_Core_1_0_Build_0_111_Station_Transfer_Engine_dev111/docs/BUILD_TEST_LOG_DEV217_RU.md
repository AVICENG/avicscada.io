# Журнал DEV217 — Rust BACnet/IP и KNXnet/IP read-only kernels

Дата: 27.11.2026

## Цель
Расширить единый Rust Communication Engine тремя протоколами: Modbus TCP, BACnet/IP и KNXnet/IP. Все три должны в итоге передавать данные через один AVIC Driver IPC v1 и общий Point Runtime.

## Реализовано в Rust crate

### Modbus TCP
Существующая реализация AVIC:
- FC01 Read Coils
- FC02 Read Discrete Inputs
- FC03 Read Holding Registers
- FC04 Read Input Registers
- MBAP transaction/protocol/unit/length validation, exception response handling, byte count and address/quantity bounds.
- Только чтение; никаких FC05/06/15/16.

### BACnet/IP — экспериментальный read-only адаптер
- Добавлена закреплённая зависимость `bacnet-rs = 0.3.2`.
- `BacnetIpReadOnlyClient`: discovery конкретного BACnet/IP peer, Device Instance, Vendor ID/name, Max APDU и segmentation metadata.
- Чтение Object List и пакетное чтение общих свойств объектов через stack API.
- Сохранение numeric/boolean/string типов Present_Value; NaN/Infinity не превращаются в JSON числа.
- Нет вызовов WriteProperty, TimeSynchronization или DeviceCommunicationControl.

**Ограничение upstream:** BACnet-RS сам указывает, что проект активно разрабатывается и не готов для production; segmentation/reassembly, Alarm & Event, Trend Log, Schedule/Calendar и BACnet/SC в таблице реализации отсутствуют. AVIC не объявляет этот стек промышленно готовым. Нужны interoperability/fuzz/segmentation tests и проверка с реальными контроллерами.

### KNXnet/IP — экспериментальный read-only tunnel adapter
- Добавлена закреплённая зависимость `knxide = 0.1.0`.
- `KnxIpReadOnlyClient`: KNXnet/IP tunnelling connection с заданными gateway/local bind, group address parsing, DPT parsing и GroupValue_Read.
- Поддержка typed DPT values из используемой библиотеки; bool/numeric/string значения сохраняются типизированно.
- В адаптере нет GroupValue_Write, device restart или иных команд управления.
- Этот этап использует tunnelling; KNX routing, ETS project import и commissioning workflow не включены.

## IPC и Core integration
- DEV216 реализовал Python reference codec и Rust framing/envelope validation.
- DEV217 пока добавляет протокольные Rust client kernels, но **ещё не соединяет их с Python Driver Manager или Point Runtime через worker process**.
- Нужны worker supervisor, handshake, protocol command dispatch, sample event mapping и Core-side ownership/generation/quality checks. Не заявлять интеграцию в рабочую SCADA до завершения этих пунктов.

## Тесты и проверка
- Добавлены Rust unit tests на BACnet value mapping (включая non-finite), KNX group address parsing и DPT typed value mapping.
- В этом рабочем окружении Cargo/Rust toolchain отсутствует. Локальный cargo check/test не запускался.
- Не подтверждены CI, реальные BACnet/KNX устройства, BACnet segmentation/RPM interoperability и KNX gateway reconnect under field faults.
- Текущая ветка PR #6 не имеет CI run для DEV216/DEV217 commits. Предыдущий CI run 45949467168 относится к старому исходному commit; он не является подтверждением этих изменений.

## Следующий шаг
DEV218 — Rust worker executable + Python process supervisor по IPC v1; затем protocol-specific read commands для Modbus, BACnet/IP и KNXnet/IP, общий Core validation/publish path и fault-injection tests.
