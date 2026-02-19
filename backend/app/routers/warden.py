"""API router for warden operations (Outpass approval, hostel oversight)."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from io import BytesIO
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import require_warden
from app.models.user import User, UserRole, Gender
from app.models.outpass import OutpassStatus
from app.services.outpass_service import OutpassService
from app.services.hostel_service import HostelService
from app.schemas.outpass import OutpassOut, OutpassWithStudentDetails
from app.schemas.hostel import (
    HostelWithDetails, HostelAssignmentWithDetails, HostelStudentProfile,
    HostelAutoAssignPreview, HostelAutoAssignConfirmRequest, HostelAutoAssignResult
)


router = APIRouter(prefix="/warden", tags=["Warden"])


def _filter_assignments(
    assignments: list[HostelAssignmentWithDetails],
    department: str | None,
    study_year: int | None,
    degree: str | None,
    gender: Gender | None,
    batch: str | None,
) -> list[HostelAssignmentWithDetails]:
    filtered = []
    for item in assignments:
        if department and item.student_department != department:
            continue
        if study_year and item.student_study_year != study_year:
            continue
        if degree and item.student_degree != degree:
            continue
        if batch and item.student_batch != batch:
            continue
        if gender:
            item_gender = item.student_gender.value if hasattr(item.student_gender, "value") else item.student_gender
            if item_gender != gender.value:
                continue
        filtered.append(item)
    return filtered


def _build_export_rows(assignments: list[HostelAssignmentWithDetails]) -> list[dict[str, str]]:
    rows = []
    for item in assignments:
        gender_value = item.student_gender.value if hasattr(item.student_gender, "value") else item.student_gender
        rows.append({
            "Name": item.student_name or "",
            "Department": item.student_department or "",
            "Year": str(item.student_study_year or ""),
            "Gender": str(gender_value or ""),
        })
    return rows


def _generate_excel(rows: list[dict[str, str]]) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Font

    wb = Workbook()
    ws = wb.active
    ws.title = "Assigned"
    headers = ["Name", "Department", "Year", "Gender"]
    ws.append(headers)
    for row in rows:
        ws.append([row.get(h, "") for h in headers])

    for cell in ws[1]:
        cell.font = Font(bold=True)

    ws.column_dimensions["A"].width = 28
    ws.column_dimensions["B"].width = 18
    ws.column_dimensions["C"].width = 8
    ws.column_dimensions["D"].width = 10

    output = BytesIO()
    wb.save(output)
    return output.getvalue()


def _generate_pdf(rows: list[dict[str, str]]) -> bytes:
    import fitz

    def clip(text: str, max_len: int) -> str:
        if len(text) <= max_len:
            return text
        return text[: max_len - 3] + "..."

    doc = fitz.open()
    page = doc.new_page()
    font_size = 10
    line_height = 14
    x_positions = [40, 220, 340, 420]
    headers = ["Name", "Department", "Year", "Gender"]

    def draw_header(p, y_pos):
        for i, header in enumerate(headers):
            p.insert_text((x_positions[i], y_pos), header, fontsize=font_size, fontname="helv")
        return y_pos + line_height

    y = 40
    y = draw_header(page, y)

    for row in rows:
        if y > page.rect.height - 40:
            page = doc.new_page()
            y = draw_header(page, 40)
        values = [
            clip(row.get("Name", ""), 28),
            clip(row.get("Department", ""), 14),
            clip(row.get("Year", ""), 6),
            clip(row.get("Gender", ""), 8),
        ]
        for i, value in enumerate(values):
            page.insert_text((x_positions[i], y), value, fontsize=font_size, fontname="helv")
        y += line_height

    return doc.tobytes()


async def _resolve_warden_hostel(
    hostel_service: HostelService,
    warden_id: int,
    hostel_id: int | None = None,
):
    """Resolve selected hostel for a warden, defaulting to latest assigned."""
    if hostel_id is None:
        return await hostel_service.get_warden_hostel(warden_id)
    hostels = await hostel_service.get_warden_hostels(warden_id)
    for hostel in hostels:
        if hostel.id == hostel_id:
            return hostel
    return None


# ==================== HOSTEL INFO ====================

@router.get("/hostel", response_model=HostelWithDetails | None)
async def get_my_hostel(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_warden)],
    hostel_id: int | None = Query(None)
):
    """Get the hostel managed by the current warden."""
    service = HostelService(db)
    hostel = await _resolve_warden_hostel(service, current_user.id, hostel_id)
    
    if not hostel:
        return None
    
    # Get details
    hostels = await service.list_hostels()
    for h in hostels:
        if h.id == hostel.id:
            return h
    
    return None


@router.get("/hostels", response_model=list[HostelWithDetails])
async def get_my_hostels(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_warden)]
):
    """Get all hostels managed by the current warden."""
    service = HostelService(db)
    assigned = await service.get_warden_hostels(current_user.id)
    if not assigned:
        return []

    assigned_ids = {hostel.id for hostel in assigned}
    all_hostels = await service.list_hostels()
    return [hostel for hostel in all_hostels if hostel.id in assigned_ids]


@router.get("/students", response_model=list[HostelAssignmentWithDetails])
async def get_hostel_students(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_warden)],
    hostel_id: int | None = Query(None)
):
    """Get all students in the warden's hostel."""
    hostel_service = HostelService(db)
    hostel = await _resolve_warden_hostel(hostel_service, current_user.id, hostel_id)
    
    if not hostel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not assigned as warden to any hostel"
        )
    
    return await hostel_service.get_hostel_students(hostel.id)


