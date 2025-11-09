from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .api.rest import router as rest_router
from .config import get_settings
from .graphql.schema import get_graphql_router
from .logging import setup_logging


def create_app() -> FastAPI:
    setup_logging()
    settings = get_settings()

    app = FastAPI(title="FinWise Agents Service", version="0.1.0")

    @app.get("/health", tags=["health"])
    async def health() -> JSONResponse:
        status = {
            "status": "ok",
            "service": "agents-service",
            "version": app.version,
        }
        return JSONResponse(status)

    app.include_router(rest_router)
    app.include_router(get_graphql_router(), prefix="/graphql")

    return app


app = create_app()


