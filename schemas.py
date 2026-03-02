"""Opus Translate — Request/Response modelleri."""

from pydantic import BaseModel, Field


class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    direction: str = Field(..., pattern=r"^(tr-en|en-tr)$")


class TranslateResponse(BaseModel):
    translation: str
    direction: str
    model: str
    duration_ms: float


class BatchRequest(BaseModel):
    texts: list[str] = Field(..., min_length=1)
    direction: str = Field(..., pattern=r"^(tr-en|en-tr)$")


class BatchResponse(BaseModel):
    translations: list[str]
    direction: str
    count: int
    duration_ms: float


class DetectResponse(BaseModel):
    language: str
    confidence: float
    suggested_direction: str


class HealthResponse(BaseModel):
    status: str
    device: str
    models_loaded: list[str]
    uptime: int
    total_translations: int
    gpu_name: str | None = None
    gpu_memory_used: str | None = None
    gpu_memory_total: str | None = None
