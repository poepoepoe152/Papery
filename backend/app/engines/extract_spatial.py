"""Layout-aware field extraction for digital PDFs.

Real business forms (B/L, booking confirmations) are multi-column boxed
layouts where the value sits to the RIGHT of its label or directly BELOW it.
Plain line-based matching grabs wrong cells on such forms. This extractor uses
per-word coordinates (from PyMuPDF) to:

1. group words into visual lines,
2. locate label anchors from the FIELD_CATALOG aliases,
3. take the value from the same line (right of the label, clipped at the next
   label) or from the line(s) directly below within the label's column,
4. validate candidates per field kind (container pattern, digits, dates).

Only applies to digital PDFs (where word boxes exist); images/DOCX fall back
to the line-based extractor.
"""
import re

from ..doctypes import FIELD_CATALOG
from . import normalize as norm

_LINE_TOL = 3.5       # words within this y-distance form one visual line
_BELOW_MAX_DY = 46    # how far below a label a value may sit (pt)
_JOIN_GAP = 14        # max x-gap when joining words of one value (pt)
_BELOW_X_SLACK = 40   # value may start slightly right of the label box


def _alias_patterns():
    pats = []
    for key, meta in FIELD_CATALOG.items():
        for alias in meta["aliases"]:
            pats.append((
                alias,
                key,
                re.compile(r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z])"),
            ))
    # longest alias first so specific labels claim their words
    return sorted(pats, key=lambda p: len(p[0]), reverse=True)


_PATTERNS = _alias_patterns()


def _mkline(page: int, ws: list) -> dict:
    ws = sorted(ws, key=lambda w: w[1])
    text = ""
    offsets = []
    for w in ws:
        if text:
            text += " "
        offsets.append((len(text), len(text) + len(w[5])))
        text += w[5]
    return {
        "page": page,
        "y0": min(w[2] for w in ws),
        "words": ws,
        "lower": text.lower(),
        "offsets": offsets,
    }


def _build_lines(words: list) -> list[dict]:
    """words: [(page, x0, y0, x1, y1, text), ...] -> visual lines."""
    by_page: dict = {}
    for w in words:
        by_page.setdefault(w[0], []).append(w)

    lines = []
    for page in sorted(by_page):
        ws = sorted(by_page[page], key=lambda w: (w[2], w[1]))
        cur: list = []
        cur_y = None
        for w in ws:
            if cur_y is None or abs(w[2] - cur_y) <= _LINE_TOL:
                cur.append(w)
                if cur_y is None:
                    cur_y = w[2]
            else:
                lines.append(_mkline(page, cur))
                cur, cur_y = [w], w[2]
        if cur:
            lines.append(_mkline(page, cur))
    return lines


def _line_matches(line: dict) -> list[dict]:
    """Label anchors found on a line: word span + pixel range per match."""
    found = []
    taken = [False] * len(line["words"])
    for alias, key, pat in _PATTERNS:
        for m in pat.finditer(line["lower"]):
            idxs = [
                i for i, (s, e) in enumerate(line["offsets"])
                if s < m.end() and e > m.start()
            ]
            if not idxs or any(taken[i] for i in idxs):
                continue
            for i in idxs:
                taken[i] = True
            found.append({
                "key": key,
                "alias": alias,
                "start": idxs[0],
                "end": idxs[-1],
                "x0": line["words"][idxs[0]][1],
                "x1": line["words"][idxs[-1]][3],
            })
    found.sort(key=lambda f: f["start"])
    return found


def _clean(value: str) -> str:
    return value.strip(" \t:#|.-")


def _same_line_value(line: dict, match: dict, matches: list[dict]) -> str:
    nxt = min(
        (m["start"] for m in matches if m["start"] > match["end"]),
        default=len(line["words"]),
    )
    toks = [w[5] for w in line["words"][match["end"] + 1 : nxt]]
    return _clean(" ".join(toks))


def _below_value(lines: list[dict], li: int, match: dict,
                 matches_per_line: list[list[dict]]) -> str:
    base = lines[li]
    for lj in range(li + 1, len(lines)):
        ln = lines[lj]
        if ln["page"] != base["page"]:
            break
        dy = ln["y0"] - base["y0"]
        if dy <= 1:
            continue
        if dy > _BELOW_MAX_DY:
            break
        bmatches = matches_per_line[lj]

        start = None
        for i, w in enumerate(ln["words"]):
            if match["x0"] - 8 <= w[1] <= match["x1"] + _BELOW_X_SLACK:
                start = i
                break
        if start is None:
            continue
        # A different label sits directly below -> no value in this box.
        if any(m["start"] <= start <= m["end"] for m in bmatches):
            return ""

        toks = [ln["words"][start][5]]
        last_x1 = ln["words"][start][3]
        for i in range(start + 1, len(ln["words"])):
            w = ln["words"][i]
            if any(m["start"] <= i <= m["end"] for m in bmatches):
                break
            if w[1] - last_x1 > _JOIN_GAP:
                break
            toks.append(w[5])
            last_x1 = w[3]
        return _clean(" ".join(toks))
    return ""


