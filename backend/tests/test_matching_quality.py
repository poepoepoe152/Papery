"""Regression tests for match quality: no nagging (false positives) and no
missed real errors (false negatives) across real-world field variations."""
import pytest

from app.engines import compare
from app.engines import normalize as norm


def fld(raw, kind):
    return {"raw": raw, "normalized": norm.normalize(raw, kind), "confidence": 0.9}


# Pairs that MUST be treated as equal (formatting/convention only).
SAME = [
    ("gross_weight", "number", "26,557.68 KG", "26557.680 KGS"),
    ("measurement_cbm", "number", "50.000 CBM", "50 CBM"),
    ("eta", "date", "2026-02-10", "10/02/2026"),
    ("etd", "date", "09/02/2026", "2026-02-09"),
    ("eta", "date", "Jan 5, 2026", "2026-01-05"),
    ("consignee", "text", "VISION INTERNATIONAL B.V.", "Vision International B.V"),
    ("shipper", "text", "RUIHUA IMPORT EXPORT CO., LTD", "RUIHUA IMPORT EXPORT CO.,LTD"),
    ("booking_number", "id", "6442748330", "644 2748 330"),
    ("container_number", "container", "TCLU 123 4567", "TCLU1234567"),
    ("voyage", "id", "1387-025W", "1387025W"),
]

# Pairs that MUST be flagged (genuine differences).
DIFF = [
    ("container_number", "container", "TCLU1234567", "TCLU1234561"),
    ("booking_number", "id", "6442748330", "6442748331"),
    ("gross_weight", "number", "26,557.68", "25,557.68"),
    ("consignee", "text", "VISION INTERNATIONAL B.V.", "VISTA INTERNATIONAL B.V."),
    ("seal_number", "id", "ML-998877", "ML-998878"),
    ("port_of_discharge", "text", "ROTTERDAM, NETHERLANDS", "ANTWERP, BELGIUM"),
    ("eta", "date", "2026-02-10", "2026-03-10"),
    # both-ambiguous day/month swap must NOT be masked
    ("etd", "date", "01/02/2026", "02/01/2026"),
]


@pytest.mark.parametrize("key,kind,ref,tgt", SAME)
def test_no_false_positive(key, kind, ref, tgt):
    findings = compare.compare({key: fld(ref, kind)}, {key: fld(tgt, kind)})
    # equal values must not produce any problem finding (multi fields that
    # match exactly produce no finding at all)
    assert not any(f["is_problem"] for f in findings), (
        f"nagged on identical values: {ref!r} vs {tgt!r}"
    )


@pytest.mark.parametrize("key,kind,ref,tgt", DIFF)
def test_no_false_negative(key, kind, ref, tgt):
    findings = compare.compare({key: fld(ref, kind)}, {key: fld(tgt, kind)})
    assert any(f["is_problem"] for f in findings), (
        f"missed a real difference: {ref!r} vs {tgt!r}"
    )


def test_dates_equivalent_direct():
    assert norm.dates_equivalent("2026-02-10", "10/02/2026")
    assert norm.dates_equivalent("13/02/2026", "2026-02-13")  # day>12 forces reading
    assert not norm.dates_equivalent("2026-02-10", "2026-03-10")
    assert not norm.dates_equivalent("01/02/2026", "02/01/2026")  # swap not masked


# --- multi-valued fields (all containers / seals on a B/L) ---
def _multi(values, kind):
    vals = [{"raw": v, "normalized": norm.normalize(v, kind)} for v in values]
    return {"raw": vals[0]["raw"], "normalized": vals[0]["normalized"],
            "confidence": 0.9, "values": vals}


def test_multi_container_all_match():
    conts = ["CSLU6072845", "TCLU1234567", "MSKU7654321"]
    findings = compare.compare({"container_number": _multi(conts, "container")},
                               {"container_number": _multi(conts, "container")})
    assert not any(f["is_problem"] for f in findings)


def test_multi_container_one_wrong_is_caught():
    ref = ["CSLU6072845", "TCLU1234567", "MSKU7654321"]
    tgt = ["CSLU6072845", "TCLU1234567", "MSKU7654320"]  # last digit changed
    findings = compare.compare({"container_number": _multi(ref, "container")},
                               {"container_number": _multi(tgt, "container")})
    problems = [f for f in findings if f["is_problem"]]
    assert len(problems) == 1 and problems[0]["severity"] == "CRITICAL"
    assert problems[0]["detected_value"] == "MSKU7654320"


def test_multi_container_missing_row_is_caught():
    ref = ["CSLU6072845", "TCLU1234567", "MSKU7654321"]
    tgt = ["CSLU6072845", "TCLU1234567"]  # a container dropped
    findings = compare.compare({"container_number": _multi(ref, "container")},
                               {"container_number": _multi(tgt, "container")})
    problems = [f for f in findings if f["is_problem"]]
    assert len(problems) == 1 and problems[0]["match_type"] == "MISSING"
    assert problems[0]["reference_value"] == "MSKU7654321"
