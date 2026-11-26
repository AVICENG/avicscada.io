"""Start the AVIC Engineering Workbench with ``python -m avic_core.ui``."""
from __future__ import annotations

import argparse
from threading import Timer


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
    config = uvicorn.Config(app, host=args.host, port=args.port, reload=args.reload)
    server = uvicorn.Server(config)

    def request_process_shutdown() -> None:
        # Let the HTTP response leave the socket before asking Uvicorn to perform
        # its normal graceful shutdown and run the ASGI lifespan cleanup.
        Timer(0.5, lambda: setattr(server, "should_exit", True)).start()

    app.state.process_shutdown_callback = request_process_shutdown
    server.run()


if __name__ == "__main__":
    main()
