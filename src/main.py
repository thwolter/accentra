import logging

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from core import configure_logging, get_settings, init_observability
from users.api import router as identity_router

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    configure_logging()
    init_observability()
    settings = get_settings()

    application = FastAPI(title=settings.app_name, version=settings.version)

    cors_origins = list(settings.cors_allow_origins)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    logger.info(f'CORS origins: {cors_origins}')

    @application.get('/healthz')
    async def healthz():  # pragma: no cover - trivial endpoint
        return {'status': 'ok'}

    @application.get('/readyz')
    async def readyz():  # pragma: no cover - trivial endpoint
        return {'status': 'ready'}

    application.include_router(identity_router)
    return application


app = create_app()
