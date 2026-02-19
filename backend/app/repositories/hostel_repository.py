"""Repository for hostel data access."""
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hostel import Hostel, HostelRoom, HostelAssignment, HostelAssignmentBatch
from app.models.user import User, UserRole, StudentCategory


class HostelRepository:
    """Repository for hostel operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== HOSTEL CRUD ====================

    async def create_hostel(
        self,
        name: str,
        address: str | None = None,
        capacity: int = 100,
        hostel_type=None,
    ) -> Hostel:
        """Create a new hostel."""
        hostel = Hostel(name=name, address=address, capacity=capacity, hostel_type=hostel_type)
        self.db.add(hostel)
        await self.db.commit()
        await self.db.refresh(hostel)
        return hostel

    async def get_hostel(self, hostel_id: int) -> Hostel | None:
        """Get hostel by ID."""
        result = await self.db.execute(
            select(Hostel).where(Hostel.id == hostel_id)
        )
        return result.scalar_one_or_none()

    async def get_hostel_by_name(self, name: str) -> Hostel | None:
        """Get hostel by name."""
        result = await self.db.execute(
            select(Hostel).where(Hostel.name == name)
        )
        return result.scalar_one_or_none()

    async def get_all_hostels(self, include_inactive: bool = False) -> list[Hostel]:
        """Get all hostels."""
        query = select(Hostel)
        if not include_inactive:
            query = query.where(Hostel.is_active == True)
        result = await self.db.execute(query.order_by(Hostel.name))
        return list(result.scalars().all())

    async def update_hostel(self, hostel_id: int, **kwargs) -> Hostel | None:
        """Update hostel."""
        hostel = await self.get_hostel(hostel_id)
        if not hostel:
            return None

        for key, value in kwargs.items():
            if hasattr(hostel, key) and (value is not None or key == "warden_id"):
                setattr(hostel, key, value)
        await self.db.commit()
        await self.db.refresh(hostel)
        return hostel

    async def assign_warden(self, hostel_id: int, warden_id: int | None) -> Hostel | None:
        """Assign or remove warden from hostel."""
        return await self.update_hostel(hostel_id, warden_id=warden_id)

    async def get_warden_hostels(self, warden_id: int) -> list[Hostel]:
        """Get all active hostels managed by a warden."""
        result = await self.db.execute(
            select(Hostel)
            .where(Hostel.warden_id == warden_id, Hostel.is_active == True)
            .order_by(Hostel.updated_at.desc(), Hostel.id.desc())
        )
        return list(result.scalars().all())

    async def get_warden_hostel(self, warden_id: int) -> Hostel | None:
        """Get hostel managed by a warden."""
        hostels = await self.get_warden_hostels(warden_id)
        return hostels[0] if hostels else None

    # ==================== ROOM CRUD ====================

    async def create_room(
        self, hostel_id: int, room_number: str, floor: int = 0, capacity: int = 2
    ) -> HostelRoom:
        """Create a new room in hostel."""
        room = HostelRoom(
            hostel_id=hostel_id,
            room_number=room_number,
            floor=floor,
            capacity=capacity
        )
        self.db.add(room)
        await self.db.commit()
        await self.db.refresh(room)
        return room

    async def get_room(self, room_id: int) -> HostelRoom | None:
        """Get room by ID."""
        result = await self.db.execute(
            select(HostelRoom).where(HostelRoom.id == room_id)
        )
        return result.scalar_one_or_none()

    async def get_hostel_rooms(self, hostel_id: int, include_inactive: bool = False) -> list[HostelRoom]:
        """Get all rooms in a hostel."""
        query = select(HostelRoom).where(HostelRoom.hostel_id == hostel_id)
        if not include_inactive:
            query = query.where(HostelRoom.is_active == True)
        result = await self.db.execute(query.order_by(HostelRoom.floor, HostelRoom.room_number))
        return list(result.scalars().all())

    async def update_room(self, room_id: int, **kwargs) -> HostelRoom | None:
        """Update room."""
        room = await self.get_room(room_id)
        if not room:
            return None
        for key, value in kwargs.items():
            if hasattr(room, key) and value is not None:
                setattr(room, key, value)
        await self.db.commit()
        await self.db.refresh(room)
        return room

    async def get_room_occupancy(self, room_id: int) -> int:
        """Get current occupancy of a room."""
        result = await self.db.execute(
            select(func.count(HostelAssignment.id))
            .where(HostelAssignment.room_id == room_id, HostelAssignment.is_active == True)
        )
        return result.scalar() or 0

    async def get_room_occupants(self, hostel_id: int) -> dict[int, list[User]]:
        """Get active occupants for rooms in a hostel."""
        result = await self.db.execute(
            select(HostelAssignment.room_id, User)
            .join(User, User.id == HostelAssignment.student_id)
            .where(
                HostelAssignment.hostel_id == hostel_id,
                HostelAssignment.is_active == True
            )
        )
        occupants: dict[int, list[User]] = {}
        for room_id, user in result.all():
            occupants.setdefault(room_id, []).append(user)
        return occupants

    # ==================== ASSIGNMENT CRUD ====================

    async def create_assignment(
        self, student_id: int, hostel_id: int, room_id: int
    ) -> HostelAssignment:
        """
        Assign student to a room.

        Note: `hostel_assignments.student_id` is globally unique in DB.
        So if an old inactive row exists, reactivate/update that row instead of inserting a new one.
        """
        active = await self.get_student_assignment(student_id)
        if active:
            raise ValueError("Student already has an active hostel assignment")

        result = await self.db.execute(
            select(HostelAssignment).where(HostelAssignment.student_id == student_id)
        )
        existing_any = result.scalar_one_or_none()

        if existing_any:
            existing_any.hostel_id = hostel_id
            existing_any.room_id = room_id
            existing_any.is_active = True
            existing_any.assigned_at = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(existing_any)
            return existing_any

        assignment = HostelAssignment(
            student_id=student_id,
            hostel_id=hostel_id,
            room_id=room_id
        )
        self.db.add(assignment)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            # Race-safe fallback for concurrent assignment requests.
            raise ValueError("Student already has an active hostel assignment")
        await self.db.refresh(assignment)
        return assignment

    async def get_assignment(self, assignment_id: int) -> HostelAssignment | None:
        """Get assignment by ID."""
        result = await self.db.execute(
            select(HostelAssignment).where(HostelAssignment.id == assignment_id)
        )
        return result.scalar_one_or_none()

    async def get_student_assignment(self, student_id: int) -> HostelAssignment | None:
        """Get active assignment for a student."""
        result = await self.db.execute(
            select(HostelAssignment)
            .where(HostelAssignment.student_id == student_id, HostelAssignment.is_active == True)
        )
        return result.scalar_one_or_none()

    async def get_hostel_assignments(self, hostel_id: int) -> list[HostelAssignment]:
        """Get all active assignments in a hostel."""
        result = await self.db.execute(
            select(HostelAssignment)
            .where(HostelAssignment.hostel_id == hostel_id, HostelAssignment.is_active == True)
        )
        return list(result.scalars().all())

    async def get_hostel_assignments_with_details(
        self, hostel_id: int
    ) -> list[tuple[HostelAssignment, User, Hostel, HostelRoom]]:
        """Get all active assignments in a hostel with joined details."""
        result = await self.db.execute(
            select(HostelAssignment, User, Hostel, HostelRoom)
            .join(User, User.id == HostelAssignment.student_id)
            .join(Hostel, Hostel.id == HostelAssignment.hostel_id)
            .join(HostelRoom, HostelRoom.id == HostelAssignment.room_id)
            .where(
                HostelAssignment.hostel_id == hostel_id,
                HostelAssignment.is_active == True,
            )
            .order_by(HostelRoom.room_number, User.last_name, User.first_name)
        )
        return list(result.all())

    async def get_all_active_assignments_with_details(
        self,
    ) -> list[tuple[HostelAssignment, User, Hostel, HostelRoom]]:
        """Get all active assignments with joined hostel, room, and student details."""
        result = await self.db.execute(
            select(HostelAssignment, User, Hostel, HostelRoom)
            .join(User, User.id == HostelAssignment.student_id)
            .join(Hostel, Hostel.id == HostelAssignment.hostel_id)
            .join(HostelRoom, HostelRoom.id == HostelAssignment.room_id)
            .where(HostelAssignment.is_active == True)
            .order_by(Hostel.name, HostelRoom.room_number, User.last_name, User.first_name)
        )
        return list(result.all())

    async def deactivate_student_assignment(self, student_id: int) -> bool:
        """Deactivate student's current assignment."""
        assignment = await self.get_student_assignment(student_id)
        if assignment:
            assignment.is_active = False
            await self.db.commit()
            return True
        return False

    async def get_hostel_occupancy(self, hostel_id: int) -> int:
        """Get total occupancy of a hostel."""
        result = await self.db.execute(
            select(func.count(HostelAssignment.id))
            .where(HostelAssignment.hostel_id == hostel_id, HostelAssignment.is_active == True)
        )
        return result.scalar() or 0

    async def create_assignment_batch(
        self,
        hostel_id: int,
        created_by: int | None,
        assigned_count: int,
        skipped_count: int,
        assigned: list,
        skipped: list,
    ) -> HostelAssignmentBatch:
        """Create a batch record for auto-assign confirmation."""
        batch = HostelAssignmentBatch(
            hostel_id=hostel_id,
            created_by=created_by,
            assigned_count=assigned_count,
            skipped_count=skipped_count,
            assigned=assigned,
            skipped=skipped,
        )
        self.db.add(batch)
        await self.db.commit()
        await self.db.refresh(batch)
        return batch

    async def get_latest_assignment_batch(self, hostel_id: int) -> HostelAssignmentBatch | None:
        """Get latest assignment batch for a hostel."""
        result = await self.db.execute(
            select(HostelAssignmentBatch)
            .where(HostelAssignmentBatch.hostel_id == hostel_id)
            .order_by(HostelAssignmentBatch.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_unassigned_hosteller_students(self, hostel_id: int | None = None) -> list[User]:
        """
        Get active hosteller students who have never had any hostel assignment row.

        `hostel_id` is accepted for caller compatibility but does not change behavior.
        """
        any_assignment_exists = select(HostelAssignment.id).where(
            HostelAssignment.student_id == User.id
        ).exists()

        query = select(User).where(
            User.is_active == True,
            User.student_category == StudentCategory.HOSTELLER,
            User.role.in_([UserRole.STUDENT, UserRole.HOSTELLER]),
            ~any_assignment_exists
        )

        result = await self.db.execute(
            query.order_by(User.department, User.study_year, User.degree, User.last_name)
        )
        return list(result.scalars().all())

    # ==================== HELPER METHODS ====================

    async def get_student_hostel_info(self, student_id: int) -> dict:
        """Get student's hostel information for dashboard."""
        assignment = await self.get_student_assignment(student_id)
        if not assignment:
            return {"is_assigned": False}

        # Get hostel and room details
        hostel = await self.get_hostel(assignment.hostel_id)
        room = await self.get_room(assignment.room_id)

        # Get warden name if assigned
        warden_name = None
        if hostel and hostel.warden_id:
            result = await self.db.execute(
                select(User).where(User.id == hostel.warden_id)
            )
            warden = result.scalar_one_or_none()
            if warden:
                warden_name = f"{warden.first_name} {warden.last_name}"

        return {
            "is_assigned": True,
            "hostel_name": hostel.name if hostel else None,
            "hostel_address": hostel.address if hostel else None,
            "room_number": room.room_number if room else None,
            "floor": room.floor if room else None,
            "warden_name": warden_name,
            "assigned_at": assignment.assigned_at
        }

    async def check_room_availability(self, room_id: int) -> bool:
        """Check if room has available beds."""
        room = await self.get_room(room_id)
        if not room:
            return False
        occupancy = await self.get_room_occupancy(room_id)
        return occupancy < room.capacity
