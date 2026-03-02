"""Opus Translate — FastAPI sunucu."""

import logging
import time
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from config import settings
from schemas import (
    TranslateRequest, TranslateResponse,
    BatchRequest, BatchResponse,
    DetectResponse, HealthResponse,
)
from translator import TranslatorEngine
from detector import LanguageDetector

log = logging.getLogger("server")

engine = TranslatorEngine()
detector = LanguageDetector()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Opus Translate başlatılıyor — %s:%s", settings.host, settings.port)
    log.info("Device: %s", engine.device)
    yield
    log.info("Kapatılıyor.")


app = FastAPI(
    title="Opus Translate",
    description="Self-hosted Türkçe↔İngilizce çeviri API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# --- Endpointler ---


@app.get("/", include_in_schema=False)
async def root():
    return FileResponse(str(static_dir / "index.html"))


@app.post("/translate", response_model=TranslateResponse)
async def translate(req: TranslateRequest):
    t0 = time.perf_counter()
    result = engine.translate(req.text, req.direction)
    duration = (time.perf_counter() - t0) * 1000
    return TranslateResponse(
        translation=result,
        direction=req.direction,
        model=settings.models[req.direction].split("/")[-1],
        duration_ms=round(duration, 1),
    )


@app.post("/translate/batch", response_model=BatchResponse)
async def translate_batch(req: BatchRequest):
    t0 = time.perf_counter()
    results = engine.translate_batch(req.texts, req.direction)
    duration = (time.perf_counter() - t0) * 1000
    return BatchResponse(
        translations=results,
        direction=req.direction,
        count=len(results),
        duration_ms=round(duration, 1),
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    gpu = engine.gpu_info()
    return HealthResponse(
        status="running",
        device=engine.device,
        models_loaded=engine.loaded_models,
        uptime=int(time.time() - engine.start_time),
        total_translations=engine.total_translations,
        **(gpu or {}),
    )


@app.get("/detect", response_model=DetectResponse)
async def detect(text: str = Query(..., min_length=1, max_length=5000)):
    return detector.detect(text)


# --- Doğrudan çalıştırma ---

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host=settings.host, port=settings.port, reload=False)
