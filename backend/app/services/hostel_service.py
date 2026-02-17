"""Service for hostel management business logic."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.hostel_repository import HostelRepository
from app.models.hostel import Hostel, HostelRoom, HostelAssignment, HostelType
from app.models.user import User, UserRole, StudentCategory, Gender
from app.schemas.hostel import (
    HostelCreate, HostelUpdate, HostelWithDetails,
    HostelRoomCreate, HostelRoomUpdate, HostelRoomWithOccupancy,
    HostelAssignmentCreate, HostelAssignmentWithDetails,
    HostelAssignmentRecommendation, HostelAutoAssignConfirmItem, HostelStudentProfile,
    HostelAutoAssignPreview, HostelAutoAssignResult, HostelAutoAssignSkip,
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
            capacity=data.capacity,
            hostel_type=data.hostel_type
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
                hostel_type=hostel.hostel_type,
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
        
        if student.role not in [UserRole.STUDENT, UserRole.HOSTELLER]:
            raise ValueError("User must be a student")
        
        if student.student_category != StudentCategory.HOSTELLER:
            raise ValueError("Student must be a hosteller")
        
        # Verify hostel and room
        hostel = await self.repo.get_hostel(data.hostel_id)
        if not hostel:
            raise ValueError("Hostel not found")
        if not hostel.is_active:
            raise ValueError("Hostel is inactive")
        
        room = await self.repo.get_room(data.room_id)
        if not room:
            raise ValueError("Room not found")
        if not room.is_active:
            raise ValueError("Room is inactive")
        
        if room.hostel_id != data.hostel_id:
            raise ValueError("Room does not belong to specified hostel")

        # Hostel type vs gender matching
        hostel_type = hostel.hostel_type or HostelType.CO_ED
        required_gender = self._required_gender(hostel_type)
        if required_gender and student.gender != required_gender:
            raise ValueError("Student gender does not match hostel type")
        
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
                    student_email=student.email,
                    student_department=student.department,
                    student_batch=student.batch,
                    student_degree=student.degree,
                    student_study_year=student.study_year,
                    student_gender=student.gender,
                    hostel_name=hostel.name,
                    room_number=room.room_number,
                    room_floor=room.floor
                ))
        
        return result

    async def get_unassigned_hostellers_for_hostel(
        self,
        hostel_id: int
    ) -> list[HostelStudentProfile]:
        """Get unassigned hosteller students eligible for this hostel."""
        hostel = await self.repo.get_hostel(hostel_id)
        if not hostel or not hostel.is_active:
            raise ValueError("Hostel not found or inactive")

        hostel_type = hostel.hostel_type or HostelType.CO_ED
        required_gender = self._required_gender(hostel_type)
        candidates = await self.repo.get_unassigned_hosteller_students()

        profiles: list[HostelStudentProfile] = []
        for student in candidates:
            if required_gender and student.gender != required_gender:
                continue
            profiles.append(
                HostelStudentProfile(
                    student_id=student.id,
                    student_name=f"{student.first_name} {student.last_name}",
                    student_register_number=student.register_number,
                    student_email=student.email,
                    student_department=student.department,
                    student_batch=student.batch,
                    student_degree=student.degree,
                    student_study_year=student.study_year,
                    student_gender=student.gender,
                )
            )
        return profiles

    # ==================== AUTO ASSIGNMENT ====================

    @staticmethod
    def _room_match_score(student: User, occupants: list[User]) -> float:
        """Score how well a student matches current room occupants."""
        if not occupants:
            return 0.1
        score = 0.0
        for occupant in occupants:
            if student.department and occupant.department and student.department == occupant.department:
                score += 3.0
            if student.study_year and occupant.study_year and student.study_year == occupant.study_year:
                score += 2.0
            if student.degree and occupant.degree and student.degree == occupant.degree:
                score += 2.0
            if student.batch and occupant.batch and student.batch == occupant.batch:
                score += 1.0
        score = score / max(len(occupants), 1)
        score += len(occupants) * 0.1  # prefer filling rooms for cohesion
        return score

    @staticmethod
    def _required_gender(hostel_type: HostelType) -> Gender | None:
        """Map hostel type to required gender (if any)."""
        if hostel_type == HostelType.BOYS:
            return Gender.MALE
        if hostel_type == HostelType.GIRLS:
            return Gender.FEMALE
        return None

    async def recommend_assignments_for_hostel(
        self,
        hostel_id: int,
        department: str | None = None,
        study_year: int | None = None,
        degree: str | None = None,
        gender: Gender | None = None,
        batch: str | None = None,
        limit: int | None = None,
        strategy: str = "fill",
    ) -> HostelAutoAssignPreview:
        """Generate room recommendations without assigning."""
        hostel = await self.repo.get_hostel(hostel_id)
        if not hostel or not hostel.is_active:
            raise ValueError("Hostel not found or inactive")

        rooms = await self.repo.get_hostel_rooms(hostel_id, include_inactive=False)
        active_rooms = [room for room in rooms if room.is_active]
        occupants_by_room = await self.repo.get_room_occupants(hostel_id)

        hostel_type = hostel.hostel_type or HostelType.CO_ED
        required_gender = self._required_gender(hostel_type)
        candidates = await self.repo.get_unassigned_hosteller_students()
        if department:
            candidates = [c for c in candidates if c.department == department]
        if study_year:
            candidates = [c for c in candidates if c.study_year == study_year]
        if degree:
            candidates = [c for c in candidates if c.degree == degree]
        if batch:
            candidates = [c for c in candidates if c.batch == batch]
        if gender:
            candidates = [c for c in candidates if c.gender == gender]

        recommendations: list[HostelAssignmentRecommendation] = []
        skipped: list[HostelAutoAssignSkip] = []

        if not active_rooms:
            for student in candidates:
                if required_gender and student.gender != required_gender:
                    skipped.append(
                        HostelAutoAssignSkip(
                            student_id=student.id,
                            reason="Gender does not match hostel type"
                        )
                    )
                else:
                    skipped.append(
                        HostelAutoAssignSkip(
                            student_id=student.id,
                            reason="No active rooms available"
                        )
                    )
            return HostelAutoAssignPreview(
                hostel_id=hostel_id,
                recommended_count=0,
                skipped_count=len(skipped),
                recommendations=[],
                skipped=skipped,
            )

        # Track occupancy in-memory for speed
        occupancy: dict[int, int] = {
            room.id: len(occupants_by_room.get(room.id, [])) for room in active_rooms
        }

        for student in candidates:
            if required_gender and student.gender != required_gender:
                skipped.append(
                    HostelAutoAssignSkip(
                        student_id=student.id,
                        reason="Gender does not match hostel type"
                    )
                )
                continue

            best_room = None
            best_score = -1.0
            best_occupancy = -1

            for room in active_rooms:
                current_occupancy = occupancy.get(room.id, 0)
                if current_occupancy >= room.capacity:
                    continue
                score = self._room_match_score(student, occupants_by_room.get(room.id, []))
                if strategy == "spread":
                    better_tiebreak = current_occupancy < best_occupancy if best_occupancy >= 0 else True
                else:
                    better_tiebreak = current_occupancy > best_occupancy
                if score > best_score or (score == best_score and better_tiebreak):
                    best_score = score
                    best_room = room
                    best_occupancy = current_occupancy

            if not best_room:
                skipped.append(
                    HostelAutoAssignSkip(
                        student_id=student.id,
                        reason="No available room"
                    )
                )
                continue

            # Update occupancy and occupants cache
            occupancy[best_room.id] = occupancy.get(best_room.id, 0) + 1
            occupants_by_room.setdefault(best_room.id, []).append(student)

            recommendations.append(
                HostelAssignmentRecommendation(
                    student_id=student.id,
                    student_name=f"{student.first_name} {student.last_name}",
                    student_register_number=student.register_number,
                    department=student.department,
                    study_year=student.study_year,
                    degree=student.degree,
                    batch=student.batch,
                    gender=student.gender,
                    hostel_id=hostel.id,
                    room_id=best_room.id,
                    room_number=best_room.room_number,
                    room_floor=best_room.floor,
                    score=best_score,
                )
            )

            if limit and len(recommendations) >= limit:
                break

        return HostelAutoAssignPreview(
            hostel_id=hostel_id,
            recommended_count=len(recommendations),
            skipped_count=len(skipped),
            recommendations=recommendations,
            skipped=skipped,
        )

    async def confirm_auto_assignments(
        self,
        hostel_id: int,
        assignments: list[HostelAutoAssignConfirmItem],
        created_by: int | None = None,
    ) -> HostelAutoAssignResult:
        """Confirm and apply recommended assignments."""
        hostel = await self.repo.get_hostel(hostel_id)
        if not hostel or not hostel.is_active:
            raise ValueError("Hostel not found or inactive")

        assigned: list[HostelAssignmentWithDetails] = []
        skipped: list[HostelAutoAssignSkip] = []

        for item in assignments:
            try:
                from sqlalchemy import select
                assignment = await self.assign_student(
                    HostelAssignmentCreate(
                        student_id=item.student_id,
                        hostel_id=hostel_id,
                        room_id=item.room_id,
                    )
                )
                room = await self.repo.get_room(item.room_id)
                student_result = await self.db.execute(
                    select(User).where(User.id == item.student_id)
                )
                student = student_result.scalar_one_or_none()

                assigned.append(
                    HostelAssignmentWithDetails(
                        id=assignment.id,
                        student_id=assignment.student_id,
                        hostel_id=assignment.hostel_id,
                        room_id=assignment.room_id,
                        assigned_at=assignment.assigned_at,
                        is_active=assignment.is_active,
                        student_name=f"{student.first_name} {student.last_name}" if student else "",
                        student_register_number=student.register_number if student else None,
                        student_email=student.email if student else None,
                        student_department=student.department if student else None,
                        student_batch=student.batch if student else None,
                        student_degree=student.degree if student else None,
                        student_study_year=student.study_year if student else None,
                        student_gender=student.gender if student else None,
                        hostel_name=hostel.name,
                        room_number=room.room_number if room else "",
                        room_floor=room.floor if room else None,
                    )
                )
            except ValueError as e:
                skipped.append(
                    HostelAutoAssignSkip(student_id=item.student_id, reason=str(e))
                )

        assigned_count = len(assigned)
        skipped_count = len(skipped)

        batch = await self.repo.create_assignment_batch(
            hostel_id=hostel_id,
            created_by=created_by,
            assigned_count=assigned_count,
            skipped_count=skipped_count,
            assigned=[item.model_dump(mode="json") for item in assigned],
            skipped=[item.model_dump(mode="json") for item in skipped],
        )
        created_by_name = None
        created_by_username = None
        created_by_email = None
        if created_by:
            from sqlalchemy import select
            user_result = await self.db.execute(select(User).where(User.id == created_by))
            creator = user_result.scalar_one_or_none()
            if creator:
                created_by_name = f"{creator.first_name} {creator.last_name}"
                created_by_username = creator.username
                created_by_email = creator.email

        return HostelAutoAssignResult(
            hostel_id=hostel_id,
            assigned_count=assigned_count,
            skipped_count=skipped_count,
            assigned=assigned,
            skipped=skipped,
            created_by_id=created_by,
            created_by_name=created_by_name,
            created_by_username=created_by_username,
            created_by_email=created_by_email,
            created_at=batch.created_at,
        )

    async def get_latest_auto_assign_result(
        self, hostel_id: int
    ) -> HostelAutoAssignResult | None:
        """Get latest auto-assign batch result for hostel."""
        batch = await self.repo.get_latest_assignment_batch(hostel_id)
        if not batch:
            return None
        created_by_name = None
        created_by_username = None
        created_by_email = None
        if batch.created_by:
            from sqlalchemy import select
            user_result = await self.db.execute(select(User).where(User.id == batch.created_by))
            creator = user_result.scalar_one_or_none()
            if creator:
                created_by_name = f"{creator.first_name} {creator.last_name}"
                created_by_username = creator.username
                created_by_email = creator.email
        return HostelAutoAssignResult(
            hostel_id=batch.hostel_id,
            assigned_count=batch.assigned_count,
            skipped_count=batch.skipped_count,
            assigned=batch.assigned,
            skipped=batch.skipped,
            created_by_id=batch.created_by,
            created_by_name=created_by_name,
            created_by_username=created_by_username,
            created_by_email=created_by_email,
            created_at=batch.created_at,
        )

    # ==================== WARDEN HELPERS ====================

    async def get_warden_hostel(self, warden_id: int) -> Hostel | None:
        """Get hostel managed by warden."""
        return await self.repo.get_warden_hostel(warden_id)
