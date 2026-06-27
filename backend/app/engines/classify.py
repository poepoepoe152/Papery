"""Heuristic document-type classification.

Deterministic keyword/anchor matching (architecture stage 1). The ML and
gated-LLM stages are future enhancements; low-confidence docs are UNKNOWN.
"""
from ..doctypes import CLASSIFICATION_RULES


def classify(text: str) -> tuple[str, float]:
    if not text:
        return "UNKNOWN", 0.0
    lowered = text.lower()
    for doc_type, keywords in CLASSIFICATION_RULES:
        for kw in keywords:
            if kw in lowered:
                # Header anchors near the top score higher.
                idx = lowered.find(kw)
                confidence = 0.95 if idx < 600 else 0.8
                return doc_type, confidence
    return "UNKNOWN", 0.0
