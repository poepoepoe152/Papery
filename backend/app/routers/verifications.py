"""Verification endpoints: create, list/search, detail, status, findings."""
from datetime import date, datetime
from typing import Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Request,
)
from sqlalchemy import or_
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from .. import audit, models, pipeline, schemas
from ..database import get_db
from ..deps import get_current_user, require_active_license, require_roles

router = APIRouter(prefix="/verifications", tags=["verifications"])


# ---------- helpers ----------
def _doc_info(doc: models.Document, include_text: bool = False) -> schemas.DocumentInfo:
    return schemas.DocumentInfo(
        id=doc.id,
        role=doc.role,
        original_name=doc.original_name,
        doc_type=doc.doc_type,
        doc_type_label=pipeline.doc_type_label(doc.doc_type) if doc.doc_type else None,
        doc_type_confidence=float(doc.doc_type_confidence) if doc.doc_type_confidence else None,
        page_count=doc.page_count,
        fields=doc.fields,
        text=(doc.text[:20000] if (include_text and doc.text) else None),
    )


def _finding_info(f: models.Finding) -> schemas.FindingInfo:
    return schemas.FindingInfo(
        id=f.id, field_key=f.field_key, field_label=f.field_label,
        reference_value=f.reference_value, detected_value=f.detected_value,
        match_type=f.match_type, severity=f.severity,
        confidence=float(f.confidence) if f.confidence is not None else None,
        explanation=f.explanation, suggested_fix=f.suggested_fix, status=f.status,
    )


def _summary(v: models.Verification) -> schemas.VerificationSummary:
    doc_types = sorted(
        {pipeline.doc_type_label(d.doc_type) for d in v.documents if d.doc_type and d.role == "TARGET"}
    )
    return schemas.VerificationSummary(
        id=v.id, title=v.title, status=v.status, stage=v.stage,
        overall_result=v.overall_result,
        critical_count=v.critical_count, major_count=v.major_count,
        minor_count=v.minor_count, created_at=v.created_at,
        completed_at=v.completed_at,
        created_by_name=v.creator.full_name if v.creator else None,
        doc_types=doc_types,
    )


def _usage_period(d: date) -> date:
    return d.replace(day=1)


