from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health
from app.core.config import settings
from app.core.db import engine
from app.core.logging import RequestLoggingMiddleware, configure_logging
from app.modules.awareness import routes as awareness_routes
from app.modules.clinics import routes as clinics_routes
from app.modules.guidance import routes as guidance_routes
from app.modules.risk import routes as risk_routes

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: nothing yet (tables/migrations handled separately).
    yield
    # Shutdown: release the DB connection pool cleanly.
    await engine.dispose()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Added last so it is outermost and times the full request.
app.add_middleware(RequestLoggingMiddleware)

app.include_router(health.router)
app.include_router(awareness_routes.router)
app.include_router(clinics_routes.router)
app.include_router(risk_routes.router)
app.include_router(guidance_routes.router)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": settings.app_name, "status": "ok"}
