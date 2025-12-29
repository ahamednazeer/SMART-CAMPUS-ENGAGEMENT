"""
API router for Bonafide Certificate endpoints.
Handles student requests and warden approvals.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_warden
from app.models.user import User, UserRole
from app.models.bonafide import CertificateStatus
from app.services.bonafide_service import BonafideCertificateService
from app.schemas.bonafide import (
    CertificateRequestCreate,
    CertificateApproval,
    CertificateOut,
    CertificateWithDetails,
    CertificateSummary,
    CertificateListOut
)

router = APIRouter(prefix="/certificates", tags=["Bonafide Certificates"])


# ============ Student Endpoints ============

@router.post("/request", response_model=CertificateOut)
async def request_certificate(
    request_data: CertificateRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Student submits a new certificate request"""
    service = BonafideCertificateService(db)
    try:
        certificate = await service.create_request(current_user, request_data)
        return CertificateOut.model_validate(certificate)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/my-requests", response_model=CertificateListOut)
async def get_my_certificates(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current student's certificate requests"""
    service = BonafideCertificateService(db)
    certificates, total = await service.get_student_certificates(
        current_user.id, page, page_size
    )
    return CertificateListOut(
        certificates=certificates,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/my-summary", response_model=CertificateSummary)
async def get_my_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current student's certificate summary"""
    service = BonafideCertificateService(db)
    return await service.get_student_summary(current_user.id)


@router.get("/{certificate_id}", response_model=CertificateOut)
async def get_certificate(
    certificate_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get certificate details"""
    service = BonafideCertificateService(db)
    certificate = await service.repo.get_by_id(certificate_id)
    if not certificate:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    # Check ownership (students can only see their own, wardens can see their hostel's)
    if certificate.student_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.WARDEN]:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    return CertificateOut.model_validate(certificate)


@router.post("/{certificate_id}/download")
async def download_certificate(
    certificate_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get approved certificate for download - returns certificate data for PDF generation"""
    service = BonafideCertificateService(db)
    try:
        certificate = await service.get_certificate_for_download(
            certificate_id, current_user.id
        )
        if not certificate:
            raise HTTPException(status_code=404, detail="Certificate not found")
        
        # Return certificate data with student and hostel info for PDF generation
        from app.repositories.hostel_repository import HostelRepository
        hostel_repo = HostelRepository(db)
        hostel_info = await hostel_repo.get_student_hostel_info(current_user.id)
        
        return {
            "certificate": CertificateOut.model_validate(certificate),
            "student": {
                "name": f"{current_user.first_name} {current_user.last_name or ''}",
                "register_number": current_user.register_number,
                "department": current_user.department,
                "email": current_user.email
            },
            "hostel": {
                "name": hostel_info.get("hostel_name") if hostel_info else None,
                "room_number": hostel_info.get("room_number") if hostel_info else None,
                "warden_name": hostel_info.get("warden_name") if hostel_info else None
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============ Warden Endpoints ============


@router.get("/warden/pending", response_model=list[CertificateWithDetails])
async def get_pending_certificates(
    current_user: User = Depends(require_warden),
    db: AsyncSession = Depends(get_db)
):
    """Get pending certificate requests for warden's hostel"""
    service = BonafideCertificateService(db)
    return await service.get_pending_for_warden(current_user.id)


@router.get("/warden/all", response_model=CertificateListOut)
async def get_all_hostel_certificates(
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(require_warden),
    db: AsyncSession = Depends(get_db)
):
    """Get all certificates for warden's hostel with optional status filter"""
    service = BonafideCertificateService(db)
    
    # Parse status if provided
    cert_status = None
    if status:
        try:
            cert_status = CertificateStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    certificates, total = await service.get_hostel_certificates(
        current_user.id, cert_status, page, page_size
    )
    return {
        "certificates": certificates,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/warden/{certificate_id}/approve", response_model=CertificateOut)
async def approve_certificate(
    certificate_id: int,
    current_user: User = Depends(require_warden),
    db: AsyncSession = Depends(get_db)
):
    """Approve a certificate request"""
    service = BonafideCertificateService(db)
    try:
        result = await service.approve_certificate(certificate_id, current_user.id)
        if not result:
            raise HTTPException(status_code=404, detail="Certificate not found")
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/warden/{certificate_id}/reject", response_model=CertificateOut)
async def reject_certificate(
    certificate_id: int,
    rejection_data: CertificateApproval,
    current_user: User = Depends(require_warden),
    db: AsyncSession = Depends(get_db)
):
    """Reject a certificate request"""
    if rejection_data.approved:
        raise HTTPException(status_code=400, detail="Use approve endpoint for approval")
    
    service = BonafideCertificateService(db)
    try:
        result = await service.reject_certificate(
            certificate_id,
            current_user.id,
            rejection_data.rejection_reason or "No reason provided"
        )
        if not result:
            raise HTTPException(status_code=404, detail="Certificate not found")
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============ Admin Endpoints ============

from app.core.dependencies import require_admin

@router.get("/admin/pending", response_model=list[CertificateWithDetails])
async def get_admin_pending_certificates(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get pending certificate requests that require admin approval"""
    service = BonafideCertificateService(db)
    return await service.get_pending_for_admin()


@router.post("/admin/{certificate_id}/approve", response_model=CertificateOut)
async def admin_approve_certificate(
    certificate_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Approve a certificate request (admin)"""
    service = BonafideCertificateService(db)
    try:
        result = await service.approve_certificate_admin(certificate_id, current_user.id)
        if not result:
            raise HTTPException(status_code=404, detail="Certificate not found")
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/admin/{certificate_id}/reject", response_model=CertificateOut)
async def admin_reject_certificate(
    certificate_id: int,
    rejection_data: CertificateApproval,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Reject a certificate request (admin)"""
    if rejection_data.approved:
        raise HTTPException(status_code=400, detail="Use approve endpoint for approval")
    
    service = BonafideCertificateService(db)
    try:
        result = await service.reject_certificate_admin(
            certificate_id,
            current_user.id,
            rejection_data.rejection_reason or "No reason provided"
        )
        if not result:
            raise HTTPException(status_code=404, detail="Certificate not found")
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

