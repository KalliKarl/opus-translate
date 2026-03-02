"""Opus Translate — FastAPI sunucu."""

import asyncio
import logging
import time
from pathlib import Path
from contextlib import asynccontextmanager

import torch
from fastapi import FastAPI, Query, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from config import settings
from auth import require_api_key
from schemas import (
    TranslateRequest, TranslateResponse,
    BatchRequest, BatchResponse,
    DetectResponse, HealthResponse,
    DeviceSwitchRequest, DeviceSwitchResponse,
    ModelStatusResponse,
)
from translator import TranslatorEngine
from detector import LanguageDetector

log = logging.getLogger("server")

engine = TranslatorEngine()
detector = LanguageDetector()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Opus Translate başlatılıyor — %s:%s", settings.host, settings.port)
    log.info("Device: %s  |  API key: %s", engine.device, "aktif" if settings.api_key else "yok")
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
async def translate(req: TranslateRequest, _=Depends(require_api_key)):
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
async def translate_batch(req: BatchRequest, _=Depends(require_api_key)):
    if len(req.texts) > settings.batch_size:
        raise HTTPException(400, f"texts max {settings.batch_size} öğe içerebilir")
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
        cuda_available=torch.cuda.is_available(),
        **(gpu or {}),
    )


@app.get("/detect", response_model=DetectResponse)
async def detect(
    text: str = Query(..., min_length=1, max_length=5000),
    _=Depends(require_api_key),
):
    return detector.detect(text)


# --- Cihaz yönetimi ---


@app.post("/config/device", response_model=DeviceSwitchResponse)
async def switch_device(req: DeviceSwitchRequest, _=Depends(require_api_key)):
    if req.device not in ("cuda", "cpu"):
        raise HTTPException(400, "device 'cuda' veya 'cpu' olmalı")
    if req.device == "cuda" and not torch.cuda.is_available():
        raise HTTPException(400, "CUDA bu sunucuda mevcut değil")
    actual = engine.switch_device(req.device)
    return DeviceSwitchResponse(device=actual, message=f"{actual} aktif, modeller lazy reload bekliyor")


# --- Model yönetimi ---


@app.post("/models/{direction}/load", response_model=ModelStatusResponse)
async def load_model(direction: str, _=Depends(require_api_key)):
    if direction not in settings.models:
        raise HTTPException(400, f"Geçersiz direction: {direction}")
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, engine._ensure_model, direction)
    return ModelStatusResponse(direction=direction, loaded=True, message="Model yüklendi")


@app.delete("/models/{direction}", response_model=ModelStatusResponse)
async def unload_model(direction: str, _=Depends(require_api_key)):
    if direction not in settings.models:
        raise HTTPException(400, f"Geçersiz direction: {direction}")
    engine.unload_model(direction)
    return ModelStatusResponse(direction=direction, loaded=False, message="Model boşaltıldı")


# --- Doğrudan çalıştırma ---

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host=settings.host, port=settings.port, reload=False)