# ---------- create ----------
@router.post("", response_model=schemas.VerificationDetail, status_code=201)
def create_verification(
    body: schemas.VerificationCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: models.User = Depends(require_active_license),
    db: Session = Depends(get_db),
):
    file_ids = list(body.reference_file_ids) + list(body.target_file_ids)
    files = (
        db.query(models.FileObject)
        .filter(
            models.FileObject.id.in_(file_ids),
            models.FileObject.company_id == current_user.company_id,
        )
        .all()
    )
    found = {f.id for f in files}
    missing = [str(fid) for fid in file_ids if fid not in found]
    if missing:
        raise HTTPException(status_code=404, detail=f"Unknown file ids: {missing}")

    # Quota enforcement (documents processed this month). Concurrency-safe:
    # upsert the period row, then lock it for the check + increment so parallel
    # requests cannot double-spend the quota or create duplicate counters.
    lic = (
        db.query(models.License)
        .filter(models.License.company_id == current_user.company_id)
        .order_by(models.License.created_at.desc())
        .first()
    )
    limit = lic.plan.monthly_document_limit if lic and lic.plan else None
    period = _usage_period(date.today())
    n_docs = len(file_ids)

    db.execute(
        pg_insert(models.UsageCounter)
        .values(
            company_id=current_user.company_id,
            period_start=period,
            documents_used=0,
        )
        .on_conflict_do_nothing(constraint="uq_usage_company_period")
    )
    counter = (
        db.query(models.UsageCounter)
        .filter(
            models.UsageCounter.company_id == current_user.company_id,
            models.UsageCounter.period_start == period,
        )
        .with_for_update()
        .one()
    )
    if limit is not None and counter.documents_used + n_docs > limit:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Monthly document limit reached ({counter.documents_used}/{limit}).",
        )
    counter.documents_used += n_docs

    v = models.Verification(
        company_id=current_user.company_id,
        created_by=current_user.id,
        title=body.title,
        status=models.VerificationStatus.QUEUED,
        stage="QUEUED",
    )
    db.add(v)
    db.flush()

    files_by_id = {f.id: f for f in files}
    for fid in body.reference_file_ids:
        f = files_by_id[fid]
        db.add(models.Document(
            verification_id=v.id, file_id=f.id,
            role=models.DocumentRole.REFERENCE, original_name=f.original_name,
        ))
    for fid in body.target_file_ids:
        f = files_by_id[fid]
        db.add(models.Document(
            verification_id=v.id, file_id=f.id,
            role=models.DocumentRole.TARGET, original_name=f.original_name,
        ))

    audit.log(
        db, action="VERIFY_CREATE", user=current_user,
        entity_type="verification", entity_id=v.id, meta={"title": v.title},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(v)

    background_tasks.add_task(pipeline.run_verification, v.id)

    detail = schemas.VerificationDetail(**_summary(v).model_dump())
    detail.documents = [_doc_info(d) for d in v.documents]
    detail.findings = []
    return detail


# ---------- list / search ----------
@router.get("", response_model=list[schemas.VerificationSummary])
def list_verifications(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    q: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    result: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    if not current_user.company_id:
        return []
    query = db.query(models.Verification).filter(
        models.Verification.company_id == current_user.company_id
    )
    # Staff only see their own; Manager/Admin see all company verifications.
    if current_user.role == models.UserRole.STAFF:
        query = query.filter(models.Verification.created_by == current_user.id)
    if q:
        query = query.filter(models.Verification.title.ilike(f"%{q}%"))
    if status_filter:
        query = query.filter(models.Verification.status == status_filter)
    if result:
        query = query.filter(models.Verification.overall_result == result)
    if date_from:
        query = query.filter(models.Verification.created_at >= date_from)
    if date_to:
        query = query.filter(models.Verification.created_at <= datetime.combine(date_to, datetime.max.time()))

    rows = (
        query.order_by(models.Verification.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [_summary(v) for v in rows]


def _get_owned(db, current_user, verification_id) -> models.Verification:
    v = (
        db.query(models.Verification)
        .filter(
            models.Verification.id == verification_id,
            models.Verification.company_id == current_user.company_id,
        )
        .first()
    )
    if v is None:
        raise HTTPException(status_code=404, detail="Verification not found")
    if current_user.role == models.UserRole.STAFF and v.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not permitted")
    return v


# ---------- detail / status ----------
@router.get("/{verification_id}", response_model=schemas.VerificationDetail)
def get_verification(
    verification_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    v = _get_owned(db, current_user, verification_id)
    detail = schemas.VerificationDetail(**_summary(v).model_dump())
    detail.documents = [_doc_info(d, include_text=True) for d in v.documents]
    detail.findings = [
        _finding_info(f)
        for f in sorted(
            v.findings,
            key=lambda x: {"CRITICAL": 0, "MAJOR": 1, "MINOR": 2}.get(x.severity, 3),
        )
    ]
    detail.error_message = v.error_message
    return detail


@router.get("/{verification_id}/status")
def get_status(
    verification_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    v = _get_owned(db, current_user, verification_id)
    return {
        "status": v.status, "stage": v.stage, "overall_result": v.overall_result,
        "critical_count": v.critical_count, "major_count": v.major_count,
        "minor_count": v.minor_count,
    }


# ---------- delete ----------
@router.delete("/{verification_id}", response_model=schemas.MessageResponse)
def delete_verification(
    verification_id: str,
    current_user: models.User = Depends(
        require_roles(models.UserRole.ADMIN, models.UserRole.MANAGER)
    ),
    db: Session = Depends(get_db),
):
    v = (
        db.query(models.Verification)
        .filter(
            models.Verification.id == verification_id,
            models.Verification.company_id == current_user.company_id,
        )
        .first()
    )
    if v is None:
        raise HTTPException(status_code=404, detail="Verification not found")
    db.delete(v)
    audit.log(db, action="VERIFY_DELETE", user=current_user,
              entity_type="verification", entity_id=verification_id)
    db.commit()
    return schemas.MessageResponse(message="Deleted")
