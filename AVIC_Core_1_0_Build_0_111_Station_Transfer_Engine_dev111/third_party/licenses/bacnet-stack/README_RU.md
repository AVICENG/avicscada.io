# Steve Karg BACnet Stack — third-party notices

- Upstream: https://github.com/bacnet-stack/bacnet-stack
- Pinned commit used by the DEV225 CMake probe: `45f9831996f1a17504a790da91a4113f2974595c`
- Upstream license policy: `license/readme.txt` at the pinned revision.
- License texts preserved alongside this notice: GPL-2.0, GCC-exception-2.0, MIT and Apache-2.0.

The upstream README states that the core uses GPL with the GCC exception and that the BACnet library may be linked with proprietary code without making the proprietary application GPL. Modifications to distributed GPL-covered upstream files remain subject to the upstream GPL terms. The repository also contains MIT and Apache-2.0 files.

**Do not treat the entire repository as one license.** Before shipping any AVIC binary, generate a file-level SPDX/SBOM for the exact CMake target and selected platform sources, preserve all applicable notices, and review changes to upstream sources. The current probe does not modify upstream sources and is not a production BACnet Worker.

The selected upstream revision is pinned in `rust/avic-communication-engine/bacnet-stack-probe/CMakeLists.txt`. Do not silently move the pin; update the pin and re-run the license/source-set audit as a separate reviewed change.
