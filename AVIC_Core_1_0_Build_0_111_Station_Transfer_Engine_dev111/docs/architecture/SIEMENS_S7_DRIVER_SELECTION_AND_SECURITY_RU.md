# Siemens S7 — open-source driver selection and AVIC integration plan

Дата проверки: 27.11.2026

## Краткое решение

**Да, Siemens S7 можно подключать открытыми библиотеками. Для AVIC выбираем два независимых protocol engines, потому что классический S7comm и S7CommPlus — разные протоколы.**

1. **S7-300 / S7-400 и legacy PUT/GET path:** `python-snap7 3.6.0` — основной классический клиент. Pure Python, MIT, Windows/Linux, stable.
2. **S7-1200 / S7-1500:** `s7commplus 0.7.0` — отдельный современный клиент для S7CommPlus V1/V2/TLS/V3, symbolic browsing, optimized DB access, subscriptions and alarms. Pure Python, MIT package, но статус upstream в pyproject — Beta. Это основной кандидат для современного S7, пока не пройдены AVIC acceptance gates.
3. **S7.Net Plus:** MIT .NET library, поддерживает ряд семейств S7, но остаётся дополнительным compatibility candidate; не заменяет S7CommPlus и не является основным AVIC engine.
4. **Rust S7CommPlus implementation:** изучить отдельно как будущую альтернативу; не выбирать production engine только по языку. Требуются независимая лицензия/source audit и hardware acceptance на реальных S7-1200/1500.

## Важные отличия и безопасность

### python-snap7 3.6.0 — classic S7

- Upstream: https://github.com/gijzelaerr/python-snap7
- Pinned upstream commit для аудита: `2aca5459cba0ce21d65f255882bcd562d86392f1`.
- Package version: `3.6.0`; pure Python rewrite from version 3.0; no native Snap7 shared library needed.
- License: MIT.
- S7-300/S7-400: classic S7 protocol.
- S7-1200/S7-1500: only classic compatibility path with PUT/GET enabled in TIA Portal; cannot access optimized DBs; PUT/GET is unauthenticated and disabled by default. The more secure default is to keep it disabled.
- S7-1500R/H classic fallback is not supported in the current support matrix.

**AVIC policy:** never enable PUT/GET or change CPU protection settings automatically. Show a clear warning and require an administrator to deliberately configure this compatibility mode. Prefer S7CommPlus or OPC UA when available.

### s7commplus 0.7.0 — modern S7CommPlus

- Upstream: https://github.com/gijzelaerr/s7commplus
- Pinned upstream commit for audit: `5295810835095d90b103430e809a47b63a0b3438`.
- Package version: `0.7.0`, published 19 Nov 2026.
- Protocols: S7CommPlus V1, V2 with TLS, V3 framing.
- Features: sync/async clients, raw DB and controller-area access, symbolic browsing and optimized DBs, subscriptions, alarm snapshots/events, server emulator.
- Package license: MIT. The 19 bundled zlib preset dictionaries are extracted from S7CommPlusDriver and remain LGPL-3.0-or-later; upstream includes a dedicated notice. HarpoS7-derived V1 SessionKey helper carries its own MIT notice.
- Upstream package is classified Beta, not production/stable. Unofficial implementation, not Siemens-supported.
- Hardware validation in upstream docs includes S7-1200 CPU 1212C FW 4.2.2 (legacy SessionKey), CPU 1215C FW 4.2/4.3 and TLS on FW 4.1/4.5/4.7.3; S7-1500 CPU 1512SP FW 2.6, CPU 1512C FW 2.5 read-only, and TLS on FW 2.9.7/2.9.8. A 1515-2 PN FW 2.9 report is not working. This is not universal S7-1500 compatibility.
- Upstream docs warn that some async handshake changes have not yet been retested on hardware. Start AVIC with synchronous client unless async hardware acceptance is complete.
- TLS must be explicitly required and certificate-verified for secure deployments. Do not use opportunistic `use_tls="auto"` without certificate verification where active network attackers matter. Do not downgrade to plaintext after a TLS/certificate/authentication failure.

