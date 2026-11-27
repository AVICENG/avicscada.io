# AVIC Core — журнал сборки DEV208

Дата: 27.11.2026

## Цель
Начать внедрение Rust engines без переписывания Python AVIC Core. Python остаётся системным владельцем инженерной модели и прикладных сервисов; Rust выносит высоконагруженный протокольный I/O в отдельный процесс.

## Реализовано
- Добавлен crate `rust/communication-engine` (Rust 2021) с JSON Lines IPC через stdin/stdout.
- Команды IPC: `health`, `modbus_read`, `shutdown`; корреляция ответов по request_id.
- Rust Modbus TCP transport: read-only FC 1/2/3/4; проверки MBAP transaction ID, protocol ID, length, unit ID, function, byte count; Modbus exception response; bounded TCP connect/read/write timeout.
- Python `RustModbusTcpClient` supervises executable, validates handshake/capabilities/response IDs and payload shape, kills stalled/broken process, exposes read interface compatible with existing Modbus adapter. Modbus adapter now closes the persistent engine process on Driver Manager stop and includes engine diagnostics.
- Driver Manager supports explicit `engine_backend=python|rust`; Rust requires `engine_binary`. No silent fallback.
- Existing Modbus adapter retains decoding, scale/offset, station ownership checks and Point Runtime publication. Diagnostics report backend.
- Python test fixtures for Modbus/BACnet adapter now retrieve their persisted DriverInstance IDs instead of referencing undefined variables/fake owners.
- GitHub Actions adds Rust cargo test/build on Ubuntu and Windows.

## Safety boundaries
- Rust engine has no Modbus write functions; FC 5/6/15/16/22/23 are not implemented.
- Rust process does not access Core database, licenses, secrets or Point Runtime.
- BACnet remains Python READ-ONLY; no Rust BACnet implementation is claimed.
- Python remains explicitly selectable; failed Rust startup does not silently switch backend.

## CI finding and correction
- First combined CI exposed setuptools flat-layout auto-discovery: the new top-level `rust/` source tree was incorrectly treated as a second Python package (`Multiple top-level packages discovered: ['rust', 'avic_core']`).
- `pyproject.toml` now explicitly discovers only `avic_core*` Python packages and excludes `rust*`/`tests*`; Rust sources remain part of the repository but are not installed as Python packages.
- Rust target build output is ignored via `rust/communication-engine/.gitignore`.

## Verification
- Python test suite after DEV208: pending the next CI run after package-discovery correction.
- Rust `cargo test` and release build: pending GitHub Actions; local Rust toolchain unavailable in this environment.
- Workflow run `45952214681`: pending at the time of this log; global repository concurrency may delay job creation.
- No hardware Modbus/BACnet acceptance claimed.
- No 1k/10k performance result claimed. Earlier small smoke-test speedups are not treated as production benchmark evidence.

## Next stages
1. Green Linux/Windows Rust + Python CI and fix all regressions.
2. Add deterministic Python-vs-Rust functional parity, 1k/10k load, timeout, malformed-peer, disconnect/reconnect, process-crash and soak tests.
3. Run real Modbus TCP hardware acceptance before changing any default backend.
4. Only then design BACnet/IP Rust transport with RPM, COV, segmentation, BBMD and vendor/device interoperability tests. Keep Python BACnet as baseline.

## Readiness
DEV208 is an integration pilot. Rust Modbus is NOT production-ready until full CI, performance/fault parity and real controller acceptance are complete.

## Дополнительная стратегия из ноутбучного обсуждения 27.11.2026

Rust-кандидаты: Communication Engine/драйверы, Point Runtime, FBD Engine, Historian, Alarm Engine; Scheduler — отдельная оценка. Порядок: Driver SDK v1 → Load & Reliability Lab и Python baseline → Rust Modbus → Rust BACnet/IP (RPM/COV/segmentation/BBMD) → версионированная IPC граница Point Runtime → остальные кандидаты только по benchmark.

Предварительные исторические Modbus 10k данные: Ubuntu Python/Rust 45 288/47 679 точек/с; Windows Python/Rust 72 167/62 554 точек/с. Это не доказывает универсальное преимущество Rust (на Windows в том замере Python быстрее). Предварительный BACnet Python 10k: 1.67/4.54 с, ошибок 0, но длинный p99 tail. Все цифры должны быть повторены единым harness.

Performance gates: 10k базово, 50k+ расширенно, 72 часа soak; throughput, CPU/RAM, p95/p99, очереди, пропуски/задержки, reconnect и recovery. Не переводить backend по умолчанию до functional parity, отказных тестов и аппаратной приёмки.

## Python regression findings after packaging fix

В combined run 45952516103 Python dependency installation прошла на всех шести jobs. На Linux выявлены 4 тестовые регрессии:
- FBD station isolation тест ожидал отказ на этапе simulate, но реализация корректно отклоняет чужую точку раньше — при add_point_node до сохранения графа; тест перенесён на фактическую границу отказа.
- MQTT adapter fixtures использовали неопределённый driver или фиктивный driver-mqtt-test; теперь они получают сохранённый station-owned DriverInstance ID. Это также восстанавливает публикацию значения и BAD_COMMUNICATION/BAD_CONFIGURATION quality transitions.
Полный matrix для текущего исправления ожидает следующего CI; статус не объявляется успешным.
