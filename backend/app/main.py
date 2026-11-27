from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.simulation import router as simulation_router, ws_router
from app.core.config import settings
from app.database.session import Base, engine
from app.database import models  # noqa: F401

Base.metadata.create_all(bind=engine)

app = FastAPI(
    contact={"name": "Tanupriya Singh", "url": "https://github.com/tanupriyasingh07/civicverse-ai"},
    license_info={"name": "Proprietary - All Rights Reserved (Tanupriya Singh)"},
    title=settings.APP_NAME,
    description="Multi-Agent Urban Crisis Simulation & Decision Intelligence Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(simulation_router)
app.include_router(ws_router)


@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "port": settings.API_PORT,
        "database_dialect": engine.dialect.name,
    }