**AVIC policy:** modern S7CommPlus Worker is read-only initially. TLS certificate verification is fail-closed. Credentials and keys go through SecretStore, never DriverInstance config, IPC diagnostics, logs, exports or test artifacts. Writes, block upload/download, CPU mode changes and administrative actions remain unavailable until a separate Command Gateway / RBAC / audit acceptance.

## Why not use S7.Net Plus as the primary engine

- Upstream: https://github.com/S7NetPlus/s7netplus
- License: MIT.
- C#/.NET library, documented compatibility includes S7-200/300/400/1200/1500.
- Useful as a secondary option for a .NET-native deployment, but its public README does not claim S7CommPlus V2/V3 TLS, secure certificate lifecycle, optimized symbolic access, or the broader newer feature set. Do not treat its PLC-family list as proof of secure S7-1500 support.

## AVIC worker architecture

- Two protocol IDs: `siemens-s7-classic` and `siemens-s7commplus`; never hide protocol choice behind a vague `siemens-s7` mode.
- Separate, supervised worker process per DriverInstance, versioned AVIC Driver IPC, scope + generation + sequence fencing, bounded queues and restart.
- Core owns canonical point types, scaling, quality, timestamps, point licensing, history, alarms, FBD/HMI and Command Gateway.
- Worker returns protocol values and diagnostics only. Core validates each binding and publishes via Point Runtime.
- No protocol worker may publish directly into HMI/FBD or bypass Command Gateway.
- S7 DB/byte/bit offsets and symbolic tag names are distinct binding types; validate DB number, area, offset, type, length, array/struct shape and access rights before polling.
- Batch adjacent compatible reads within PLC PDU limits; never read across unconfigured gaps by default.
- Keep CPU state, connection state, protocol version, negotiated TLS, certificate identity, protection level and per-tag quality as separate diagnostics.
- Reconnect with bounded exponential backoff and jitter; invalidate stale samples and never report stale values as GOOD.

## Implementation sequence

1. Add optional dependency group for both open-source libraries; pin supported version ranges and produce SBOM/notices.
2. Build classic S7 worker and simulator tests for S7-300/400-style DB/area access.
3. Build S7CommPlus worker with synchronous client first; use upstream server emulator for protocol contract tests.
4. Add read-only symbolic browse, optimized DB tag read, DB raw read, multi-tag batches and subscriptions as separate capabilities.
5. Add Windows and Linux CI, reconnect/timeout/invalid-packet/certificate tests and no-secret-in-logs tests.
6. Hardware acceptance: at least one S7-1200 and one S7-1500 with exact order number, firmware, TIA project security configuration and test log. Test legacy SessionKey and TLS paths separately.
7. Only after read-only acceptance consider write commands through AVIC Command Gateway. Never write directly from a driver.

## Acceptance checklist (not yet passed)

- [ ] Dependency/license inventory generated for pinned artifacts, including LGPL zlib dictionary notice.
- [ ] Windows/Linux worker packaging and process isolation.
- [ ] Classic S7 simulator contract tests.
- [ ] S7CommPlus emulator contract tests.
- [ ] TLS CA validation, invalid certificate, hostname/fingerprint mismatch, forced TLS failure; no plaintext fallback.
- [ ] PLC access denied, password rejected, expired/revoked certificate, reconnect and generation-fencing tests.
- [ ] Batch read boundaries, optimized DB symbolic reads, arrays/UDTs and data type decoding.
- [ ] Hardware test on exact S7-1200 model/firmware.
- [ ] Hardware test on exact S7-1500 model/firmware.
- [ ] AVIC Command Gateway write authorization tests (separate milestone; writes disabled until passed).

**Current status:** selection/audit only. No Siemens S7 driver is implemented or hardware-accepted in AVIC yet.
