"""Verification pipeline orchestration.

Runs in a background task (Celery/Redis is the production target). Stages:
ingest text -> classify -> extract fields -> compare -> summarize.
Each verification owns its own DB session so it is safe off the request thread.
"""
from datetime import datetime, timezone

from . import models
from .database import SessionLocal
from .doctypes import DOC_TYPE_LABELS
from .engines import classify, compare, extract_fields, extract_spatial, text_extract


def _process_document(doc: models.Document) -> None:
    file = doc.file
    if file is None:
        doc.text = ""
        doc.fields = {}
        return
    extracted = text_extract.extract_text(file.storage_path, doc.original_name or "")
    text = extracted["text"]
    doc_type, conf = classify.classify(text)

    # Line-based extraction first, then layout-aware (word coordinates) results
    # override where they are at least as confident — critical for the
    # multi-column boxed forms used by carriers.
    fields = extract_fields.extract_fields(text)
    for key, value in extract_spatial.extract_fields_spatial(
        extracted.get("words") or []
    ).items():
        current = fields.get(key)
        if current is None or value["confidence"] >= current["confidence"]:
            fields[key] = value

    doc.text = text[:200_000]  # cap stored text
    doc.page_count = extracted["page_count"]
    doc.doc_type = doc_type
    doc.doc_type_confidence = conf
    doc.fields = fields


def run_verification(verification_id) -> None:
    db = SessionLocal()
    try:
        v = db.query(models.Verification).filter(
            models.Verification.id == verification_id
        ).first()
        if v is None:
            return

        v.status = models.VerificationStatus.PROCESSING
        v.stage = "EXTRACTING"
        db.commit()

        documents = (
            db.query(models.Document)
            .filter(models.Document.verification_id == v.id)
            .all()
        )

        # 1) text + classify + extract for each document
        for doc in documents:
            _process_document(doc)
        db.commit()

        references = [d for d in documents if d.role == models.DocumentRole.REFERENCE]
        targets = [d for d in documents if d.role == models.DocumentRole.TARGET]

        # Merge reference fields (first non-empty wins per field).
        merged_ref: dict = {}
        for ref in references:
            for k, val in (ref.fields or {}).items():
                merged_ref.setdefault(k, val)

        v.stage = "COMPARING"
        db.commit()

        all_findings: list[dict] = []
        for tgt in targets:
            results = compare.compare(merged_ref, tgt.fields or {})
            all_findings.extend(results)

        # Persist only the notable findings (problems + formatting notes).
        persisted = []
        for f in all_findings:
            if f["match_type"] == "EXACT":
                continue
            finding = models.Finding(
                verification_id=v.id,
                field_key=f["field_key"],
                field_label=f["field_label"],
                reference_value=f["reference_value"],
                detected_value=f["detected_value"],
                match_type=f["match_type"],
                severity=f["severity"],
                confidence=f["confidence"],
                used_llm=f["used_llm"],
                explanation=f["explanation"],
                suggested_fix=f["suggested_fix"],
                status=models.FindingStatus.OPEN,
            )
            db.add(finding)
            persisted.append(f)

        summary = compare.summarize(all_findings)
        v.critical_count = summary["critical"]
        v.major_count = summary["major"]
        v.minor_count = summary["minor"]
        v.overall_result = summary["overall"]
        v.status = models.VerificationStatus.COMPLETED
        v.stage = "DONE"
        v.completed_at = datetime.now(timezone.utc)
        db.commit()

        # Notify on completion / critical errors.
        _notify(db, v)
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        v = db.query(models.Verification).filter(
            models.Verification.id == verification_id
        ).first()
        if v is not None:
            v.status = models.VerificationStatus.FAILED
            v.stage = "FAILED"
            v.error_message = str(exc)[:1000]
            db.commit()
        print(f"[pipeline] verification {verification_id} failed: {exc}")
    finally:
        db.close()


def _notify(db, v) -> None:
    # Lightweight: audit entries serve as the notification feed for now.
    from . import audit

    audit.log(
        db,
        action="VERIFICATION_COMPLETED",
        company_id=v.company_id,
        entity_type="verification",
        entity_id=v.id,
        meta={"result": v.overall_result, "critical": v.critical_count},
    )
    db.commit()


def doc_type_label(doc_type: str) -> str:
    return DOC_TYPE_LABELS.get(doc_type or "UNKNOWN", doc_type or "Unknown")
