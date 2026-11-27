# Siemens S7 — DEV239 historical implementation (retired)

Дата пересмотра: 27.11.2026

> **Внимание:** документ описывает историческую Rust-реализацию DEV239. Этот путь больше не является частью целевой реализации AVIC и удалён из Rust Communication Engine в DEV247. Не использовать приведённый ниже старый IPC payload и не подключать S7 через Rust/Python fallback.

## Текущее решение

- Siemens S7 — только C Worker.
- Каталог драйверов держит S7 в состоянии PLANNED.
- Rust s7.rs, зависимость tokio-s7 и ветка s7comm в avic_driver_worker удалены.
- Python Snap7 / S7CommPlus не входят в runtime dependencies.
- Snap7 (C++ core) и libnodave (pure C, beta warning) остаются кандидатами для технического аудита, но ни один пока не принят.
- Реального C Worker и аппаратной приёмки ещё нет.

Актуальная спецификация и лицензионная оценка:
docs/architecture/SIEMENS_S7_DRIVER_SELECTION_AND_SECURITY_RU.md.

## Историческая справка

В DEV239 существовал read-only S7comm путь через Rust crate tokio-s7, поддерживавший ограниченное чтение стандартных DB по ISO-on-TCP. Его проверки не подтверждают готовность C реализации и не должны использоваться как критерий текущей готовности.

## Миграция

Старый путь отключён и удалён из активного Rust Worker. Общий IPC contract, sequence/generation fencing и supervisor сохраняются для других протоколов. S7 вернётся в runtime только после выбора проверенного C engine, реализации C Worker, simulator tests, Windows/Linux CI и аппаратной приёмки.
