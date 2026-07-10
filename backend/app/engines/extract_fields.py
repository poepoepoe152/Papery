"""Deterministic, schema-driven field extraction.

Line-oriented label/anchor extraction: for each field alias we look for the
label followed by its value (same line, or the next non-empty line). Values are
normalized per field kind. Confidence reflects alias specificity.
"""
import re

from ..doctypes import FIELD_CATALOG
from . import normalize as norm

# Strip a trailing value that is actually the next label, e.g. "ACME  Consignee:".
_STOP_WORDS = sorted(
    {alias for meta in FIELD_CATALOG.values() for alias in meta["aliases"]},
    key=len,
    reverse=True,
)


def _clean_value(value: str) -> str:
    value = value.strip(" \t:.-")
    # Cut at a following label if present on the same line.
    low = value.lower()
    cut = len(value)
    for sw in _STOP_WORDS:
        i = low.find(sw + ":")
        if 0 < i < cut:
            cut = i
    return value[:cut].strip(" \t:.-")


def _find_value(lines: list[str], alias: str) -> str | None:
    pattern = re.compile(
        r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z])\s*[:#\-]?\s*(.*)",
        re.IGNORECASE,
    )
    for i, line in enumerate(lines):
        m = pattern.search(line)
        if not m:
            continue
        value = _clean_value(m.group(1))
        if value:
            return value
        # Value likely on the following non-empty line.
        for nxt in lines[i + 1 : i + 3]:
            nxt = nxt.strip()
            if nxt:
                return _clean_value(nxt)
    return None


def extract_fields(text: str) -> dict[str, dict]:
    if not text:
        return {}
    lines = [ln for ln in text.splitlines()]
    result: dict[str, dict] = {}

    for field_key, meta in FIELD_CATALOG.items():
        best_value = None
        best_alias_len = -1
        # Prefer the most specific (longest) alias that matches.
        for alias in sorted(meta["aliases"], key=len, reverse=True):
            value = _find_value(lines, alias)
            if value and len(alias) > best_alias_len:
                best_value = value
                best_alias_len = len(alias)
        if best_value is None:
            continue
        normalized = norm.normalize(best_value, meta["kind"])
        if not normalized:
            continue
        # Numeric/identifier/date fields must contain a digit — this rejects
        # phantom matches where a bare alias (e.g. "Booking" in the title
        # "BOOKING CONFIRMATION") captures an all-letters word.
        if meta["kind"] in ("id", "number", "container", "date") and not any(
            ch.isdigit() for ch in normalized
        ):
            continue
        confidence = 0.9 if best_alias_len >= 6 else 0.75
        result[field_key] = {
            "raw": best_value,
            "normalized": normalized,
            "confidence": confidence,
        }
    return result
