# Siemens S7 — third-party license inventory

Дата аудита: 27.11.2026

## Pinned upstreams

- python-snap7 3.6.0 — https://github.com/gijzelaerr/python-snap7
  - audited commit: `2aca5459cba0ce21d65f255882bcd562d86392f1`
  - license: MIT; source file: `python-snap7-MIT.txt`
- s7commplus 0.7.0 — https://github.com/gijzelaerr/s7commplus
  - audited commit: `5295810835095d90b103430e809a47b63a0b3438`
  - package license: MIT; source file: `s7commplus-MIT.txt`
  - bundled preset dictionaries: LGPL-3.0-or-later, notice: `S7CommPlusDriver-zlib-dictionaries-NOTICE.txt`; full LGPL-3 text preserved in `S7CommPlusDriver-LICENSE.txt`
  - V1 SessionKey helper: MIT notice in `HarpoS7-MIT.txt`
- S7.Net Plus — https://github.com/S7NetPlus/s7netplus
  - audited commit: `ab6308eacd553f571e4792c6ca31bbbfde5c133c`
  - license: MIT; source file: `S7NetPlus-MIT.txt`

## AVIC dependency policy

The Core default installation does not install these protocol libraries. They are exposed as an optional extra `.[s7]` with bounded version ranges. The actual worker implementation must pin a release, generate an SBOM, preserve notices and run the license audit before packaging.

Do not silently upgrade `s7commplus`: it is classified Beta upstream and hardware compatibility depends on CPU model, firmware, protection settings and TIA project configuration. Upstream explicitly disclaims Siemens affiliation/support.

Classic PUT/GET access on S7-1200/1500 is disabled by default and unauthenticated. AVIC must not enable it or weaken PLC protection automatically.

This inventory is a software engineering audit, not legal advice. Recheck upstream licenses and dependency metadata for every release.