@router.get("/hostel/unassigned-students", response_model=list[HostelStudentProfile])
async def get_unassigned_hostel_students(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_warden)],
    hostel_id: int | None = Query(None)
):
    """Get unassigned hosteller students eligible for the warden's hostel."""
    hostel_service = HostelService(db)
    hostel = await _resolve_warden_hostel(hostel_service, current_user.id, hostel_id)

    if not hostel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not assigned as warden to any hostel"
        )

    try:
        return await hostel_service.get_unassigned_hostellers_for_hostel(hostel.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/hostel/auto-assign", response_model=HostelAutoAssignPreview)
async def preview_auto_assign_hostel_students(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_warden)],
    hostel_id: int | None = Query(None),
    department: str | None = Query(None),
    study_year: int | None = Query(None, ge=1, le=8),
    degree: str | None = Query(None),
    gender: Gender | None = Query(None),
    batch: str | None = Query(None),
    limit: int | None = Query(None, ge=1, le=1000),
    strategy: str = Query("fill"),
):
    """Preview auto-assign recommendations for warden's hostel."""
    hostel_service = HostelService(db)
    hostel = await _resolve_warden_hostel(hostel_service, current_user.id, hostel_id)

    if not hostel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not assigned as warden to any hostel"
        )

    if strategy not in ["fill", "spread"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid strategy")

    try:
        return await hostel_service.recommend_assignments_for_hostel(
            hostel.id,
            department=department,
            study_year=study_year,
            degree=degree,
            gender=gender,
            batch=batch,
            limit=limit,
            strategy=strategy,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/hostel/auto-assign/confirm", response_model=HostelAutoAssignResult)
async def confirm_auto_assign_hostel_students(
    payload: HostelAutoAssignConfirmRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_warden)],
    hostel_id: int | None = Query(None)
):
    """Confirm and apply auto-assign recommendations."""
    hostel_service = HostelService(db)
    hostel = await _resolve_warden_hostel(hostel_service, current_user.id, hostel_id)

    if not hostel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not assigned as warden to any hostel"
        )

    try:
        return await hostel_service.confirm_auto_assignments(
            hostel.id,
            payload.assignments,
            created_by=current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/hostel/auto-assign/latest", response_model=HostelAutoAssignResult | None)
async def get_latest_auto_assign_result(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_warden)],
    hostel_id: int | None = Query(None)
):
    """Get latest auto-assign result for warden's hostel."""
    hostel_service = HostelService(db)
    hostel = await _resolve_warden_hostel(hostel_service, current_user.id, hostel_id)

    if not hostel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not assigned as warden to any hostel"
        )

    return await hostel_service.get_latest_auto_assign_result(hostel.id)


@router.get("/hostel/assignments/export")
async def export_hostel_assignments(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_warden)],
    hostel_id: int | None = Query(None),
    format: str = Query("excel"),
    department: str | None = Query(None),
    study_year: int | None = Query(None, ge=1, le=8),
    degree: str | None = Query(None),
    gender: Gender | None = Query(None),
    batch: str | None = Query(None),
):
    """Export assigned hostel students (warden only)."""
    hostel_service = HostelService(db)
    hostel = await _resolve_warden_hostel(hostel_service, current_user.id, hostel_id)

    if not hostel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not assigned as warden to any hostel"
        )

    fmt = format.lower()
    if fmt not in ["excel", "pdf"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid format")

    assignments = await hostel_service.get_hostel_students(hostel.id)
    filtered = _filter_assignments(assignments, department, study_year, degree, gender, batch)
    rows = _build_export_rows(filtered)

    if fmt == "excel":
        content = _generate_excel(rows)
        filename = f"hostel_assignments_{hostel.id}.xlsx"
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        content = _generate_pdf(rows)
        filename = f"hostel_assignments_{hostel.id}.pdf"
        media_type = "application/pdf"

    return StreamingResponse(
        BytesIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# ==================== OUTPASS MANAGEMENT ====================

@router.get("/outpass/pending", response_model=list[OutpassWithStudentDetails])
async def get_pending_outpasses(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_warden)],
    hostel_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """Get pending outpass requests for approval."""
    service = OutpassService(db)
    try:
        outpasses, total = await service.get_pending_for_warden(
            current_user.id, hostel_id, page, page_size
        )
        return outpasses
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/outpass/all", response_model=list[OutpassWithStudentDetails])
async def get_all_outpasses(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_warden)],
    hostel_id: int | None = Query(None),
    status_filter: OutpassStatus | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """Get all outpass requests for the hostel."""
    service = OutpassService(db)
    try:
        outpasses, total = await service.get_all_hostel_outpasses(
            current_user.id, hostel_id, status_filter, page, page_size
        )
        return outpasses
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/outpass/student/{student_id}", response_model=list[OutpassOut])
async def get_student_outpass_history(
    student_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_warden)]
):
    """Get outpass history for a specific student."""
    service = OutpassService(db)
    try:
        return await service.get_outpass_history_for_student(current_user.id, student_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


class ApproveRejectRequest(BaseModel):
    """Request body for approval/rejection."""
    rejection_reason: str | None = None


@router.post("/outpass/{outpass_id}/approve", response_model=OutpassOut)
async def approve_outpass(
    outpass_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_warden)]
):
    """Approve an outpass request."""
    service = OutpassService(db)
    try:
        outpass = await service.approve_outpass(outpass_id, current_user.id)
        return OutpassOut.model_validate(outpass)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/outpass/{outpass_id}/reject", response_model=OutpassOut)
async def reject_outpass(
    outpass_id: int,
    body: ApproveRejectRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_warden)]
):
    """Reject an outpass request."""
    if not body.rejection_reason:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rejection reason is required"
        )
    
    service = OutpassService(db)
    try:
        outpass = await service.reject_outpass(
            outpass_id, current_user.id, body.rejection_reason
        )
        return OutpassOut.model_validate(outpass)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
