"""Unit tests for the document-understanding engines (offline, no DB)."""
from app.engines import classify, compare
from app.engines import extract_fields as ef
from app.engines import normalize as norm


# --- normalization ---
def test_number_normalization_ignores_formatting():
    assert norm.normalize_number("26,557.680") == norm.normalize_number("26557.68")
    assert norm.normalize_number("26,557.680 kg") == "26557.68"
    assert norm.normalize_number("1,000") == "1000"


def test_date_normalization():
    assert norm.normalize_date("2026-01-05") == "2026-01-05"
    assert norm.normalize_date("Jan 5, 2026") == "2026-01-05"


def test_container_normalization():
    assert norm.normalize_container("tclu 123 4567") == "TCLU1234567"


def test_ocr_normalize_collapses_confusables():
    assert norm.ocr_normalize("TCLU1234567") == norm.ocr_normalize("TCLuI234567")


# --- classification ---
def test_classify_bill_of_lading():
    doc_type, conf = classify.classify("DRAFT BILL OF LADING\nShipper: ACME")
    assert doc_type == "DRAFT_BL"
    assert conf > 0.5


def test_classify_unknown():
    doc_type, conf = classify.classify("random unrelated text")
    assert doc_type == "UNKNOWN"


# --- field extraction ---
SAMPLE = """BOOKING CONFIRMATION
Booking No: SITGUAYE12345
Shipper: ACME FREIGHT CO
Consignee: GLOBEX LOGISTICS
Container No: TCLU1234567
Seal No: ML-998877
Gross Weight: 26,557.680 KG
Port of Loading: SHANGHAI
"""


def test_extract_fields_finds_key_values():
    fields = ef.extract_fields(SAMPLE)
    assert fields["booking_number"]["normalized"] == "SITGUAYE12345"
    assert fields["container_number"]["normalized"] == "TCLU1234567"
    assert fields["gross_weight"]["normalized"] == "26557.68"
    assert "consignee" in fields


# --- comparison ---
def _fld(raw, kind="text"):
    return {"raw": raw, "normalized": norm.normalize(raw, kind), "confidence": 0.9}


def test_compare_exact_is_not_a_problem():
    ref = {"booking_number": _fld("ABC123", "id")}
    tgt = {"booking_number": _fld("ABC123", "id")}
    findings = compare.compare(ref, tgt)
    assert findings[0]["match_type"] == "EXACT"
    assert findings[0]["is_problem"] is False


def test_compare_formatting_only_is_minor_pass():
    ref = {"gross_weight": _fld("26,557.68", "number")}
    tgt = {"gross_weight": _fld("26557.680", "number")}
    findings = compare.compare(ref, tgt)
    assert findings[0]["match_type"] == "NORMALIZED"
    summary = compare.summarize(findings)
    assert summary["overall"] == "PASS"


def test_compare_critical_mismatch_fails():
    ref = {"container_number": _fld("TCLU1234567", "container")}
    tgt = {"container_number": _fld("TCLU7654321", "container")}
    findings = compare.compare(ref, tgt)
    summary = compare.summarize(findings)
    assert summary["overall"] == "FAIL"
    assert summary["critical"] == 1


def test_compare_missing_field():
    ref = {"seal_number": _fld("ML-998877", "id")}
    tgt = {}
    findings = compare.compare(ref, tgt)
    assert findings[0]["match_type"] == "MISSING"


def test_document_title_does_not_create_phantom_id_field():
    """'BOOKING CONFIRMATION' as a heading must not yield booking_number=CONFIRMATION."""
    fields = ef.extract_fields("BOOKING CONFIRMATION\nShipper: ACME CO\nConsignee: GLOBEX")
    assert "booking_number" not in fields
    # numeric/id fields require a digit
    fields2 = ef.extract_fields("Seal No: SEALED\nContainer No: TCLU1234567")
    assert "seal_number" not in fields2  # "SEALED" has no digit
    assert fields2["container_number"]["normalized"] == "TCLU1234567"
