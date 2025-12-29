"""Service for hostel management business logic."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.hostel_repository import HostelRepository
from app.models.hostel import Hostel, HostelRoom, HostelAssignment
from app.models.user import User, UserRole, StudentCategory
from app.schemas.hostel import (
    HostelCreate, HostelUpdate, HostelWithDetails,
    HostelRoomCreate, HostelRoomUpdate, HostelRoomWithOccupancy,
    HostelAssignmentCreate, HostelAssignmentWithDetails,
    StudentHostelInfo
)


class HostelService:
    """Service for hostel operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = HostelRepository(db)

    # ==================== HOSTEL OPERATIONS ====================

    async def create_hostel(self, data: HostelCreate) -> Hostel:
        """Create a new hostel."""
        # Check for duplicate name
        existing = await self.repo.get_hostel_by_name(data.name)
        if existing:
            raise ValueError(f"Hostel with name '{data.name}' already exists")
        
        return await self.repo.create_hostel(
            name=data.name,
            address=data.address,
            capacity=data.capacity
        )

    async def get_hostel(self, hostel_id: int) -> Hostel | None:
        """Get hostel by ID."""
        return await self.repo.get_hostel(hostel_id)

    async def list_hostels(self, include_inactive: bool = False) -> list[HostelWithDetails]:
        """List all hostels with details."""
        hostels = await self.repo.get_all_hostels(include_inactive)
        result = []
        
        for hostel in hostels:
            rooms = await self.repo.get_hostel_rooms(hostel.id)
            occupancy = await self.repo.get_hostel_occupancy(hostel.id)
            
            # Get warden name
            warden_name = None
            if hostel.warden_id:
                from sqlalchemy import select
                warden_result = await self.db.execute(
                    select(User).where(User.id == hostel.warden_id)
                )
                warden = warden_result.scalar_one_or_none()
                if warden:
                    warden_name = f"{warden.first_name} {warden.last_name}"
            
            result.append(HostelWithDetails(
                id=hostel.id,
                name=hostel.name,
                address=hostel.address,
                capacity=hostel.capacity,
                warden_id=hostel.warden_id,
                is_active=hostel.is_active,
                created_at=hostel.created_at,
                updated_at=hostel.updated_at,
                room_count=len(rooms),
                occupied_beds=occupancy,
                warden_name=warden_name
            ))
        
        return result

    async def update_hostel(self, hostel_id: int, data: HostelUpdate) -> Hostel:
        """Update hostel."""
        hostel = await self.repo.get_hostel(hostel_id)
        if not hostel:
            raise ValueError("Hostel not found")
        
        # Check name uniqueness if changing
        if data.name and data.name != hostel.name:
            existing = await self.repo.get_hostel_by_name(data.name)
            if existing:
                raise ValueError(f"Hostel with name '{data.name}' already exists")
        
        updated = await self.repo.update_hostel(
            hostel_id,
            **data.model_dump(exclude_unset=True)
        )
        return updated

    async def assign_warden(self, hostel_id: int, warden_id: int) -> Hostel:
        """Assign warden to hostel."""
        # Verify warden exists and has correct role
        from sqlalchemy import select
        result = await self.db.execute(select(User).where(User.id == warden_id))
        warden = result.scalar_one_or_none()
        
        if not warden:
            raise ValueError("User not found")
        
        if warden.role not in [UserRole.WARDEN, UserRole.ADMIN]:
            raise ValueError("User must have WARDEN or ADMIN role")
        
        return await self.repo.assign_warden(hostel_id, warden_id)

    async def remove_warden(self, hostel_id: int) -> Hostel:
        """Remove warden from hostel."""
        return await self.repo.assign_warden(hostel_id, None)

    # ==================== ROOM OPERATIONS ====================

    async def add_room(self, data: HostelRoomCreate) -> HostelRoom:
        """Add room to hostel."""
        hostel = await self.repo.get_hostel(data.hostel_id)
        if not hostel:
            raise ValueError("Hostel not found")
        
        return await self.repo.create_room(
            hostel_id=data.hostel_id,
            room_number=data.room_number,
            floor=data.floor,
            capacity=data.capacity
        )

    async def get_hostel_rooms(
        self, hostel_id: int, include_inactive: bool = False
    ) -> list[HostelRoomWithOccupancy]:
        """Get all rooms in a hostel with occupancy."""
        rooms = await self.repo.get_hostel_rooms(hostel_id, include_inactive)
        result = []
        
        for room in rooms:
            occupancy = await self.repo.get_room_occupancy(room.id)
            result.append(HostelRoomWithOccupancy(
                id=room.id,
                hostel_id=room.hostel_id,
                room_number=room.room_number,
                floor=room.floor,
                capacity=room.capacity,
                is_active=room.is_active,
                created_at=room.created_at,
                current_occupancy=occupancy,
                available_beds=room.capacity - occupancy
            ))
        
        return result

    async def update_room(self, room_id: int, data: HostelRoomUpdate) -> HostelRoom:
        """Update room."""
        room = await self.repo.get_room(room_id)
        if not room:
            raise ValueError("Room not found")
        
        return await self.repo.update_room(
            room_id,
            **data.model_dump(exclude_unset=True)
        )

    # ==================== ASSIGNMENT OPERATIONS ====================

    async def assign_student(self, data: HostelAssignmentCreate) -> HostelAssignment:
        """Assign student to a room."""
        # Verify student
        from sqlalchemy import select
        result = await self.db.execute(select(User).where(User.id == data.student_id))
        student = result.scalar_one_or_none()
        
        if not student:
            raise ValueError("Student not found")
        
        if student.role != UserRole.STUDENT:
            raise ValueError("User must be a student")
        
        if student.student_category != StudentCategory.HOSTELLER:
            raise ValueError("Student must be a hosteller")
        
        # Verify hostel and room
        hostel = await self.repo.get_hostel(data.hostel_id)
        if not hostel:
            raise ValueError("Hostel not found")
        
        room = await self.repo.get_room(data.room_id)
        if not room:
            raise ValueError("Room not found")
        
        if room.hostel_id != data.hostel_id:
            raise ValueError("Room does not belong to specified hostel")
        
        # Check room availability
        if not await self.repo.check_room_availability(data.room_id):
            raise ValueError("Room is full")
        
        return await self.repo.create_assignment(
            student_id=data.student_id,
            hostel_id=data.hostel_id,
            room_id=data.room_id
        )

    async def remove_student_assignment(self, student_id: int) -> bool:
        """Remove student's hostel assignment."""
        return await self.repo.deactivate_student_assignment(student_id)

    async def get_student_hostel_info(self, student_id: int) -> StudentHostelInfo:
        """Get student's hostel info for dashboard."""
        info = await self.repo.get_student_hostel_info(student_id)
        return StudentHostelInfo(**info)

    async def get_hostel_students(self, hostel_id: int) -> list[HostelAssignmentWithDetails]:
        """Get all students in a hostel with details."""
        assignments = await self.repo.get_hostel_assignments(hostel_id)
        result = []
        
        from sqlalchemy import select
        for assignment in assignments:
            # Get student details
            student_result = await self.db.execute(
                select(User).where(User.id == assignment.student_id)
            )
            student = student_result.scalar_one_or_none()
            
            # Get hostel and room
            hostel = await self.repo.get_hostel(assignment.hostel_id)
            room = await self.repo.get_room(assignment.room_id)
            
            if student and hostel and room:
                result.append(HostelAssignmentWithDetails(
                    id=assignment.id,
                    student_id=assignment.student_id,
                    hostel_id=assignment.hostel_id,
                    room_id=assignment.room_id,
                    assigned_at=assignment.assigned_at,
                    is_active=assignment.is_active,
                    student_name=f"{student.first_name} {student.last_name}",
                    student_register_number=student.register_number,
                    hostel_name=hostel.name,
                    room_number=room.room_number
                ))
        
        return result

    # ==================== WARDEN HELPERS ====================

    async def get_warden_hostel(self, warden_id: int) -> Hostel | None:
        """Get hostel managed by warden."""
        return await self.repo.get_warden_hostel(warden_id)
