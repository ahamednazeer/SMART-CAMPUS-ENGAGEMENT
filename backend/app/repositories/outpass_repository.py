"""Repository for outpass request data access."""
from datetime import datetime, date
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.outpass import OutpassRequest, OutpassStatus, OutpassLog
from app.models.user import User
from app.models.hostel import HostelAssignment


class OutpassRepository:
    """Repository for outpass operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== OUTPASS CRUD ====================

    async def create_outpass(
        self,
        student_id: int,
        reason: str,
        destination: str,
        start_datetime: datetime,
        end_datetime: datetime,
        emergency_contact: str
    ) -> OutpassRequest:
        """Create a new outpass request."""
        outpass = OutpassRequest(
            student_id=student_id,
            reason=reason,
            destination=destination,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            emergency_contact=emergency_contact,
            status=OutpassStatus.SUBMITTED
        )
        self.db.add(outpass)
        await self.db.commit()
        await self.db.refresh(outpass)
        
        # Create initial log
        await self._create_log(outpass.id, None, OutpassStatus.SUBMITTED, student_id, "Request submitted")
        
        return outpass

    async def get_outpass(self, outpass_id: int) -> OutpassRequest | None:
        """Get outpass by ID."""
        result = await self.db.execute(
            select(OutpassRequest).where(OutpassRequest.id == outpass_id)
        )
        return result.scalar_one_or_none()

    async def get_student_outpasses(
        self,
        student_id: int,
        status: OutpassStatus | None = None,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[list[OutpassRequest], int]:
        """Get outpass requests for a student with pagination."""
        query = select(OutpassRequest).where(OutpassRequest.student_id == student_id)
        count_query = select(func.count(OutpassRequest.id)).where(OutpassRequest.student_id == student_id)
        
        if status:
            query = query.where(OutpassRequest.status == status)
            count_query = count_query.where(OutpassRequest.status == status)
        
        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Get paginated results
        result = await self.db.execute(
            query.order_by(OutpassRequest.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_pending_for_hostel(
        self,
        hostel_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[list[OutpassRequest], int]:
        """Get pending outpass requests for a hostel (warden view)."""
        # First get student IDs in this hostel
        assignment_result = await self.db.execute(
            select(HostelAssignment.student_id)
            .where(HostelAssignment.hostel_id == hostel_id, HostelAssignment.is_active == True)
        )
        student_ids = [row[0] for row in assignment_result.fetchall()]
        
        if not student_ids:
            return [], 0
        
        # Query for pending outpasses
        query = select(OutpassRequest).where(
            OutpassRequest.student_id.in_(student_ids),
            OutpassRequest.status == OutpassStatus.SUBMITTED
        )
        count_query = select(func.count(OutpassRequest.id)).where(
            OutpassRequest.student_id.in_(student_ids),
            OutpassRequest.status == OutpassStatus.SUBMITTED
        )
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        result = await self.db.execute(
            query.order_by(OutpassRequest.start_datetime.asc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def update_status(
        self,
        outpass_id: int,
        new_status: OutpassStatus,
        changed_by: int,
        rejection_reason: str | None = None,
        notes: str | None = None
    ) -> OutpassRequest | None:
        """Update outpass status."""
        outpass = await self.get_outpass(outpass_id)
        if not outpass:
            return None
        
        old_status = outpass.status
        outpass.status = new_status
        
        if new_status == OutpassStatus.REJECTED and rejection_reason:
            outpass.rejection_reason = rejection_reason
        
        if new_status in [OutpassStatus.APPROVED, OutpassStatus.REJECTED]:
            outpass.reviewed_by = changed_by
            outpass.reviewed_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(outpass)
        
        # Create log
        await self._create_log(outpass_id, old_status, new_status, changed_by, notes or rejection_reason)
        
        return outpass

    # ==================== VALIDATION METHODS ====================

    async def check_overlapping_outpass(
        self,
        student_id: int,
        start_datetime: datetime,
        end_datetime: datetime,
        exclude_id: int | None = None
    ) -> bool:
        """Check if student has overlapping outpass requests."""
        query = select(OutpassRequest).where(
            OutpassRequest.student_id == student_id,
            OutpassRequest.status.in_([
                OutpassStatus.SUBMITTED,
                OutpassStatus.UNDER_REVIEW,
                OutpassStatus.APPROVED
            ]),
            # Overlapping condition: new start < existing end AND new end > existing start
            OutpassRequest.start_datetime < end_datetime,
            OutpassRequest.end_datetime > start_datetime
        )
        
        if exclude_id:
            query = query.where(OutpassRequest.id != exclude_id)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def get_monthly_count(self, student_id: int, year: int, month: int) -> int:
        """Get count of outpass requests in a specific month."""
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        
        result = await self.db.execute(
            select(func.count(OutpassRequest.id)).where(
                OutpassRequest.student_id == student_id,
                OutpassRequest.created_at >= start_date,
                OutpassRequest.created_at < end_date
            )
        )
        return result.scalar() or 0

    async def get_student_summary(self, student_id: int) -> dict:
        """Get summary of student's outpass usage."""
        # Total counts by status
        result = await self.db.execute(
            select(OutpassRequest.status, func.count(OutpassRequest.id))
            .where(OutpassRequest.student_id == student_id)
            .group_by(OutpassRequest.status)
        )
        status_counts = dict(result.fetchall())
        
        # Current month count
        now = datetime.utcnow()
        current_month_count = await self.get_monthly_count(student_id, now.year, now.month)
        
        return {
            "total_requests": sum(status_counts.values()),
            "approved_count": status_counts.get(OutpassStatus.APPROVED, 0),
            "rejected_count": status_counts.get(OutpassStatus.REJECTED, 0),
            "pending_count": status_counts.get(OutpassStatus.SUBMITTED, 0),
            "current_month_count": current_month_count,
            "monthly_limit": 4  # Configurable
        }

    # ==================== EXPIRATION ====================

    async def expire_old_outpasses(self) -> int:
        """Mark expired outpasses (past end_datetime and still approved)."""
        now = datetime.utcnow()
        result = await self.db.execute(
            select(OutpassRequest).where(
                OutpassRequest.status == OutpassStatus.APPROVED,
                OutpassRequest.end_datetime < now
            )
        )
        outpasses = result.scalars().all()
        
        count = 0
        for outpass in outpasses:
            outpass.status = OutpassStatus.EXPIRED
            await self._create_log(outpass.id, OutpassStatus.APPROVED, OutpassStatus.EXPIRED, 0, "Auto-expired")
            count += 1
        
        if count > 0:
            await self.db.commit()
        
        return count

    # ==================== LOG METHODS ====================

    async def _create_log(
        self,
        outpass_id: int,
        previous_status: OutpassStatus | None,
        new_status: OutpassStatus,
        changed_by: int,
        notes: str | None = None
    ) -> OutpassLog:
        """Create outpass status change log."""
        log = OutpassLog(
            outpass_id=outpass_id,
            previous_status=previous_status,
            new_status=new_status,
            changed_by=changed_by,
            notes=notes
        )
        self.db.add(log)
        await self.db.commit()
        return log

    async def get_outpass_logs(self, outpass_id: int) -> list[OutpassLog]:
        """Get all logs for an outpass request."""
        result = await self.db.execute(
            select(OutpassLog)
            .where(OutpassLog.outpass_id == outpass_id)
            .order_by(OutpassLog.created_at.desc())
        )
        return list(result.scalars().all())
