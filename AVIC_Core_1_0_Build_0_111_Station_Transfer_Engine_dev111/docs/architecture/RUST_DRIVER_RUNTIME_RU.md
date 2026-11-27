# Rust Driver Runtime — эксплуатационная схема (DEV219)

## Единая модель

Rust и Python — это не два дерева и не два Point Runtime. В AVIC Engineering Tree остаётся одна структура:

`Project → Station → Driver Network → Device → Points`

Для каждого DriverInstance в конфигурации можно выбрать `engine: "python"` (по умолчанию) или `engine: "rust"`. Сами точки, их лицензирование, качество, источники, аудит и подписчики не меняются.

## Сборка worker

Из корня репозитория:

```powershell
cargo build --release --manifest-path rust/avic-communication-engine/Cargo.toml --bin avic-driver-worker
```

Windows бинарный файл: `rust/avic-communication-engine/target/release/avic-driver-worker.exe`.
Linux: `rust/avic-communication-engine/target/release/avic-driver-worker`.

Запуск Core с доверенным worker:

```powershell
python -m avic_core --data-dir C:\AVIC\data --rust-worker C:\AVIC\bin\avic-driver-worker.exe health
```

Можно передать путь при создании приложения:
`CoreApplication(data_dir, rust_worker_command=absolute_path)`.

## Modbus TCP

```json
{
  "engine": "rust",
  "host": "192.168.1.70",
  "port": 502,
  "unit_id": 1,
  "timeout": 2.0,
  "poll_interval_seconds": 5.0,
  "bindings": [
    {"point_id": "POINT-UUID", "function": 3, "address": 0, "count": 1, "data_type": "uint16"}
  ]
}
```

FC01/02/03/04 read only. Register decode uses AVIC byte order, word order, scale and offset.

## BACnet/IP

```json
{
  "engine": "rust",
  "network_id": "NETWORK-UUID",
  "interface_name": "Ethernet",
  "local_address": "192.168.1.10",
  "subnet_cidr": "192.168.1.0/24",
  "udp_port": 47808,
  "timeout": 3.0,
  "bindings": [
    {
      "point_id": "POINT-UUID",
      "address": ["192.168.1.70", 47808],
      "device_instance": 1234,
      "object_type": 0,
      "object_instance": 1,
      "property_id": 85,
      "scale": 1.0,
      "offset": 0.0
    }
  ]
}
```

Current Rust backend binds BACnet socket to station `local_address:udp_port`. Supported property is Present_Value (85), no array index. Object type numeric values follow BACnet standard object type enumeration.

## KNXnet/IP

```json
{
  "engine": "rust",
  "gateway_host": "192.168.1.20",
  "gateway_port": 3671,
  "local_host": "192.168.1.10",
  "local_port": 0,
  "timeout": 2.0,
  "poll_interval_seconds": 5.0,
  "bindings": [
    {"point_id": "POINT-UUID", "group_address": "1/2/3", "datapoint_type": "9.001"}
  ]
}
```

Current Rust backend performs GroupValue_Read using the commissioned group address and configured DPT. It does not send GroupValue_Write.

## BACnet quality mapping

BACnet Status_Flags order is interpreted as inAlarm, fault, overridden, outOfService:
- fault → AVIC BAD_COMMUNICATION;
- outOfService → AVIC DISABLED;
- overridden → AVIC UNCERTAIN;
- absent/malformed Status_Flags → AVIC UNCERTAIN;
- inAlarm does not by itself change data quality; Alarm Manager remains responsible for alarm semantics.

## Process transport and lifecycle

Rust worker is a child process connected through anonymous stdin/stdout pipes owned by Core; no TCP listener is exposed for IPC. The supervisor uses bounded response queue, handshake, timeout, process termination on a hung pipe, and monotonic per-DriverInstance generation. On orderly stop, owned points transition to STALE.

## Security and limitations

- Never place passwords, tokens, certificates or private keys in DriverInstance config or IPC payloads.
- The Core checks licensing before driver start. The worker is bound to one station/DriverInstance/generation; samples are validated and published only by Core Point Runtime.
- Worker IPC does not grant field-control rights. All write commands are rejected.
- Without an explicitly registered worker executable, Rust engine startup fails closed.
- The current implementation is an integration pilot, not production acceptance: protocol connections are opened per read; persistent sessions, batching, COV, KNX routing, signed worker packages, SBOM and field hardware tests remain outstanding.
- BACnet-RS upstream currently marks itself not production-ready and lacks segmentation/reassembly, alarm/event, trend-log, schedule/calendar and BACnet/SC support.
