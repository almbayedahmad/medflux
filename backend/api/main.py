from fastapi import FastAPI
from core.logging import configure_logging
from core.monitoring import init_monitoring
from backend.api.v1 import api_v1
from backend.api.middleware.request_log import request_log_middleware
from core.logging.uncaught import install_uncaught_hook


def create_app() -> FastAPI:
    configure_logging(force=True)
    init_monitoring()
    app = FastAPI(title="MedFlux API", version="v1")
    app.include_router(api_v1, prefix="/api/v1")
    app.middleware("http")(request_log_middleware)
    install_uncaught_hook()
    # Optional Prometheus metrics endpoint
    try:
        from prometheus_client import CONTENT_TYPE_LATEST, generate_latest  # type: ignore
        from fastapi.responses import Response

        @app.get("/metrics")
        def metrics_endpoint() -> Response:  # type: ignore[override]
            return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
    except Exception:  # pragma: no cover
        pass
    return app


app = create_app()
