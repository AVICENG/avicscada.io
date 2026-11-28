# Журнал сборки и проверок DEV263

Дата CI: 28.11.2026  
Commit: `cf1863b5198c24b274421f7207d8b45e1ff2d2d7`  
PR: #11 — текущая ветка C protocol workers.

## Цель DEV263

Исправить BACnet/IP simulator gate: базовый upstream `bacserv` не гарантирует Analog Input 0, поэтому положительный ReadProperty перенесён на гарантированно существующий Device Object (type 8, instance 123), свойство Object_Name (77). Отрицательный запрос выполняется к тому же объекту для неподдерживаемого property 511.

## Подтверждённые результаты CI run 46125903521

### BACnet Stack

- Ubuntu: build + codec tests — **success**.
- Windows: build + codec tests — **success**.
- Ubuntu upstream `bacserv` integration — **success**.
- Положительный ReadProperty: ACK получен для Device:123 / Object_Name:77; возвращено имя `AVIC-CI-BACnet-Simulator`.
- Отрицательный ReadProperty: BACnet Error получен; класс 2, код 32.
- Клиент использовал прямой unicast endpoint. Этот тест **не подтверждает** broadcast Who-Is/I-Am discovery, работу через BBMD или реальное оборудование.

### Другие native jobs

- Paho MQTT C native probe: Ubuntu — **success**; Windows — **success**.
- libmodbus C Worker: Ubuntu — **success**; Windows UCRT64 — **success**.
- OPC UA open62541 native probe: Ubuntu — **success**; Windows UCRT64 — **success**.
- Rust Communication Engine: Ubuntu — **success**; Windows — **success**.
- Siemens S7 C-only policy: все запущенные Ubuntu/Windows jobs — **success**.

Paho результаты подтверждают только нативную сборку и lifecycle self-test probe. Они не подтверждают полноценный MQTT AVIC C Worker или доставку MQTT сообщений в Point Runtime.

### Python regression matrix — результаты на момент записи

| Python | Ubuntu | Windows |
|---|---:|---:|
| 3.11 | 31 533 passed, 8 skipped | Выполнение ещё шло |
| 3.12 | 31 533 passed, 8 skipped | Выполнение ещё шло |
| 3.13 | 31 533 passed, 8 skipped | 31 530 passed, 11 skipped |

Все завершённые Python jobs завершились успешно, без failed tests. Windows пропуски включают платформозависимые проверки POSIX и проверки, требующие отдельного native worker/PTY окружения; причины сверять по JUnit/pytest summary конкретного job.

**Важно:** на момент создания этого журнала workflow run оставался `in_progress`: Windows Python 3.11 и 3.12 jobs не завершились. Поэтому DEV263 нельзя считать полностью принятым до их итогов и общего workflow conclusion. После завершения CI этот журнал должен быть дополнен точными Windows результатами и итогом run.

## Ограничения, остающиеся открытыми

1. BACnet broadcast discovery (Who-Is/I-Am) и BBMD traversal не подтверждены этим simulator gate.
2. BACnet реальное оборудование, конкретные модели и firmware не проверялись.
3. MQTT Paho пока является native probe, не полноценным AVIC Worker.
4. Paho probe не проверяет end-to-end subscription, reconnect, QoS, TLS или Point Runtime.
5. Никакой драйвер не повышается до 🟩/🟦 на основании одних сборок или probe tests.

## Решение по статусам

Статусы протоколов не меняются этим журналом. BACnet/IP остаётся 🟨: прямой ReadProperty ACK/Error gate подтверждён, но полный runtime/discovery и hardware gates открыты. MQTT остаётся 🟧 до реализации C Worker, AVIC IPC event delivery и тестов с брокером.