def _column_values(lines: list[dict], li: int, match: dict,
                   matches_per_line: list[list[dict]]) -> list[str]:
    """Walk down the label's column collecting every cell value (table rows),
    stopping at another label in the column or a large vertical gap."""
    base = lines[li]
    out: list[str] = []
    prev_y = base["y0"]
    for lj in range(li + 1, len(lines)):
        ln = lines[lj]
        if ln["page"] != base["page"]:
            break
        dy = ln["y0"] - prev_y
        if dy <= 1:
            continue
        if dy > 80:  # column ended
            break
        bmatches = matches_per_line[lj]
        start = None
        for i, w in enumerate(ln["words"]):
            if match["x0"] - 8 <= w[1] <= match["x1"] + _BELOW_X_SLACK:
                start = i
                break
        if start is None:
            continue
        if any(m["start"] <= start <= m["end"] for m in bmatches):
            break  # a different label heads the column below
        toks = [ln["words"][start][5]]
        last_x1 = ln["words"][start][3]
        for i in range(start + 1, len(ln["words"])):
            w = ln["words"][i]
            if any(m["start"] <= i <= m["end"] for m in bmatches):
                break
            if w[1] - last_x1 > _JOIN_GAP:
                break
            toks.append(w[5])
            last_x1 = w[3]
        out.append(_clean(" ".join(toks)))
        prev_y = ln["y0"]
    return out


def _valid(value: str, kind: str) -> bool:
    if not value:
        return False
    if kind == "container":
        return re.search(r"[A-Za-z]{4}\s?\d{6,7}", value) is not None
    if kind == "number":
        return re.search(r"\d", value) is not None
    if kind == "date":
        from dateutil import parser as date_parser

        try:
            date_parser.parse(value, fuzzy=True)
            return True
        except (ValueError, OverflowError):
            return False
    if kind == "id":
        return len(value) >= 3 and re.search(r"\d", value) is not None
    return re.search(r"[A-Za-z]{2,}", value) is not None


def extract_fields_spatial(words: list) -> dict[str, dict]:
    """words: [(page, x0, y0, x1, y1, text), ...] -> {field_key: {...}}"""
    if not words:
        return {}
    lines = _build_lines(words)
    matches_per_line = [_line_matches(ln) for ln in lines]

    result: dict[str, dict] = {}
    # For multi-valued fields (e.g. container/seal), collect every value on the
    # document keyed by its normalized form so all table rows are captured.
    multi: dict[str, dict] = {}

    for li, line in enumerate(lines):
        for match in matches_per_line[li]:
            key = match["key"]
            meta = FIELD_CATALOG[key]
            same = _same_line_value(line, match, matches_per_line[li])
            below = _below_value(lines, li, match, matches_per_line)

            candidates = []  # (raw, conf) — a table label can head a column of values
            if meta.get("multi"):
                if _valid(same, meta["kind"]):
                    candidates.append((same, 0.95))
                # collect the whole column of values beneath the label (rows)
                for col_val in _column_values(lines, li, match, matches_per_line):
                    if _valid(col_val, meta["kind"]):
                        candidates.append((col_val, 0.9))
                if not candidates:
                    continue
            else:
                if _valid(same, meta["kind"]):
                    candidates.append((same, 0.95))
                elif _valid(below, meta["kind"]):
                    candidates.append((below, 0.9))
                elif meta["kind"] == "text" and same:
                    # low-confidence fallback only for free-text fields; id/
                    # number/date/container must pass validation so a heading
                    # word never becomes a phantom identifier
                    candidates.append((same, 0.5))
                elif meta["kind"] == "text" and below:
                    candidates.append((below, 0.45))
                else:
                    continue

            for cand, conf in candidates:
                normalized = norm.normalize(cand, meta["kind"])
                if not normalized:
                    continue
                if meta.get("multi"):
                    bucket = multi.setdefault(key, {})
                    if normalized not in bucket:
                        bucket[normalized] = cand
                    continue
                prev = result.get(key)
                if (
                    prev is None
                    or conf > prev["confidence"]
                    or (conf == prev["confidence"]
                        and len(match["alias"]) > prev.get("_alias_len", 0))
                ):
                    result[key] = {
                        "raw": cand,
                        "normalized": normalized,
                        "confidence": conf,
                        "_alias_len": len(match["alias"]),
                    }

    for v in result.values():
        v.pop("_alias_len", None)

    for key, bucket in multi.items():
        values = [{"raw": raw, "normalized": nz} for nz, raw in bucket.items()]
        result[key] = {
            "raw": values[0]["raw"],
            "normalized": values[0]["normalized"],
            "confidence": 0.92,
            "values": values,
        }
    return result
