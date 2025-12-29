"""
Service layer for Bonafide Certificate business logic.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bonafide import BonafideCertificate, CertificateType, CertificatePurpose, CertificateStatus, ApproverType
from app.models.hostel import HostelAssignment
from app.models.user import User, StudentCategory
from app.repositories.bonafide_repository import BonafideCertificateRepository
from app.repositories.hostel_repository import HostelRepository
from app.schemas.bonafide import (
    CertificateRequestCreate,
    CertificateOut,
    CertificateWithDetails,
    CertificateSummary
)


class BonafideCertificateService:
    """Service for bonafide certificate business logic"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = BonafideCertificateRepository(db)
        self.hostel_repo = HostelRepository(db)

    async def validate_student_eligibility(self, student: User) -> tuple[bool, str, Optional[dict]]:
        """
        Validate if student is eligible to request certificate.
        Returns: (is_eligible, message, hostel_info)
        """
        # Check if student is a hosteller
        if student.student_category != StudentCategory.HOSTELLER:
            return False, "Only hostellers can request bonafide certificates", None

        # Check if student has active hostel assignment
        hostel_info = await self.hostel_repo.get_student_hostel_info(student.id)
        if not hostel_info or not hostel_info.get("is_assigned"):
            return False, "You must have an active hostel assignment", None

        return True, "Eligible", hostel_info

    async def create_request(
        self,
        student: User,
        request_data: CertificateRequestCreate
    ) -> BonafideCertificate:
        """Create a new certificate request"""
        is_general = request_data.certificate_type == CertificateType.GENERAL_BONAFIDE
        
        hostel_id = None
        room_number = None
        approver_type = ApproverType.ADMIN if is_general else ApproverType.WARDEN
        
        # For hostel-specific certificates, validate hosteller eligibility
        if not is_general:
            is_eligible, message, hostel_info = await self.validate_student_eligibility(student)
            if not is_eligible:
                raise ValueError(message)
            hostel_id = hostel_info.get("hostel_id")
            room_number = hostel_info.get("room_number")

        # Create certificate request
        certificate = BonafideCertificate(
            student_id=student.id,
            hostel_id=hostel_id,
            room_number=room_number,
            certificate_type=request_data.certificate_type,
            purpose=request_data.purpose,
            purpose_details=request_data.purpose_details,
            status=CertificateStatus.SUBMITTED,
            approver_type=approver_type
        )

        return await self.repo.create(certificate)

    async def get_student_certificates(
        self,
        student_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[CertificateOut], int]:
        """Get all certificates for a student"""
        certificates, total = await self.repo.get_by_student(student_id, page, page_size)
        return [CertificateOut.model_validate(c) for c in certificates], total

    async def get_student_summary(self, student_id: int) -> CertificateSummary:
        """Get summary stats for a student"""
        summary = await self.repo.get_student_summary(student_id)
        return CertificateSummary(**summary)

    async def get_pending_for_warden(self, warden_id: int) -> List[CertificateWithDetails]:
        """Get pending certificate requests for warden's hostel"""
        # Get warden's hostel
        hostel = await self.hostel_repo.get_warden_hostel(warden_id)
        if not hostel:
            return []

        certificates = await self.repo.get_pending_for_hostel(hostel.id)
        return await self._enrich_certificates(certificates)

    async def get_hostel_certificates(
        self,
        warden_id: int,
        status: Optional[CertificateStatus] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[CertificateWithDetails], int]:
        """Get all certificates for warden's hostel"""
        # Get warden's hostel
        hostel = await self.hostel_repo.get_warden_hostel(warden_id)
        if not hostel:
            return [], 0

        certificates, total = await self.repo.get_by_hostel(hostel.id, status, page, page_size)
        enriched = await self._enrich_certificates(certificates)
        return enriched, total

    async def approve_certificate(
        self,
        certificate_id: int,
        warden_id: int
    ) -> Optional[CertificateOut]:
        """Approve a certificate request"""
        certificate = await self.repo.get_by_id(certificate_id)
        if not certificate:
            raise ValueError("Certificate not found")

        # Verify warden owns the hostel
        hostel = await self.hostel_repo.get_warden_hostel(warden_id)
        if not hostel or hostel.id != certificate.hostel_id:
            raise ValueError("Unauthorized to approve this certificate")

        # Check status
        if certificate.status not in [CertificateStatus.SUBMITTED, CertificateStatus.UNDER_REVIEW]:
            raise ValueError(f"Cannot approve certificate with status {certificate.status}")

        # Generate certificate number
        cert_number = await self.repo.generate_certificate_number(hostel.id)

        # Update status
        updated = await self.repo.update_status(
            certificate_id=certificate_id,
            status=CertificateStatus.APPROVED,
            reviewer_id=warden_id,
            certificate_number=cert_number
        )

        return CertificateOut.model_validate(updated) if updated else None

    async def reject_certificate(
        self,
        certificate_id: int,
        warden_id: int,
        rejection_reason: str
    ) -> Optional[CertificateOut]:
        """Reject a certificate request"""
        certificate = await self.repo.get_by_id(certificate_id)
        if not certificate:
            raise ValueError("Certificate not found")

        # Verify warden owns the hostel
        hostel = await self.hostel_repo.get_warden_hostel(warden_id)
        if not hostel or hostel.id != certificate.hostel_id:
            raise ValueError("Unauthorized to reject this certificate")

        # Check status
        if certificate.status not in [CertificateStatus.SUBMITTED, CertificateStatus.UNDER_REVIEW]:
            raise ValueError(f"Cannot reject certificate with status {certificate.status}")

        # Update status
        updated = await self.repo.update_status(
            certificate_id=certificate_id,
            status=CertificateStatus.REJECTED,
            reviewer_id=warden_id,
            rejection_reason=rejection_reason
        )

        return CertificateOut.model_validate(updated) if updated else None

    async def get_certificate_for_download(
        self,
        certificate_id: int,
        student_id: int
    ) -> Optional[BonafideCertificate]:
        """Get approved certificate for download"""
        certificate = await self.repo.get_by_id(certificate_id)
        if not certificate:
            return None

        # Verify ownership
        if certificate.student_id != student_id:
            raise ValueError("Unauthorized to download this certificate")

        # Check status
        if certificate.status not in [CertificateStatus.APPROVED, CertificateStatus.DOWNLOADED]:
            raise ValueError("Certificate not approved yet")

        # Increment download count
        await self.repo.increment_download(certificate_id)
        return certificate

    async def _enrich_certificates(
        self,
        certificates: List[BonafideCertificate]
    ) -> List[CertificateWithDetails]:
        """Add student and hostel details to certificates"""
        enriched = []
        for cert in certificates:
            # Get student info
            from sqlalchemy import select
            student_result = await self.db.execute(
                select(User).where(User.id == cert.student_id)
            )
            student = student_result.scalar_one_or_none()

            # Get hostel info
            hostel = await self.hostel_repo.get_hostel(cert.hostel_id) if cert.hostel_id else None

            cert_dict = {
                **CertificateOut.model_validate(cert).model_dump(),
                "student_name": f"{student.first_name} {student.last_name or ''}" if student else None,
                "student_register_number": student.register_number if student else None,
                "student_department": student.department if student else None,
                "hostel_name": hostel.name if hostel else None
            }
            enriched.append(CertificateWithDetails(**cert_dict))

        return enriched

    # ============ Admin Methods ============

    async def get_pending_for_admin(self) -> List[CertificateWithDetails]:
        """Get pending certificate requests that require admin approval"""
        certificates = await self.repo.get_pending_for_admin()
        return await self._enrich_certificates(certificates)

    async def approve_certificate_admin(
        self,
        certificate_id: int,
        admin_id: int
    ) -> Optional[CertificateOut]:
        """Approve a certificate request (admin)"""
        certificate = await self.repo.get_by_id(certificate_id)
        if not certificate:
            raise ValueError("Certificate not found")

        # Verify this is an admin-approvable certificate
        if certificate.approver_type != ApproverType.ADMIN:
            raise ValueError("This certificate requires warden approval, not admin")

        # Check status
        if certificate.status not in [CertificateStatus.SUBMITTED, CertificateStatus.UNDER_REVIEW]:
            raise ValueError(f"Cannot approve certificate with status {certificate.status}")

        # Generate certificate number
        cert_number = await self.repo.generate_certificate_number(0)  # 0 for admin certs

        # Update status
        updated = await self.repo.update_status(
            certificate_id=certificate_id,
            status=CertificateStatus.APPROVED,
            reviewer_id=admin_id,
            certificate_number=cert_number
        )

        return CertificateOut.model_validate(updated) if updated else None

    async def reject_certificate_admin(
        self,
        certificate_id: int,
        admin_id: int,
        rejection_reason: str
    ) -> Optional[CertificateOut]:
        """Reject a certificate request (admin)"""
        certificate = await self.repo.get_by_id(certificate_id)
        if not certificate:
            raise ValueError("Certificate not found")

        # Verify this is an admin-approvable certificate
        if certificate.approver_type != ApproverType.ADMIN:
            raise ValueError("This certificate requires warden approval, not admin")

        # Check status
        if certificate.status not in [CertificateStatus.SUBMITTED, CertificateStatus.UNDER_REVIEW]:
            raise ValueError(f"Cannot reject certificate with status {certificate.status}")

        # Update status
        updated = await self.repo.update_status(
            certificate_id=certificate_id,
            status=CertificateStatus.REJECTED,
            reviewer_id=admin_id,
            rejection_reason=rejection_reason
        )

        return CertificateOut.model_validate(updated) if updated else None

