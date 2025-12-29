"""Repository for maintenance complaint data access."""
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.maintenance import HostelMaintenance, MaintenanceStatus, MaintenanceCategory


class MaintenanceRepository:
    """Repository for maintenance complaint operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== CRUD ====================

    async def create_complaint(
        self,
        student_id: int,
        hostel_id: int,
        room_id: int,
        category: MaintenanceCategory,
        description: str
    ) -> HostelMaintenance:
        """Create a new maintenance complaint."""
        complaint = HostelMaintenance(
            student_id=student_id,
            hostel_id=hostel_id,
            room_id=room_id,
            category=category,
            description=description,
            status=MaintenanceStatus.PENDING
        )
        self.db.add(complaint)
        await self.db.commit()
        await self.db.refresh(complaint)
        return complaint

    async def get_complaint(self, complaint_id: int) -> HostelMaintenance | None:
        """Get complaint by ID."""
        result = await self.db.execute(
            select(HostelMaintenance).where(HostelMaintenance.id == complaint_id)
        )
        return result.scalar_one_or_none()

    async def get_student_complaints(
        self,
        student_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[list[HostelMaintenance], int]:
        """Get complaints raised by a student."""
        count_query = select(func.count(HostelMaintenance.id)).where(
            HostelMaintenance.student_id == student_id
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        result = await self.db.execute(
            select(HostelMaintenance)
            .where(HostelMaintenance.student_id == student_id)
            .order_by(HostelMaintenance.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_hostel_complaints(
        self,
        hostel_id: int,
        status: MaintenanceStatus | None = None,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[list[HostelMaintenance], int]:
        """Get complaints for a hostel (warden view)."""
        query = select(HostelMaintenance).where(HostelMaintenance.hostel_id == hostel_id)
        count_query = select(func.count(HostelMaintenance.id)).where(
            HostelMaintenance.hostel_id == hostel_id
        )
        
        if status:
            query = query.where(HostelMaintenance.status == status)
            count_query = count_query.where(HostelMaintenance.status == status)
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        result = await self.db.execute(
            query.order_by(HostelMaintenance.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_assigned_complaints(
        self,
        staff_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[list[HostelMaintenance], int]:
        """Get complaints assigned to a maintenance staff."""
        count_query = select(func.count(HostelMaintenance.id)).where(
            HostelMaintenance.assigned_to == staff_id,
            HostelMaintenance.status.in_([MaintenanceStatus.ASSIGNED, MaintenanceStatus.IN_PROGRESS])
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        result = await self.db.execute(
            select(HostelMaintenance)
            .where(
                HostelMaintenance.assigned_to == staff_id,
                HostelMaintenance.status.in_([MaintenanceStatus.ASSIGNED, MaintenanceStatus.IN_PROGRESS])
            )
            .order_by(HostelMaintenance.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    # ==================== STATUS UPDATES ====================

    async def assign_staff(
        self,
        complaint_id: int,
        staff_id: int
    ) -> HostelMaintenance | None:
        """Assign maintenance staff to a complaint."""
        complaint = await self.get_complaint(complaint_id)
        if not complaint:
            return None
        
        complaint.assigned_to = staff_id
        complaint.assigned_at = datetime.utcnow()
        complaint.status = MaintenanceStatus.ASSIGNED
        
        await self.db.commit()
        await self.db.refresh(complaint)
        return complaint

    async def update_status(
        self,
        complaint_id: int,
        new_status: MaintenanceStatus,
        resolution_notes: str | None = None
    ) -> HostelMaintenance | None:
        """Update complaint status."""
        complaint = await self.get_complaint(complaint_id)
        if not complaint:
            return None
        
        complaint.status = new_status
        
        if new_status == MaintenanceStatus.COMPLETED:
            complaint.resolved_at = datetime.utcnow()
            if resolution_notes:
                complaint.resolution_notes = resolution_notes
        
        await self.db.commit()
        await self.db.refresh(complaint)
        return complaint

    # ==================== STATISTICS ====================

    async def get_hostel_stats(self, hostel_id: int) -> dict:
        """Get maintenance statistics for a hostel."""
        result = await self.db.execute(
            select(HostelMaintenance.status, func.count(HostelMaintenance.id))
            .where(HostelMaintenance.hostel_id == hostel_id)
            .group_by(HostelMaintenance.status)
        )
        status_counts = dict(result.fetchall())
        
        return {
            "pending": status_counts.get(MaintenanceStatus.PENDING, 0),
            "assigned": status_counts.get(MaintenanceStatus.ASSIGNED, 0),
            "in_progress": status_counts.get(MaintenanceStatus.IN_PROGRESS, 0),
            "completed": status_counts.get(MaintenanceStatus.COMPLETED, 0),
            "closed": status_counts.get(MaintenanceStatus.CLOSED, 0),
            "total": sum(status_counts.values())
        }
