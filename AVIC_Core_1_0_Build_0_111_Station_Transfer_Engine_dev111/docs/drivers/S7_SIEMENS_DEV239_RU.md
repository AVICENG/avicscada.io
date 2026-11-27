# Siemens S7comm — DEV239

Дата: 27.11.2026

## Назначение

Отдельный read-only драйвер Siemens SIMATIC S7 поверх ISO-on-TCP (обычно TCP/102). Реализация включена в Rust Communication Engine и вызывается через общий AVIC Driver Worker IPC. Драйвер не подменяет OPC UA и не использует Modbus.

## Поддерживаемые семейства

S7-200, S7-200 SMART, S7-300, S7-400, S7-1200 и S7-1500. PLC family, Rack/Slot (если не заданы, используются defaults семейства CPU), TCP port и timeout задаются явно. Начальный профиль чтения — абсолютная адресация байтов стандартного DB; одна операция ограничена 200 байтами.

## Worker IPC

Команда configure:
```json
{"protocol":"s7comm"}
```

Команда read (поля передаются в payload общего DriverEnvelope):
```json
{
  "protocol": "s7comm",
  "host": "192.168.1.10",
  "port": 102,
  "plc_type": "S7-1200",
  "rack": 0,
  "slot": 1,
  "db_number": 1,
  "offset": 0,
  "count": 4,
  "timeout_ms": 3000
}
```

Ответ содержит PLC family, DB number, byte offset, count и массив bytes. Сессия сохраняется в пределах Worker и освобождается на stop/shutdown. При ошибке чтения качество точки должен выставлять вызывающий Runtime по общим правилам качества связи.

## Безопасность и ограничения

- Реализовано только чтение. Worker не предоставляет S7 write API; IPC write/write_point возвращает WRITE_DISABLED.
- Для S7-1200/1500 legacy PUT/GET требует явного разрешения на стороне CPU. Доступ к optimized DB этим абсолютным legacy read path не поддерживается.
- Siemens предупреждает, что legacy PUT/GET не обеспечивает собственную защиту от сетевых атак. Использовать только в сегментированной/защищённой OT-сети с ACL/firewall; не публиковать TCP/102 в Интернет.
- S7CommPlus secure PG/HMI path, TLS, аутентификация, symbolic tag browse, SZL inventory, multi-area batching, reconnect soak и hardware acceptance ещё не завершены.
- Текущий адаптер использует tokio-s7 0.1.7 (Apache-2.0), закреплённую версию. Зависимость и реализация требуют CI review, включая Windows/Linux.
- Каталог AVIC показывает read-only transport, но это не означает аппаратную или промышленную готовность.

## Проверки

```powershell
cargo test --manifest-path rust/avic-communication-engine/Cargo.toml
cargo clippy --manifest-path rust/avic-communication-engine/Cargo.toml --all-targets -- -D warnings
```

Аппаратная проверка должна выполняться на отдельном тестовом PLC или PLCSIM/совместимом симуляторе с заранее подготовленным стандартным DB. Проверить неверные Rack/Slot, выключенный PUT/GET, отсутствующий DB, выход за границы и потерю TCP-соединения. Не выполнять запись в production PLC.
