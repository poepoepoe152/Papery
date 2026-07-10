"""Value normalization helpers used by extraction and comparison."""
import re

from dateutil import parser as date_parser

# OCR character-confusion map (applied both directions during comparison).
OCR_CONFUSIONS = {
    "0": "O", "O": "0",
    "1": "I", "I": "1",
    "5": "S", "S": "5",
    "8": "B", "B": "8",
    "2": "Z", "Z": "2",
    "6": "G", "G": "6",
}

_NUMBER_RE = re.compile(r"[-+]?[\d.,]*\d")


def normalize_text(value: str) -> str:
    if value is None:
        return ""
    v = value.lower().strip()
    # Punctuation -> space so "CO., LTD" and "CO.,LTD" compare equal, then
    # collapse whitespace. Keeps letters/digits (incl. non-ASCII) intact.
    v = re.sub(r"[^\w\s]", " ", v)
    v = re.sub(r"\s+", " ", v).strip()
    return v


def normalize_id(value: str) -> str:
    """Identifiers: uppercase, drop spaces and common separators."""
    if value is None:
        return ""
    return re.sub(r"[\s\-_/.]", "", value).upper()


def normalize_container(value: str) -> str:
    """Container numbers: 4 letters + 7 digits, no separators."""
    if value is None:
        return ""
    cleaned = re.sub(r"[\s\-_/.]", "", value).upper()
    m = re.search(r"[A-Z]{4}\d{6,7}", cleaned)
    return m.group(0) if m else cleaned


def _canonical_number_token(token: str) -> str:
    """Resolve US ('1,234.50') vs EU ('1.234,50') grouping to a plain float
    string. When both separators appear, the rightmost is the decimal point.
    A lone comma with exactly two trailing digits is read as a decimal comma
    (EU '60,00'); otherwise a lone comma is a thousands separator."""
    has_dot = "." in token
    has_comma = "," in token
    if has_dot and has_comma:
        if token.rfind(",") > token.rfind("."):  # EU: comma is decimal
            token = token.replace(".", "").replace(",", ".")
        else:  # US: dot is decimal
            token = token.replace(",", "")
    elif has_comma:
        after = token.split(",")[-1]
        if token.count(",") == 1 and len(after) == 2:
            token = token.replace(",", ".")  # EU decimal comma
        else:
            token = token.replace(",", "")  # thousands separators
    return token


def normalize_number(value: str) -> str:
    """Extract the first numeric token and normalize grouping + trailing zeros
    so '26,557.680' == '26557.68' and '1.000,50' == '1000.5'."""
    if value is None:
        return ""
    m = _NUMBER_RE.search(value.replace(" ", ""))
    if not m:
        return normalize_text(value)
    token = _canonical_number_token(m.group(0))
    try:
        num = float(token)
    except ValueError:
        return normalize_text(value)
    if num == int(num):
        return str(int(num))
    return ("%f" % num).rstrip("0").rstrip(".")


def normalize_date(value: str) -> str:
    if value is None:
        return ""
    try:
        dt = date_parser.parse(value, dayfirst=False, fuzzy=True)
        return dt.strftime("%Y-%m-%d")
    except (ValueError, OverflowError):
        return normalize_text(value)


def _parse_date(value: str, dayfirst: bool):
    try:
        return date_parser.parse(value, dayfirst=dayfirst, fuzzy=True).date()
    except (ValueError, OverflowError, TypeError):
        return None


def _date_candidates(value: str) -> set:
    """All plausible dates for a string across day/month conventions."""
    out = set()
    for dayfirst in (False, True):
        d = _parse_date(value, dayfirst)
        if d is not None:
            out.add(d)
    return out


def _unambiguous_date(value: str):
    """Return the single forced date if the string admits only one reading
    (ISO YYYY-MM-DD, a spelled-out month, or a day component > 12), else None."""
    if value is None:
        return None
    if re.search(r"\b\d{4}-\d{1,2}-\d{1,2}\b", value):
        return _parse_date(value, False)
    if re.search(r"[A-Za-z]{3,}", value):  # month name present
        return _parse_date(value, False)
    two_digit = [int(n) for n in re.findall(r"\b\d{1,2}\b", value)]
    if any(12 < n <= 31 for n in two_digit):
        return _parse_date(value, False)
    return None


def dates_equivalent(a: str, b: str) -> bool:
    """True if two date strings denote the same calendar day.

    Resolves ISO-vs-slash format differences ('2026-02-10' == '10/02/2026')
    by anchoring on whichever side is unambiguous. When BOTH sides are
    ambiguous slash dates, it does NOT mask a day/month swap — it requires
    agreement under a single fixed convention."""
    ua, ub = _unambiguous_date(a), _unambiguous_date(b)
    if ua is not None and ub is not None:
        return ua == ub
    if ua is not None:
        return ua in _date_candidates(b)
    if ub is not None:
        return ub in _date_candidates(a)
    return _parse_date(a, False) is not None and _parse_date(a, False) == _parse_date(b, False)


def normalize(value: str, kind: str) -> str:
    if kind == "number":
        return normalize_number(value)
    if kind == "date":
        return normalize_date(value)
    if kind == "container":
        return normalize_container(value)
    if kind == "id":
        return normalize_id(value)
    return normalize_text(value)


def ocr_normalize(value: str) -> str:
    """Collapse OCR-confusable characters to a canonical form for comparison."""
    canon = {
        "O": "0", "I": "1", "S": "5", "B": "8", "Z": "2", "G": "6",
    }
    out = []
    for ch in value.upper():
        out.append(canon.get(ch, ch))
    return "".join(out)
