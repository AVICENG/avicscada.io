"""Start the AVIC Engineering Workbench with ``python -m avic_core.ui``."""
from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="AVIC Engineering Workbench")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP bind address")
    parser.add_argument("--port", type=int, default=8000, help="HTTP port")
    parser.add_argument("--data-dir", default=None, help="Persistent AVIC data directory")
    parser.add_argument("--reload", action="store_true", help="Enable development reload")
    args = parser.parse_args()

    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover - exercised in minimal installs
        raise SystemExit(
            "Для запуска Workbench установите HTTP-зависимости: "
            "python -m pip install -e \".[http]\""
        ) from exc

    # Import factory only after argument parsing; do not create an app on import.
    from .app import create_ui_app

    app = create_ui_app(data_dir=args.data_dir)
    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
