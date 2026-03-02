"""Opus Translate — Çeviri motoru (sadece çeviri sorumluluğu)."""

import logging
import time

import torch
from transformers import MarianMTModel, MarianTokenizer

from config import settings

log = logging.getLogger("translator")


class TranslatorEngine:
    """MarianMT tabanlı çeviri motoru. Lazy model loading."""

    def __init__(self) -> None:
        self._models: dict[str, MarianMTModel] = {}
        self._tokenizers: dict[str, MarianTokenizer] = {}
        self._device: str = settings.resolved_device
        self.total_translations: int = 0
        self.start_time: float = time.time()

    @property
    def device(self) -> str:
        return self._device

    @property
    def loaded_models(self) -> list[str]:
        return list(self._models.keys())

    # --- Model yönetimi ---

    def _ensure_model(self, direction: str) -> None:
        if direction in self._models:
            return
        model_id = settings.models[direction]
        log.info("%s yükleniyor (%s)...", model_id, self._device)
        tokenizer = MarianTokenizer.from_pretrained(model_id)
        model = MarianMTModel.from_pretrained(model_id)
        model.to(self._device)
        model.eval()
        self._tokenizers[direction] = tokenizer
        self._models[direction] = model
        log.info("%s hazır.", model_id)

    # --- Çeviri (DRY: ortak inference) ---

    def _inference(self, texts: list[str], direction: str) -> list[str]:
        self._ensure_model(direction)
        tokenizer = self._tokenizers[direction]
        model = self._models[direction]

        inputs = tokenizer(
            texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=settings.max_length,
        )
        inputs = {k: v.to(self._device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model.generate(**inputs, max_length=settings.max_length)

        results = [tokenizer.decode(o, skip_special_tokens=True) for o in outputs]
        self.total_translations += len(results)
        return results

    def translate(self, text: str, direction: str) -> str:
        return self._inference([text], direction)[0]

    def translate_batch(self, texts: list[str], direction: str) -> list[str]:
        return self._inference(texts, direction)

    # --- GPU bilgisi ---

    def gpu_info(self) -> dict[str, str] | None:
        if self._device != "cuda":
            return None
        try:
            idx = torch.cuda.current_device()
            props = torch.cuda.get_device_properties(idx)
            return {
                "gpu_name": torch.cuda.get_device_name(idx),
                "gpu_memory_used": f"{torch.cuda.memory_allocated(idx) // (1024 * 1024)} MB",
                "gpu_memory_total": f"{props.total_mem // (1024 * 1024)} MB",
            }
        except Exception:
            return None
