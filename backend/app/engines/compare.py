"""AI comparison engine (deterministic core + optional LLM hook).

Pipeline per field: exact → normalized(formatting) → OCR-confusion → fuzzy →
mismatch. Severity comes from the field catalog. The semantic LLM stage is a
disabled-by-default hook (see maybe_llm_semantic) kept for cost-gated use.
"""
from rapidfuzz import fuzz

from ..config import settings
from ..doctypes import FIELD_CATALOG
from . import normalize as norm

FUZZY_THRESHOLD = 88.0  # 0..100


def _severity(field_key: str) -> str:
    return FIELD_CATALOG.get(field_key, {}).get("severity", "MAJOR")


def _label(field_key: str) -> str:
    return FIELD_CATALOG.get(field_key, {}).get("label", field_key)


def maybe_llm_semantic(ref: str, tgt: str, field_key: str) -> dict | None:
    """Cost-gated semantic check. Returns None unless an LLM is configured.

    Wiring a provider here lets the engine resolve abbreviations / synonyms when
    deterministic confidence is low (architecture stage 5). Disabled by default.
    """
    if not settings.OPENAI_API_KEY:
        return None
    return None  # Provider integration is added in a later phase.


def _compare_pair(field_key: str, ref_raw: str, ref_norm: str, tgt_raw: str, tgt_norm: str) -> dict:
    meta = FIELD_CATALOG.get(field_key, {"kind": "text"})
    sev = _severity(field_key)

    # 1) exact normalized match.
    if ref_norm == tgt_norm:
        if ref_raw.strip() == tgt_raw.strip():
            return {"match_type": "EXACT", "severity": "MINOR", "confidence": 1.0,
                    "explanation": "Values match exactly.", "suggested_fix": None,
                    "is_problem": False}
        return {"match_type": "NORMALIZED", "severity": "MINOR", "confidence": 0.99,
                "explanation": "Formatting differs but values are identical.",
                "suggested_fix": None, "is_problem": False}

    # 1b) date equivalence (ISO vs slash formats denote the same day).
    if meta.get("kind") == "date" and norm.dates_equivalent(ref_raw, tgt_raw):
        return {"match_type": "NORMALIZED", "severity": "MINOR", "confidence": 0.98,
                "explanation": "Same date written in a different format.",
                "suggested_fix": None, "is_problem": False}

    # 2) OCR-confusion aware.
    if norm.ocr_normalize(ref_norm) == norm.ocr_normalize(tgt_norm):
        return {"match_type": "FUZZY", "severity": sev, "confidence": 0.7,
                "explanation": "Difference matches a common OCR substitution "
                               "(e.g. O/0, I/1, S/5, B/8).",
                "suggested_fix": ref_raw, "is_problem": True}

    # 3) fuzzy similarity.
    ratio = fuzz.ratio(ref_norm, tgt_norm)
    if ratio >= FUZZY_THRESHOLD:
        return {"match_type": "FUZZY", "severity": sev, "confidence": ratio / 100.0,
                "explanation": f"Values are similar ({ratio:.0f}% match) but not identical.",
                "suggested_fix": ref_raw, "is_problem": True}

    # 4) gated semantic (optional).
    llm = maybe_llm_semantic(ref_raw, tgt_raw, field_key)
    if llm is not None:
        return llm

    # 5) mismatch.
    return {"match_type": "MISMATCH", "severity": sev, "confidence": ratio / 100.0,
            "explanation": "Values do not match.",
            "suggested_fix": ref_raw, "is_problem": True}


def _values_of(entry: dict) -> list[dict]:
    if not entry:
        return []
    return entry.get("values") or [
        {"raw": entry["raw"], "normalized": entry["normalized"]}
    ]


