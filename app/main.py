import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import (
    ai,
    auth,
    branches,
    campaigns,
    customers,
    dashboard,
    delivery,
    menu,
    orders,
    payments,
    platform,
    restaurants,
    reviews,
    settings,
    users,
)
from app.core.config import get_settings
from app.database.sqlite import init_db
from app.utils.data_bootstrap import bootstrap_json_data
from app.middleware.error_middleware import generic_exception_handler, http_exception_handler
from app.middleware.logging_middleware import LoggingMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings_config = get_settings()
    if settings_config.is_production:
        bootstrap_json_data()
    init_db()
    yield


def create_app() -> FastAPI:
    settings_config = get_settings()
    docs_enabled = settings_config.debug and not settings_config.is_production
    application = FastAPI(
        title=settings_config.app_name,
        description="AI Restaurant Direct Ordering Platform API",
        version="2.0.0",
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings_config.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(LoggingMiddleware)

    application.add_exception_handler(StarletteHTTPException, http_exception_handler)
    application.add_exception_handler(Exception, generic_exception_handler)

    application.include_router(auth.router)
    application.include_router(restaurants.router)
    application.include_router(branches.router)
    application.include_router(menu.router)
    application.include_router(orders.router)
    application.include_router(customers.router)
    application.include_router(delivery.router)
    application.include_router(campaigns.router)
    application.include_router(reviews.router)
    application.include_router(users.router)
    application.include_router(payments.router)
    application.include_router(dashboard.router)
    application.include_router(platform.router)
    application.include_router(settings.router)
    application.include_router(ai.router)

    @application.get("/api/health")
    def health_check():
        return {
            "status": "ok",
            "app": settings_config.app_name,
            "env": settings_config.app_env,
            "api_version": "1.3.0",
            "features": ["delivery_accept", "delivery_order_details", "live_location_tracking"],
        }

    return application


app = create_app()
