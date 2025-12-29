"""Repository for Complaint model."""
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.complaint import Complaint, ComplaintStatus


class ComplaintRepository:
    """Repository for Complaint CRUD operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, complaint: Complaint) -> Complaint:
        """Create a new complaint."""
        self.db.add(complaint)
        await self.db.flush()
        await self.db.refresh(complaint)
        return complaint
    
    async def get_by_id(self, complaint_id: int) -> Complaint | None:
        """Get complaint by ID with relationships."""
        result = await self.db.execute(
            select(Complaint)
            .options(selectinload(Complaint.student))
            .where(Complaint.id == complaint_id)
        )
        return result.scalar_one_or_none()
    
    async def get_student_complaints(self, student_id: int) -> list[Complaint]:
        """Get all complaints by a student."""
        result = await self.db.execute(
            select(Complaint)
            .where(Complaint.student_id == student_id)
            .order_by(Complaint.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_pending_complaints(self, student_type: str | None = None) -> list[Complaint]:
        """Get pending complaints (SUBMITTED or IN_PROGRESS)."""
        stmt = select(Complaint).options(selectinload(Complaint.student)).where(
            Complaint.status.in_([ComplaintStatus.SUBMITTED, ComplaintStatus.IN_PROGRESS])
        )
        
        if student_type:
            stmt = stmt.where(Complaint.student_type == student_type)
        
        stmt = stmt.order_by(Complaint.created_at.asc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_resolved_complaints(self, student_type: str | None = None) -> list[Complaint]:
        """Get resolved complaints (CLOSED or REJECTED)."""
        stmt = select(Complaint).options(selectinload(Complaint.student)).where(
            Complaint.status.in_([ComplaintStatus.CLOSED, ComplaintStatus.REJECTED])
        )
        
        if student_type:
            stmt = stmt.where(Complaint.student_type == student_type)
        
        stmt = stmt.order_by(Complaint.closed_at.desc()).limit(50)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def update(self, complaint: Complaint) -> Complaint:
        """Update a complaint."""
        await self.db.flush()
        await self.db.refresh(complaint)
        return complaint
    
    async def check_duplicate(self, student_id: int, location: str, category: str) -> bool:
        """Check if student has an open complaint for same location and category."""
        result = await self.db.execute(
            select(Complaint).where(
                Complaint.student_id == student_id,
                Complaint.location == location,
                Complaint.category == category,
                Complaint.status.in_([ComplaintStatus.SUBMITTED, ComplaintStatus.IN_PROGRESS])
            )
        )
        return result.scalar_one_or_none() is not None
