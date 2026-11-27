# Журнал DEV218 — Rust worker process и Python supervisor

Дата: 27.11.2026

## Реализовано
- Добавлен бинарный target `avic-driver-worker`.
- Worker использует IPC v1 framing и envelope; первое сообщение обязательно `initialize`.
- Проверяет неизменность installation/project/station/DriverInstance/worker/generation на каждом запросе.
- Проверяет sequence; старые поколения и повторные/переупорядоченные запросы отклоняются.
- Lifecycle: initialize → configure → start → read/get_status → stop → shutdown.
- Read-only dispatch:
  - Modbus TCP FC01/02/03/04;
  - BACnet/IP discovery + object-list/common-property read;
  - KNXnet/IP tunnel + GroupValue_Read по заданному DPT.
- `write` / `write_point` всегда отклоняются.
- Worker отклоняет secret-like keys в config/read payload.
- Добавлен Python `RustDriverWorker`: только абсолютный путь к бинарному файлу, shell=False, отдельный процесс, bounded response queue, отдельное чтение stdout/stderr, проверка correlation/scope/generation/sequence, таймауты, graceful stop/shutdown и принудительное завершение при ошибках.
- Добавлены тесты Python supervisor с fake IPC worker.

## Важные ограничения
- Worker сейчас открывает протокольное соединение на каждый read request. Постоянные Modbus/BACnet/KNX sessions, batch scheduler и COV subscriptions ещё не реализованы.
- BACnet worker возвращает список объектов; полноценное сопоставление object_type/instance с AVIC bindings и проверка качества/свежести остаются в Core-side adapter.
- KNX worker использует tunnelling read; routing, ETS import и COV-like group monitoring не входят в этот этап.
- Python supervisor пока является самостоятельным компонентом и **не подключён к DriverManagerService factory или Point Runtime publish path**.
- Worker принимает команду configure, но конфигурация протокола передаётся per-read; постоянный configuration state ещё не используется.
- Никаких write/control функций не открыто.

## Проверки
- Локальный Rust toolchain отсутствует; cargo fmt/check/test не запускались.
- CI run для DEV216–DEV218 ещё не получен. Python fake-worker tests добавлены, но пока не объявляются пройденными.
- Не проводились реальные device/gateway tests.

## Следующий шаг
DEV219 — подключить RustDriverWorker к DriverManagerService как альтернативный runtime backend, добавить Rust-backed Point Adapter с fail-closed binding/quality checks, persistence/diagnostics/lifecycle ownership и fault injection. Затем заменить per-read connection creation на persistent protocol sessions и batch polling.
