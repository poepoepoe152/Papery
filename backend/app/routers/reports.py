"""Report download endpoints (PDF / Excel / JSON)."""
import io

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .. import audit, models
from ..database import get_db
from ..deps import get_current_user
from ..engines import reports

router = APIRouter(tags=["reports"])


@router.get("/verifications/{verification_id}/report")
def download_report(
    verification_id: str,
    fmt: str = Query("PDF", pattern="^(?i)(pdf|xlsx|json)$"),
    current_user: models.User = Depends(get_current_user),
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
    if current_user.role == models.UserRole.STAFF and v.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not permitted")
    if v.status != models.VerificationStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="Verification not completed yet")

    documents = sorted(v.documents, key=lambda d: d.role)
    findings = sorted(
        v.findings,
        key=lambda x: {"CRITICAL": 0, "MAJOR": 1, "MINOR": 2}.get(x.severity, 3),
    )
    data, ext, mime = reports.build_report(fmt, v, documents, findings)

    audit.log(db, action="REPORT_DOWNLOAD", user=current_user,
              entity_type="verification", entity_id=v.id, meta={"format": ext})
    db.commit()

    safe_title = "".join(c if c.isalnum() else "_" for c in (v.title or "report"))[:40]
    filename = f"papery_{safe_title}.{ext}"
    return StreamingResponse(
        io.BytesIO(data),
        media_type=mime,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
