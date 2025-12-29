"""
Repository for Bonafide Certificate database operations.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.bonafide import BonafideCertificate, CertificateStatus, ApproverType
from app.models.hostel import Hostel, HostelAssignment
from app.models.user import User


class BonafideCertificateRepository:
    """Repository for bonafide certificate CRUD operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, certificate: BonafideCertificate) -> BonafideCertificate:
        """Create a new certificate request"""
        self.db.add(certificate)
        await self.db.commit()
        await self.db.refresh(certificate)
        return certificate

    async def get_by_id(self, certificate_id: int) -> Optional[BonafideCertificate]:
        """Get certificate by ID"""
        result = await self.db.execute(
            select(BonafideCertificate).where(BonafideCertificate.id == certificate_id)
        )
        return result.scalar_one_or_none()

    async def get_by_student(
        self,
        student_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[BonafideCertificate], int]:
        """Get all certificates for a student with pagination"""
        # Count total
        count_result = await self.db.execute(
            select(func.count(BonafideCertificate.id))
            .where(BonafideCertificate.student_id == student_id)
        )
        total = count_result.scalar() or 0

        # Get paginated results
        offset = (page - 1) * page_size
        result = await self.db.execute(
            select(BonafideCertificate)
            .where(BonafideCertificate.student_id == student_id)
            .order_by(BonafideCertificate.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        certificates = result.scalars().all()
        return list(certificates), total

    async def get_by_hostel(
        self,
        hostel_id: int,
        status: Optional[CertificateStatus] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[BonafideCertificate], int]:
        """Get all certificates for a hostel with optional status filter"""
        query = select(BonafideCertificate).where(BonafideCertificate.hostel_id == hostel_id)
        
        if status:
            query = query.where(BonafideCertificate.status == status)

        # Count total
        count_result = await self.db.execute(
            select(func.count(BonafideCertificate.id))
            .where(BonafideCertificate.hostel_id == hostel_id)
            .where(BonafideCertificate.status == status if status else True)
        )
        total = count_result.scalar() or 0

        # Get paginated results
        offset = (page - 1) * page_size
        result = await self.db.execute(
            query.order_by(BonafideCertificate.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        certificates = result.scalars().all()
        return list(certificates), total

    async def get_pending_for_hostel(self, hostel_id: int) -> List[BonafideCertificate]:
        """Get all pending certificates for a hostel"""
        result = await self.db.execute(
            select(BonafideCertificate)
            .where(BonafideCertificate.hostel_id == hostel_id)
            .where(BonafideCertificate.status.in_([
                CertificateStatus.SUBMITTED,
                CertificateStatus.UNDER_REVIEW
            ]))
            .order_by(BonafideCertificate.created_at.asc())
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        certificate_id: int,
        status: CertificateStatus,
        reviewer_id: Optional[int] = None,
        rejection_reason: Optional[str] = None,
        certificate_number: Optional[str] = None
    ) -> Optional[BonafideCertificate]:
        """Update certificate status"""
        certificate = await self.get_by_id(certificate_id)
        if not certificate:
            return None

        certificate.status = status
        if reviewer_id:
            certificate.reviewed_by = reviewer_id
            certificate.reviewed_at = datetime.utcnow()
        if rejection_reason:
            certificate.rejection_reason = rejection_reason
        if certificate_number:
            certificate.certificate_number = certificate_number
        
        certificate.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(certificate)
        return certificate

    async def increment_download(self, certificate_id: int) -> Optional[BonafideCertificate]:
        """Increment download count"""
        certificate = await self.get_by_id(certificate_id)
        if not certificate:
            return None

        certificate.download_count += 1
        certificate.last_downloaded_at = datetime.utcnow()
        if certificate.status == CertificateStatus.APPROVED:
            certificate.status = CertificateStatus.DOWNLOADED
        
        await self.db.commit()
        await self.db.refresh(certificate)
        return certificate

    async def generate_certificate_number(self, hostel_id: int) -> str:
        """Generate unique certificate number"""
        year = datetime.utcnow().year
        # Count certificates for this hostel this year
        count_result = await self.db.execute(
            select(func.count(BonafideCertificate.id))
            .where(BonafideCertificate.hostel_id == hostel_id)
            .where(BonafideCertificate.certificate_number.isnot(None))
            .where(func.extract('year', BonafideCertificate.created_at) == year)
        )
        count = (count_result.scalar() or 0) + 1
        return f"BC-{year}-{hostel_id:03d}-{count:04d}"

    async def get_student_summary(self, student_id: int) -> dict:
        """Get summary stats for a student"""
        result = await self.db.execute(
            select(
                BonafideCertificate.status,
                func.count(BonafideCertificate.id)
            )
            .where(BonafideCertificate.student_id == student_id)
            .group_by(BonafideCertificate.status)
        )
        rows = result.all()
        
        summary = {
            "total_requests": 0,
            "pending_count": 0,
            "approved_count": 0,
            "rejected_count": 0,
            "downloaded_count": 0
        }
        
        for status, count in rows:
            summary["total_requests"] += count
            if status in [CertificateStatus.SUBMITTED, CertificateStatus.UNDER_REVIEW]:
                summary["pending_count"] += count
            elif status == CertificateStatus.APPROVED:
                summary["approved_count"] += count
            elif status == CertificateStatus.REJECTED:
                summary["rejected_count"] += count
            elif status == CertificateStatus.DOWNLOADED:
                summary["downloaded_count"] += count
        
        return summary

    async def get_pending_for_admin(self) -> List[BonafideCertificate]:
        """Get all pending certificates that require admin approval"""
        result = await self.db.execute(
            select(BonafideCertificate)
            .where(BonafideCertificate.approver_type == ApproverType.ADMIN)
            .where(BonafideCertificate.status.in_([
                CertificateStatus.SUBMITTED,
                CertificateStatus.UNDER_REVIEW
            ]))
            .order_by(BonafideCertificate.created_at.asc())
        )
        return list(result.scalars().all())

