from __future__ import annotations

import argparse
import json
from avic_core.application import CoreApplication


def main() -> int:
    parser = argparse.ArgumentParser(description="AVIC Core 1.0 local foundation")
    parser.add_argument("--data-dir", required=True, help="Постоянный каталог данных AVIC Core")
    parser.add_argument("command", choices=("init", "health"), nargs="?", default="health")
    args = parser.parse_args()
    with CoreApplication(args.data_dir) as core:
        if args.command == "init":
            print(json.dumps({"status": "initialized", "data_dir": str(core.paths.root)}, ensure_ascii=False))
            return 0
        report = core.health_report()
        print(json.dumps({"status": report.status, "checked_at": report.checked_at,
                          "checks": [item.__dict__ for item in report.checks]}, ensure_ascii=False, indent=2))
        return 0 if report.status == "OK" else 2


if __name__ == "__main__":
    raise SystemExit(main())
