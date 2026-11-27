# DEV207 — Rust Communication Engine: первый Modbus TCP pilot

Статус: **Rust pilot реализован; unit tests и первый smoke benchmark прошли на Windows/Linux. Полная матрица AVIC Python тестов выявила регрессии; 10k benchmark profile ожидает повторного CI.** Не считать Rust-движок production-ready до завершения полного CI, отказных серий и аппаратной приёмки.

## Что реализовано

Добавлен независимый Rust crate rust/avic-communication-engine без сторонних crate-зависимостей:

- read-only Modbus TCP Function Code 03;
- проверка MBAP transaction ID / protocol ID / unit ID / length;
- ограничение FC03 на 1..125 регистров;
- TCP read/write timeouts;
- проверка function code, byte count и длины ответа;
- bounded по числу потоков benchmark workers;
- метрики throughput, ошибок и p50/p95/p99 времени транзакции;
- unit tests границ аргументов.

В Rust pilot намеренно отсутствуют write functions, управление оборудованием, конфигурация AVIC, лицензирование, RBAC, Audit и прямая запись в Point Runtime. Это transport pilot, не готовый production Driver.

## Modbus: Python vs Rust

Скрипт tools/modbus_load_compare.py поднимает один локальный synthetic Modbus TCP FC03 server и последовательно запускает существующий Python ModbusTcpPointAdapter + ModbusTcpClient и Rust avic-modbus-bench. Одинаковы число устройств, регистров на устройство, циклы, конкурентность и loopback server. Оба варианта сохраняют обновлённые значения в локальном point-value buffer/runtime stub.

Команда 10k profile:

```powershell
python tools/modbus_load_compare.py --devices 100 --points-per-device 100 --cycles 10 --concurrency 16
```

Это 10 000 точек (100 устройств × 100 регистров), 10 циклов, до 16 параллельных workers. Один групповой FC03 read на устройство за цикл; максимум 125 регистров в группе. CI запускает этот профиль на Windows и Linux.

Первый smoke прогон меньшего масштаба (4 устройства × 20 точек, 2 цикла, concurrency 2) прошёл на обеих ОС:

| ОС | Python updates/s | Rust updates/s | Ошибки Python/Rust |
|---|---:|---:|---:|
| Ubuntu | 31 071.29 | 104 695.94 | 0 / 0 |
| Windows | 5 292.11 | 30 005.81 | 0 / 0 |

Smoke содержит всего 160 обновлений на движок и слишком мал для выводов о промышленной производительности. Значения показывают только успешность сравнимого пути на loopback и служат проверкой стенда, не обещанием ускорения. Более показательный 10k profile запущен в следующем CI.

## BACnet: Python baseline

Скрипт tools/bacnet_load_baseline.py измеряет существующий Python BACnet/IP adapter на локальном UDP loopback с синтетическим ReadProperty peer. Он создаёт 10 000 bindings и выполняет по одному подтверждённому ReadProperty Present_Value на каждую точку:

```powershell
python tools/bacnet_load_baseline.py --points 10000
```

Текущий BACnet client сериализует операции через lock и не использует RPM/COV. CI запускает Python baseline на Windows и Linux. Это исходный профиль Python, а не Rust parity.

Rust BACnet не включён в первый pilot: до реализации требуется выбрать и проверить стек, APDU/NPDU, segmentation/reassembly, RPM, COV subscribe/renew/cancel, BBMD/Foreign Device, vendor interoperability и лицензии зависимостей. Нельзя выдавать сравнение Rust BACnet, пока эквивалентный Rust transport не реализован и не проверен тем же simulator/hardware workload.

## Что тесты не доказывают

- Loopback benchmark не измеряет пропускную способность реальной Ethernet-сети или слабых контроллеров.
- Он не моделирует packet loss, задержки сети, внутренние очереди PLC, восстановление, COV, Historian и FBD.
- Он не подтверждает production capacity на Windows/Linux hardware.
- Один прогон не является основанием для миграции. Нужны повторные серии, нагрузка/отказы и hardware acceptance.

## CI и найденные проблемы

Rust cargo test и same-simulator smoke comparison завершились успешно на Ubuntu и Windows. В полной Python матрице на Ubuntu были выявлены старые регрессионные тесты, не соответствующие усиленным station/driver ownership проверкам, а также несколько fixture defects. Исправлены тестовые setup/expectations: тестовые устройства теперь имеют реальные station-owned DriverInstance, cross-station FBD test ожидает отказ на этапе добавления точки, history API тест использует существующую станцию и точку, а license Gate fixture реализует новый feature check. Повторный CI на финальном HEAD должен подтвердить исправления на всех 6 Python jobs.

Workflow .github/workflows/avic-core-ci.yml содержит Rust matrix на Ubuntu/Windows, 10k Modbus Python/Rust benchmark и 10k BACnet Python baseline.

Окончательный статус будет обновлён после завершения CI. Физическая проверка на реальных Modbus/BACnet контроллерах ещё не выполнена.
