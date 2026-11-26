from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_settings()  # fail at startup, with a clear message, if configuration is missing
    yield


app = FastAPI(title="SAP Guide", lifespan=lifespan)
app.include_router(router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}