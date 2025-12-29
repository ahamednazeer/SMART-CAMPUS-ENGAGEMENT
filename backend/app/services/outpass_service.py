"""Service for outpass request business logic."""
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.outpass_repository import OutpassRepository
from app.repositories.hostel_repository import HostelRepository
from app.models.outpass import OutpassRequest, OutpassStatus
from app.models.user import User, UserRole, StudentCategory
from app.schemas.outpass import (
    OutpassCreate, OutpassOut, OutpassApproval,
    OutpassWithStudentDetails, OutpassSummary
)


class OutpassService:
    """Service for outpass operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = OutpassRepository(db)
        self.hostel_repo = HostelRepository(db)

    # ==================== STUDENT OPERATIONS ====================

    async def submit_outpass(self, student_id: int, data: OutpassCreate) -> OutpassRequest:
        """Submit a new outpass request."""
        # Verify student is an active hosteller with assignment
        from sqlalchemy import select
        result = await self.db.execute(select(User).where(User.id == student_id))
        student = result.scalar_one_or_none()
        
        if not student:
            raise ValueError("Student not found")
        
        if not student.is_active:
            raise ValueError("Student account is not active")
        
        if student.student_category != StudentCategory.HOSTELLER:
            raise ValueError("Only hostellers can apply for outpass")
        
        # Check hostel assignment
        assignment = await self.hostel_repo.get_student_assignment(student_id)
        if not assignment:
            raise ValueError("Student is not assigned to any hostel")
        
        # Check for overlapping outpass
        has_overlap = await self.repo.check_overlapping_outpass(
            student_id,
            data.start_datetime,
            data.end_datetime
        )
        if has_overlap:
            raise ValueError("You have an overlapping outpass request for this time period")
        
        # Check monthly limit (configurable - default 4)
        monthly_limit = 4
        now = datetime.utcnow()
        current_month_count = await self.repo.get_monthly_count(student_id, now.year, now.month)
        if current_month_count >= monthly_limit:
            raise ValueError(f"Monthly outpass limit ({monthly_limit}) exceeded")
        
        # Create outpass
        return await self.repo.create_outpass(
            student_id=student_id,
            reason=data.reason,
            destination=data.destination,
            start_datetime=data.start_datetime,
            end_datetime=data.end_datetime,
            emergency_contact=data.emergency_contact
        )

    async def get_student_outpasses(
        self,
        student_id: int,
        status: OutpassStatus | None = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[OutpassOut], int]:
        """Get student's outpass history."""
        skip = (page - 1) * page_size
        outpasses, total = await self.repo.get_student_outpasses(
            student_id, status, skip, page_size
        )
        return [OutpassOut.model_validate(o) for o in outpasses], total

    async def get_outpass_details(self, outpass_id: int, student_id: int) -> OutpassOut:
        """Get outpass details (student can only see their own)."""
        outpass = await self.repo.get_outpass(outpass_id)
        if not outpass:
            raise ValueError("Outpass request not found")
        
        if outpass.student_id != student_id:
            raise PermissionError("You can only view your own outpass requests")
        
        return OutpassOut.model_validate(outpass)

    async def get_student_summary(self, student_id: int) -> OutpassSummary:
        """Get summary of student's outpass usage."""
        summary = await self.repo.get_student_summary(student_id)
        return OutpassSummary(**summary)

    # ==================== WARDEN OPERATIONS ====================

    async def get_pending_for_warden(
        self,
        warden_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[OutpassWithStudentDetails], int]:
        """Get pending outpass requests for warden's hostel."""
        # Get warden's hostel
        hostel = await self.hostel_repo.get_warden_hostel(warden_id)
        if not hostel:
            raise ValueError("You are not assigned as warden to any hostel")
        
        skip = (page - 1) * page_size
        outpasses, total = await self.repo.get_pending_for_hostel(
            hostel.id, skip, page_size
        )
        
        # Enrich with student details
        result = []
        for outpass in outpasses:
            details = await self._enrich_outpass_with_student(outpass)
            result.append(details)
        
        return result, total

    async def get_all_hostel_outpasses(
        self,
        warden_id: int,
        status: OutpassStatus | None = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[OutpassWithStudentDetails], int]:
        """Get all outpass requests for warden's hostel."""
        hostel = await self.hostel_repo.get_warden_hostel(warden_id)
        if not hostel:
            raise ValueError("You are not assigned as warden to any hostel")
        
        # Get student IDs from hostel
        from sqlalchemy import select
        from app.models.hostel import HostelAssignment
        
        assignment_result = await self.db.execute(
            select(HostelAssignment.student_id)
            .where(HostelAssignment.hostel_id == hostel.id, HostelAssignment.is_active == True)
        )
        student_ids = [row[0] for row in assignment_result.fetchall()]
        
        if not student_ids:
            return [], 0
        
        # Query outpasses
        from sqlalchemy import func
        
        query = select(OutpassRequest).where(OutpassRequest.student_id.in_(student_ids))
        count_query = select(func.count(OutpassRequest.id)).where(
            OutpassRequest.student_id.in_(student_ids)
        )
        
        if status:
            query = query.where(OutpassRequest.status == status)
            count_query = count_query.where(OutpassRequest.status == status)
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        skip = (page - 1) * page_size
        result = await self.db.execute(
            query.order_by(OutpassRequest.created_at.desc())
            .offset(skip)
            .limit(page_size)
        )
        outpasses = result.scalars().all()
        
        # Enrich with student details
        enriched = []
        for outpass in outpasses:
            details = await self._enrich_outpass_with_student(outpass)
            enriched.append(details)
        
        return enriched, total

    async def approve_outpass(
        self,
        outpass_id: int,
        warden_id: int
    ) -> OutpassRequest:
        """Approve an outpass request."""
        outpass = await self.repo.get_outpass(outpass_id)
        if not outpass:
            raise ValueError("Outpass request not found")
        
        # Verify warden manages the student's hostel
        await self._verify_warden_authority(warden_id, outpass.student_id)
        
        if outpass.status != OutpassStatus.SUBMITTED:
            raise ValueError(f"Cannot approve outpass with status '{outpass.status.value}'")
        
        return await self.repo.update_status(
            outpass_id,
            OutpassStatus.APPROVED,
            warden_id,
            notes="Approved by warden"
        )

    async def reject_outpass(
        self,
        outpass_id: int,
        warden_id: int,
        rejection_reason: str
    ) -> OutpassRequest:
        """Reject an outpass request."""
        outpass = await self.repo.get_outpass(outpass_id)
        if not outpass:
            raise ValueError("Outpass request not found")
        
        # Verify warden manages the student's hostel
        await self._verify_warden_authority(warden_id, outpass.student_id)
        
        if outpass.status != OutpassStatus.SUBMITTED:
            raise ValueError(f"Cannot reject outpass with status '{outpass.status.value}'")
        
        if not rejection_reason or len(rejection_reason.strip()) < 5:
            raise ValueError("Rejection reason is required (minimum 5 characters)")
        
        return await self.repo.update_status(
            outpass_id,
            OutpassStatus.REJECTED,
            warden_id,
            rejection_reason=rejection_reason
        )

    async def get_outpass_history_for_student(
        self,
        warden_id: int,
        student_id: int
    ) -> list[OutpassOut]:
        """Get outpass history for a specific student (warden view)."""
        # Verify warden authority
        await self._verify_warden_authority(warden_id, student_id)
        
        outpasses, _ = await self.repo.get_student_outpasses(student_id)
        return [OutpassOut.model_validate(o) for o in outpasses]

    # ==================== ADMIN OPERATIONS ====================

    async def get_all_outpasses(
        self,
        status: OutpassStatus | None = None,
        hostel_id: int | None = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[OutpassWithStudentDetails], int]:
        """Get all outpass requests (admin view)."""
        from sqlalchemy import select, func
        from app.models.hostel import HostelAssignment
        
        query = select(OutpassRequest)
        count_query = select(func.count(OutpassRequest.id))
        
        # Filter by hostel if specified
        if hostel_id:
            assignment_result = await self.db.execute(
                select(HostelAssignment.student_id)
                .where(HostelAssignment.hostel_id == hostel_id, HostelAssignment.is_active == True)
            )
            student_ids = [row[0] for row in assignment_result.fetchall()]
            query = query.where(OutpassRequest.student_id.in_(student_ids))
            count_query = count_query.where(OutpassRequest.student_id.in_(student_ids))
        
        if status:
            query = query.where(OutpassRequest.status == status)
            count_query = count_query.where(OutpassRequest.status == status)
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        skip = (page - 1) * page_size
        result = await self.db.execute(
            query.order_by(OutpassRequest.created_at.desc())
            .offset(skip)
            .limit(page_size)
        )
        outpasses = result.scalars().all()
        
        enriched = []
        for outpass in outpasses:
            details = await self._enrich_outpass_with_student(outpass)
            enriched.append(details)
        
        return enriched, total

    # ==================== HELPER METHODS ====================

    async def _verify_warden_authority(self, warden_id: int, student_id: int) -> None:
        """Verify warden has authority over the student's hostel."""
        warden_hostel = await self.hostel_repo.get_warden_hostel(warden_id)
        if not warden_hostel:
            raise PermissionError("You are not assigned as warden to any hostel")
        
        student_assignment = await self.hostel_repo.get_student_assignment(student_id)
        if not student_assignment:
            raise ValueError("Student is not assigned to any hostel")
        
        if student_assignment.hostel_id != warden_hostel.id:
            raise PermissionError("You can only manage students in your hostel")

    async def _enrich_outpass_with_student(
        self, outpass: OutpassRequest
    ) -> OutpassWithStudentDetails:
        """Add student details to outpass data."""
        from sqlalchemy import select
        
        # Get student
        result = await self.db.execute(select(User).where(User.id == outpass.student_id))
        student = result.scalar_one_or_none()
        
        # Get room number
        assignment = await self.hostel_repo.get_student_assignment(outpass.student_id)
        room_number = None
        if assignment:
            room = await self.hostel_repo.get_room(assignment.room_id)
            room_number = room.room_number if room else None
        
        return OutpassWithStudentDetails(
            id=outpass.id,
            student_id=outpass.student_id,
            reason=outpass.reason,
            destination=outpass.destination,
            start_datetime=outpass.start_datetime,
            end_datetime=outpass.end_datetime,
            emergency_contact=outpass.emergency_contact,
            status=outpass.status,
            rejection_reason=outpass.rejection_reason,
            reviewed_by=outpass.reviewed_by,
            reviewed_at=outpass.reviewed_at,
            created_at=outpass.created_at,
            updated_at=outpass.updated_at,
            student_name=f"{student.first_name} {student.last_name}" if student else "Unknown",
            student_register_number=student.register_number if student else None,
            student_room_number=room_number,
            student_department=student.department if student else None
        )
