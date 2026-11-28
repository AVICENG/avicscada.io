# AVIC Core — журнал сборки DEV260

Дата CI: 28.11.2026  
GitHub Actions run: `46122912454`  
HEAD: `c603a1568a4a3104ac6726afdbd0f38d5a9d23cb`  
PR: [#11](https://github.com/AVICENG/avicscada.io/pull/11)

## Python full regression

| ОС | Python | Passed | Skipped | Failed |
|---|---:|---:|---:|---:|
| Ubuntu | 3.11 | 31 524 | 8 | 0 |
| Ubuntu | 3.12 | 31 524 | 8 | 0 |
| Ubuntu | 3.13 | 31 524 | 8 | 0 |
| Windows | 3.11 | 31 521 | 11 | 0 |
| Windows | 3.12 | 31 521 | 11 | 0 |
| Windows | 3.13 | 31 521 | 11 | 0 |

Windows 11 skipped: seven tests require the C Worker binary supplied by the separate native C job; one Linux PTY round-trip is covered by the Linux native C job; two Modbus RTU tests require POSIX flock/symlink semantics; one SecretStore test requires POSIX permissions. All six full-suite jobs passed with zero failures. Windows jobs report 448 warnings.

## Native CI jobs

**Passed:** Modbus C Worker Windows UCRT64 and Ubuntu; Paho MQTT C native probe Windows and Ubuntu; OPC UA open62541 native probe Windows and Ubuntu; Rust Communication Engine Windows and Ubuntu; Siemens S7 C-only policy Windows and Ubuntu; BACnet Stack POC Windows build/codec.

**Failed:** BACnet Stack POC / Ubuntu simulator integration. The server executable was built and launched, route interface name and IPv4 were resolved, but ReadProperty timed out for Device Instance 123. This is a real integration failure. The CI runner's broadcast behavior is a plausible cause, not a proven root cause. DEV261 therefore isolates direct unicast ReadProperty from broadcast discovery.

## Rust vs Python synthetic benchmark

Workload: Modbus TCP loopback, 100 devices × 100 points, 100 000 updates, 16 parallel operations, zero errors.

| Metric | Python | Rust |
|---|---:|---:|
| Throughput | ~183 000 updates/s | ~2 310 000 updates/s |
| p50 | 8.042 ms | 0.284 ms |
| p95 | 10.879 ms | 3.761 ms |

Observed ~12.7× throughput and ~28× lower p50. This is a synthetic loopback benchmark, not a real-network or hardware performance guarantee.

## Scope / limitations

- DEV260 adds a bounded asynchronous event queue (256), separate from correlated responses, with common identity/generation/sequence validation.
- `drain_events(max_items)` is available. Event overflow policy is drop-newest only for explicitly replaceable sample/telemetry; critical event overflow fences the worker.
- DEV260 does not yet publish unsolicited events to Point Runtime.
- Paho and OPC UA jobs are native probes, not complete AVIC production workers.
- BACnet simulator ACK/Error integration remains failed/unverified; hardware acceptance has not been performed.
- No driver status promotion is justified by DEV260 alone.

## DEV261 / DEV262 preparation

After DEV260 completed, follow-up changes were prepared separately: direct unicast BACnet ReadProperty mode and simulator script/test; Paho callback topic-name ownership cleanup; expanded IPC event kinds and bounded `next_event(timeout_seconds)` API. These changes are not part of DEV260 HEAD and must be compiled, tested and reviewed in a new CI run before being considered implemented.
