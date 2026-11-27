# DEV207 — Rust Communication Engine: первый Modbus TCP pilot

Статус: **исходный код добавлен; CI и сравнительные испытания ожидают выполнения**. Не считать Rust-движок production-ready до завершения матрицы Windows/Linux и аппаратной приёмки.

## Что реализовано

Добавлен независимый Rust crate `rust/avic-communication-engine` без сторонних crate-зависимостей:

- read-only Modbus TCP Function Code 03;
- проверка параметров, MBAP transaction ID / protocol ID / unit ID / length;
- ограничение FC03 на 1..125 регистров;
- таймауты чтения/записи TCP;
- проверка function code, byte count и длины ответа;
- отдельные bounded по числу потоков benchmark workers;
- метрики throughput, ошибок и p50/p95/p99 времени одной групповой транзакции;
- unit tests для границ аргументов.

В Rust pilot намеренно отсутствуют write functions, автоматическое управление оборудованием, конфигурация AVIC, лицензирование, RBAC, Audit и прямая запись в Point Runtime. Это безопасный read-only transport benchmark, не готовый AVIC Driver.

## Сравнение Python и Rust

Скрипт: `tools/modbus_load_compare.py`.

Он поднимает один и тот же локальный synthetic Modbus TCP FC03 server, после чего последовательно запускает:
1. существующий Python `ModbusTcpPointAdapter` + `ModbusTcpClient`;
2. Rust `avic-modbus-bench`.

Оба движка получают одинаковые параметры:
- число устройств;
- регистры/точки на устройство;
- число циклов;
- максимальная конкурентность;
- один и тот же loopback TCP simulator.

Пример из корня каталога сборки:

```powershell
python tools/modbus_load_compare.py --devices 100 --points-per-device 100 --cycles 20 --concurrency 16
```

Ограничение пилота: один групповой FC03 read на устройство за цикл; до 125 регистров на группу. Для 10 000 точек пример использует 100 устройств × 100 регистров. Для большего числа точек нужно увеличить число устройств или добавить несколько групп, не нарушая лимиты протокола.

Отчёт JSON содержит updates/sec, elapsed, requests, errors и p50/p95/p99 latency. Скрипт завершится ошибкой, если один из движков потерял транзакции или число обработанных обновлений не совпало.

## Чего этот тест не доказывает

- Это loopback synthetic benchmark, а не пропускная способность реальной Ethernet-сети.
- Он не моделирует слабые CPU контроллеров, внутренние очереди PLC, packet loss, latency WAN, COV, BACnet, Historian или полный FBD workload.
- Он не подтверждает производительность на Windows/Linux production hardware.
- Результат одного прогона не является основанием для миграции драйвера. Нужны повторные серии, контроль среды, нагрузка/отказы и hardware acceptance.

## BACnet: отдельная очередь

Текущий BACnet adapter остаётся Python baseline. Rust BACnet не включён в этот первый пилот: до реализации требуется выбрать и проверить стек, APDU/NPDU, segmentation/reassembly, RPM, COV subscribe/renew/cancel, BBMD/Foreign Device, vendor interoperability и лицензионную безопасность зависимостей. Нельзя сравнивать «Rust BACnet» с Python, пока нет эквивалентной реализации и одинакового simulator/hardware workload.

Следующий шаг после успешного Modbus pilot — зафиксировать protocol-neutral Driver SDK/IPC контракт, затем начать Rust BACnet adapter. До этого BACnet benchmark фиксируется отдельно на Python, чтобы получить baseline и профиль реальных/симулированных устройств.

## CI

Workflow `.github/workflows/avic-core-ci.yml` расширен отдельной матрицей Rust pilot на Ubuntu и Windows:
- `cargo test`;
- Python installation;
- smoke comparison against same local simulator.

Окончательный статус появится только после завершения всех jobs. Код и этот документ не означают, что испытания уже прошли.
