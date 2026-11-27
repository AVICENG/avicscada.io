# Журнал DEV216 — Python reference IPC codec и Rust framing

Дата: 27.11.2026

## Цель
Начать практическую реализацию Driver SDK v1, зафиксированного в DEV215. Это общий wire format для Rust worker и Python Supervisor.

## Реализовано
- Python reference codec: `avic_core/drivers/ipc.py`.
- Rust IPC framing: `rust/avic-communication-engine/src/ipc.rs`.
- 4-byte big-endian length prefix; JSON envelope; лимит 1 MiB до выделения body buffer.
- Envelope содержит contract/version, message/worker IDs, station/project/installation/driver scope, generation, sequence, UTC timestamp, correlation ID и object payload.
- Валидация версии, обязательных идентификаторов, generation, timestamp и типа payload.
- SequenceGuard: reject stale generation и duplicate/out-of-order sequence; sequence gaps сигнализируются вызывающему коду для diagnostics.
- Rust использует serde/serde_json/uuid; протокол не открывает worker доступ к Point Runtime и не заменяет Core authorization.

## Тесты добавлены
- Python: round trip, EOF/truncated header/body, oversized length, unknown contract, non-UTC timestamp, schema mismatch, generation fencing и sequence gap.
- Rust: round trip, invalid contract/generation, oversized frame before body allocation, generation fencing и sequence gap.

## Честный статус
- Код добавлен, но локальный cargo toolchain в рабочем окружении недоступен; Rust compile/test не заявляется до CI.
- Python тесты также должны быть выполнены в CI.
- Ещё не реализованы: process supervisor, Windows Named Pipe / Linux UDS transport, handshake state machine, BACnet-Rust и KNX-Rust field I/O, Modbus worker IPC bridge и Point Runtime adapter.
- До этих этапов Rust-драйверы не считаются подключёнными к production SCADA.
