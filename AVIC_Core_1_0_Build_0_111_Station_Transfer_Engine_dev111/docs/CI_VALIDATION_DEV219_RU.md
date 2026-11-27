# DEV219 CI validation branch

This stacked validation branch is based on `architecture/rust-communication-engine` and contains the complete DEV216–DEV219 working tree as its base.

Purpose:
- trigger the repository CI matrix against the current Rust worker, BACnet/IP, KNXnet/IP and Python Driver Manager integration;
- validate Cargo compilation/tests on Windows and Linux;
- validate the Python suite, including the new IPC supervisor, Rust Point Runtime adapter and Driver Manager tests.

No production-readiness claim is made until the workflow completes successfully. BACnet-RS upstream limitations, per-read connection overhead and lack of hardware acceptance remain open.
