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
    v = re.sub(r"\s+", " ", v)
    v = v.strip(" .,:;-\t")
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


def normalize_number(value: str) -> str:
    """Extract the first numeric token and drop thousands separators and
    trailing zeros so '26,557.680' == '26557.68'."""
    if value is None:
        return ""
    m = _NUMBER_RE.search(value.replace(" ", ""))
    if not m:
        return normalize_text(value)
    token = m.group(0)
    # Treat commas as thousands separators.
    token = token.replace(",", "")
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
