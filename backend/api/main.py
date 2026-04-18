"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.db.database import init_db
from backend.api.routes import auth, classify, feedback, stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Spam SMS Filter API",
    description="Real-time SMS spam classification with ML models and user feedback.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(classify.router, prefix="/api/v1")
app.include_router(feedback.router, prefix="/api/v1")
app.include_router(stats.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
