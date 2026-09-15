from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1 import admin, auth, catalog, dashboard, datasets
from app.config import settings

app = FastAPI(
    title="OmniSure API",
    description="AI insurtech platform — Phase 1 foundation (auth, dashboards, catalog).",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENV == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(catalog.router)
app.include_router(dashboard.router)
app.include_router(admin.router)
app.include_router(datasets.router)

# Serve the frontend (static HTML/CSS/JS built from the Stitch design).
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")


@app.get("/api/v1/health", tags=["health"])
def health():
    return {"status": "ok", "env": settings.ENV, "demo_mode": settings.DEMO_MODE}