def _compare_multi(field_key: str, ref: dict, tgt: dict) -> list[dict]:
    """Set comparison for multi-valued fields (all containers / seals): every
    reference value must appear in the target; report changed / missing / extra."""
    label = _label(field_key)
    sev = _severity(field_key)
    ref_vals = _values_of(ref)
    tgt_vals = list(_values_of(tgt))
    findings: list[dict] = []

    def base(match_type, severity, ref_v, det_v, conf, expl, fix, problem):
        return {
            "field_key": field_key, "field_label": label,
            "reference_value": ref_v, "detected_value": det_v,
            "match_type": match_type, "severity": severity, "confidence": conf,
            "used_llm": False, "explanation": expl, "suggested_fix": fix,
            "is_problem": problem,
        }

    remaining = tgt_vals[:]
    unmatched_refs = []
    # 1) exact (normalized) pairing
    for rv in ref_vals:
        hit = next((t for t in remaining if t["normalized"] == rv["normalized"]), None)
        if hit is not None:
            remaining.remove(hit)
        else:
            unmatched_refs.append(rv)

    # 1b) exactly one value differs on each side -> clearly the same slot changed
    if len(unmatched_refs) == 1 and len(remaining) == 1:
        rv, tv = unmatched_refs[0], remaining[0]
        ocr = norm.ocr_normalize(rv["normalized"]) == norm.ocr_normalize(tv["normalized"])
        expl = ("Difference matches a common OCR substitution."
                if ocr else "Value differs from the reference.")
        return [base("FUZZY", sev, rv["raw"], tv["raw"], 0.7, expl, rv["raw"], True)]

    # 2) fuzzy / OCR pairing for the leftovers
    for rv in unmatched_refs:
        if not remaining:
            findings.append(base("MISSING", sev, rv["raw"], None, 0.9,
                                 f"{label} not found in target.", rv["raw"], True))
            continue
        best = max(remaining, key=lambda t: fuzz.ratio(rv["normalized"], t["normalized"]))
        ratio = fuzz.ratio(rv["normalized"], best["normalized"])
        ocr = norm.ocr_normalize(rv["normalized"]) == norm.ocr_normalize(best["normalized"])
        if ocr or ratio >= FUZZY_THRESHOLD:
            remaining.remove(best)
            expl = ("Difference matches a common OCR substitution."
                    if ocr else f"Values are similar ({ratio:.0f}% match) but not identical.")
            findings.append(base("FUZZY", sev, rv["raw"], best["raw"],
                                 0.7 if ocr else ratio / 100.0, expl, rv["raw"], True))
        else:
            findings.append(base("MISSING", sev, rv["raw"], None, ratio / 100.0,
                                 f"{label} not found in target.", rv["raw"], True))

    # 3) any target values left over are extras
    for t in remaining:
        findings.append(base("EXTRA", "MINOR", None, t["raw"], 0.6,
                             f"{label} present in target but not in reference.", None, True))

    return findings


def compare(reference_fields: dict, target_fields: dict) -> list[dict]:
    """Return a list of finding dicts comparing target against reference."""
    findings: list[dict] = []
    keys = set(reference_fields) | set(target_fields)

    for field_key in sorted(keys):
        ref = reference_fields.get(field_key)
        tgt = target_fields.get(field_key)
        label = _label(field_key)

        if FIELD_CATALOG.get(field_key, {}).get("multi"):
            if ref or tgt:
                findings.extend(_compare_multi(field_key, ref, tgt))
            continue

        if ref and not tgt:
            findings.append({
                "field_key": field_key, "field_label": label,
                "reference_value": ref["raw"], "detected_value": None,
                "match_type": "MISSING", "severity": _severity(field_key),
                "confidence": 0.9, "used_llm": False,
                "explanation": "Field present in reference but missing in target.",
                "suggested_fix": ref["raw"], "is_problem": True,
            })
            continue
        if tgt and not ref:
            findings.append({
                "field_key": field_key, "field_label": label,
                "reference_value": None, "detected_value": tgt["raw"],
                "match_type": "EXTRA", "severity": "MINOR",
                "confidence": 0.6, "used_llm": False,
                "explanation": "Field present in target but not in reference.",
                "suggested_fix": None, "is_problem": True,
            })
            continue

        res = _compare_pair(
            field_key, ref["raw"], ref["normalized"], tgt["raw"], tgt["normalized"]
        )
        findings.append({
            "field_key": field_key, "field_label": label,
            "reference_value": ref["raw"], "detected_value": tgt["raw"],
            "match_type": res["match_type"], "severity": res["severity"],
            "confidence": res["confidence"], "used_llm": False,
            "explanation": res["explanation"], "suggested_fix": res["suggested_fix"],
            "is_problem": res["is_problem"],
        })

    return findings


def summarize(findings: list[dict]) -> dict:
    """Compute counts and overall result from problem findings."""
    crit = sum(1 for f in findings if f["is_problem"] and f["severity"] == "CRITICAL")
    major = sum(1 for f in findings if f["is_problem"] and f["severity"] == "MAJOR")
    minor = sum(
        1 for f in findings
        if f["severity"] == "MINOR" and (f["is_problem"] or f["match_type"] == "NORMALIZED")
    )
    if crit:
        overall = "FAIL"
    elif major:
        overall = "WARN"
    else:
        overall = "PASS"
    return {"critical": crit, "major": major, "minor": minor, "overall": overall}
