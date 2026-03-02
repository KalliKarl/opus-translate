"""Opus Translate — Dil algılama."""

from schemas import DetectResponse

_TURKISH_CHARS = set("çğıöşüÇĞİÖŞÜ")


class LanguageDetector:
    """Türkçe karakter heuristic'i ile dil algılama."""

    def detect(self, text: str) -> DetectResponse:
        turkish_count = sum(1 for c in text if c in _TURKISH_CHARS)
        total_alpha = sum(1 for c in text if c.isalpha()) or 1
        ratio = turkish_count / total_alpha

        if ratio > 0.02:
            return DetectResponse(
                language="tr",
                confidence=min(0.6 + ratio * 5, 0.99),
                suggested_direction="tr-en",
            )

        return DetectResponse(
            language="en",
            confidence=0.8 if turkish_count == 0 else 0.6,
            suggested_direction="en-tr",
        )
