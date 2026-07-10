"""Regression test: layout-aware extraction on a realistic multi-column form.

Mimics a carrier B/L / booking layout (labels ABOVE values, boxed columns,
cargo table) — the layout that defeats plain line-based matching.
"""
from app.engines import compare, extract_fields, extract_spatial, text_extract

VALUES = {
    "booking": "6442748330",
    "bl": "COSU6442748330",
    "shipper": "RUIHUA IMPORT EXPORT CO., LTD",
    "vessel": "EVER GLOBE",
    "voyage": "1387-025W",
    "consignee": "VISION INTERNATIONAL B.V.",
    "notify": "VAREKAMP COLDSTORES HOLLAND B.V.",
    "pol": "LAEM CHABANG, THAILAND",
    "pod": "ROTTERDAM, NETHERLANDS",
    "container": "CSLU6072845",
    "seal": "COS26374925",
    "pkgs": "1912 BOXES",
    "gw": "26,557.68 KGS",
    "cbm": "50.000 CBM",
}


def make_form(path: str, title: str, v: dict) -> None:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(path), pagesize=A4)

    def label(x, y, t):
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x, y, t)

    def value(x, y, t):
        c.setFont("Helvetica", 11)
        c.drawString(x, y, t)

    c.setFont("Helvetica-Bold", 15)
    c.drawString(50, 800, title)
    label(350, 770, "Booking No.")
    value(350, 755, v["booking"])
    label(470, 770, "B/L No.")
    value(470, 755, v["bl"])
    label(50, 740, "Shipper")
    value(50, 725, v["shipper"])
    label(350, 740, "Vessel")
    value(350, 725, v["vessel"])
    label(470, 740, "Voyage")
    value(470, 725, v["voyage"])
    label(50, 700, "Consignee")
    value(50, 685, v["consignee"])
    label(50, 660, "Notify Party")
    value(50, 645, v["notify"])
    label(50, 610, "Port of Loading")
    value(50, 595, v["pol"])
    label(300, 610, "Port of Discharge")
    value(300, 595, v["pod"])
    label(50, 550, "Container No.")
    label(170, 550, "Seal No.")
    label(260, 550, "Packages")
    label(340, 550, "Gross Weight")
    label(460, 550, "Measurement")
    value(50, 535, v["container"])
    value(170, 535, v["seal"])
    value(260, 535, v["pkgs"])
    value(340, 535, v["gw"])
    value(460, 535, v["cbm"])
    c.save()


def _extract_merged(path: str, name: str) -> dict:
    extracted = text_extract.extract_text(str(path), name)
    fields = extract_fields.extract_fields(extracted["text"])
    for key, val in extract_spatial.extract_fields_spatial(extracted["words"]).items():
        cur = fields.get(key)
        if cur is None or val["confidence"] >= cur["confidence"]:
            fields[key] = val
    return fields


def test_spatial_extraction_on_multicolumn_form(tmp_path):
    pdf = tmp_path / "form.pdf"
    make_form(pdf, "BOOKING CONFIRMATION", VALUES)
    fields = _extract_merged(pdf, "form.pdf")

    assert fields["booking_number"]["raw"] == "6442748330"
    assert fields["bl_number"]["raw"] == "COSU6442748330"
    assert fields["container_number"]["normalized"] == "CSLU6072845"
    assert fields["seal_number"]["raw"] == "COS26374925"
    assert fields["gross_weight"]["normalized"] == "26557.68"
    assert fields["package_count"]["normalized"] == "1912"
    assert fields["vessel"]["raw"] == "EVER GLOBE"
    assert fields["voyage"]["raw"] == "1387-025W"
    assert "LAEM CHABANG" in fields["port_of_loading"]["raw"]
    assert "ROTTERDAM" in fields["port_of_discharge"]["raw"]
    assert "VISION INTERNATIONAL" in fields["consignee"]["raw"]


def test_compare_realistic_forms_catches_only_real_error(tmp_path):
    ref_pdf = tmp_path / "ref.pdf"
    tgt_pdf = tmp_path / "tgt.pdf"
    make_form(ref_pdf, "BOOKING CONFIRMATION", VALUES)
    tgt_values = dict(VALUES, container="CSLU6072846", gw="26557.680 KGS")
    make_form(tgt_pdf, "DRAFT BILL OF LADING", tgt_values)

    ref = _extract_merged(ref_pdf, "ref.pdf")
    tgt = _extract_merged(tgt_pdf, "tgt.pdf")
    findings = compare.compare(ref, tgt)

    problems = [f for f in findings if f["is_problem"]]
    assert len(problems) == 1, [
        (f["field_key"], f["match_type"]) for f in problems
    ]
    assert problems[0]["field_key"] == "container_number"
    assert problems[0]["severity"] == "CRITICAL"

    summary = compare.summarize(findings)
    assert summary["overall"] == "FAIL"
    assert summary["critical"] == 1
    # weight formatting difference is recognized as identical (minor note only)
    weight = next(f for f in findings if f["field_key"] == "gross_weight")
    assert weight["match_type"] == "NORMALIZED"
