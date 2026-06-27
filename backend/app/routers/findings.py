"""Finding actions + learning-mode feedback."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import audit, models, schemas
from ..database import get_db
from ..deps import get_current_user, require_roles

router = APIRouter(tags=["findings"])

_VALID_FINDING_STATUS = {
    models.FindingStatus.ACCEPTED,
    models.FindingStatus.DISMISSED,
    models.FindingStatus.CORRECTED,
    models.FindingStatus.OPEN,
}


@router.patch("/findings/{finding_id}", response_model=schemas.FindingInfo)
def update_finding(
    finding_id: str,
    body: schemas.FindingUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    finding = (
        db.query(models.Finding)
        .join(models.Verification, models.Finding.verification_id == models.Verification.id)
        .filter(
            models.Finding.id == finding_id,
            models.Verification.company_id == current_user.company_id,
        )
        .first()
    )
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found")

    if body.status is not None:
        if body.status not in _VALID_FINDING_STATUS:
            raise HTTPException(status_code=400, detail="Invalid status")
        finding.status = body.status

    # Learning mode: any correction/override is captured as feedback.
    if body.corrected_value is not None or body.status in (
        models.FindingStatus.CORRECTED,
        models.FindingStatus.DISMISSED,
    ):
        db.add(models.Feedback(
            company_id=current_user.company_id,
            finding_id=finding.id,
            field_key=finding.field_key,
            original_value=finding.detected_value,
            corrected_value=body.corrected_value,
            correction_type="VERDICT_OVERRIDE" if body.corrected_value is None else "FIELD_FIX",
            created_by=current_user.id,
            approval_status="PENDING",
        ))

    audit.log(db, action="FINDING_UPDATE", user=current_user,
              entity_type="finding", entity_id=finding.id,
              meta={"status": finding.status})
    db.commit()
    db.refresh(finding)
    return schemas.FindingInfo(
        id=finding.id, field_key=finding.field_key, field_label=finding.field_label,
        reference_value=finding.reference_value, detected_value=finding.detected_value,
        match_type=finding.match_type, severity=finding.severity,
        confidence=float(finding.confidence) if finding.confidence is not None else None,
        explanation=finding.explanation, suggested_fix=finding.suggested_fix,
        status=finding.status,
    )


@router.get("/feedback/pending")
def list_pending_feedback(
    current_user: models.User = Depends(require_roles(models.UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(models.Feedback)
        .filter(
            models.Feedback.company_id == current_user.company_id,
            models.Feedback.approval_status == "PENDING",
        )
        .order_by(models.Feedback.created_at.desc())
        .all()
    )
    return [
        {
            "id": str(r.id), "field_key": r.field_key,
            "original_value": r.original_value, "corrected_value": r.corrected_value,
            "correction_type": r.correction_type, "created_at": r.created_at,
        }
        for r in rows
    ]


@router.patch("/feedback/{feedback_id}", response_model=schemas.MessageResponse)
def review_feedback(
    feedback_id: str,
    approve: bool,
    current_user: models.User = Depends(require_roles(models.UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    fb = (
        db.query(models.Feedback)
        .filter(
            models.Feedback.id == feedback_id,
            models.Feedback.company_id == current_user.company_id,
        )
        .first()
    )
    if fb is None:
        raise HTTPException(status_code=404, detail="Feedback not found")
    fb.approval_status = "APPROVED" if approve else "REJECTED"
    fb.approved_by = current_user.id
    audit.log(db, action="FEEDBACK_REVIEW", user=current_user,
              entity_type="feedback", entity_id=fb.id,
              meta={"approved": approve})
    db.commit()
    return schemas.MessageResponse(message="Updated")
