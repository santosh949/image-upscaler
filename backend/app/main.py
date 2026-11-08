import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.app.core.config import settings
from backend.app.database import init_db
from backend.app.services.job_manager import job_manager
from backend.app.api.endpoints import router as api_router
from backend.app.api.projects import router as projects_router
from backend.app.api.versions import router as versions_router
from backend.app.api.resolution import router as resolution_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    job_manager.start_dispatcher()
    yield
    job_manager.stop_dispatcher()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url=None,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(versions_router, prefix="/api/v1")
app.include_router(resolution_router, prefix="/api/v1")

frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.isdir(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=False)
