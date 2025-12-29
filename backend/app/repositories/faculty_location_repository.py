"""Repository for Faculty Location & Availability module."""
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.faculty_location import (
    CampusBuilding, FacultyAvailability, 
    AvailabilityStatus, VisibilityLevel
)
from app.models.user import User, UserRole


class FacultyLocationRepository:
    """Repository for Faculty Location CRUD operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ============ Campus Building Operations ============
    
    async def create_building(self, building: CampusBuilding) -> CampusBuilding:
        """Create a new campus building."""
        self.db.add(building)
        await self.db.flush()
        await self.db.refresh(building)
        return building
    
    async def get_building_by_id(self, building_id: int) -> CampusBuilding | None:
        """Get a campus building by ID."""
        result = await self.db.execute(
            select(CampusBuilding).where(CampusBuilding.id == building_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all_buildings(self, include_inactive: bool = False) -> list[CampusBuilding]:
        """Get all campus buildings."""
        stmt = select(CampusBuilding)
        if not include_inactive:
            stmt = stmt.where(CampusBuilding.is_active == True)
        stmt = stmt.order_by(CampusBuilding.name)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def update_building(self, building: CampusBuilding) -> CampusBuilding:
        """Update a campus building."""
        await self.db.flush()
        await self.db.refresh(building)
        return building
    
    async def delete_building(self, building_id: int) -> bool:
        """Soft delete a campus building (set inactive)."""
        building = await self.get_building_by_id(building_id)
        if building:
            building.is_active = False
            await self.db.flush()
            return True
        return False
    
    # ============ Faculty Availability Operations ============
    
    async def create_availability(self, availability: FacultyAvailability) -> FacultyAvailability:
        """Create faculty availability record."""
        self.db.add(availability)
        await self.db.flush()
        await self.db.refresh(availability)
        return availability
    
    async def get_by_faculty_id(self, faculty_id: int) -> FacultyAvailability | None:
        """Get faculty availability by faculty ID."""
        result = await self.db.execute(
            select(FacultyAvailability)
            .options(
                selectinload(FacultyAvailability.faculty),
                selectinload(FacultyAvailability.last_seen_building)
            )
            .where(FacultyAvailability.faculty_id == faculty_id)
        )
        return result.scalar_one_or_none()
    
    async def update_availability(self, availability: FacultyAvailability) -> FacultyAvailability:
        """Update faculty availability settings."""
        await self.db.flush()
        await self.db.refresh(availability)
        return availability
    
    async def update_last_seen(
        self, 
        faculty_id: int, 
        building_id: int, 
        floor: int | None = None
    ) -> FacultyAvailability | None:
        """Update faculty last-seen location."""
        availability = await self.get_by_faculty_id(faculty_id)
        if availability:
            availability.last_seen_building_id = building_id
            availability.last_seen_floor = floor
            availability.last_seen_at = datetime.now(timezone.utc)
            await self.db.flush()
            await self.db.refresh(availability)
        return availability
    
    async def get_visible_faculty(
        self,
        viewer_department: str | None = None,
        is_admin: bool = False,
        search_query: str | None = None,
        department_filter: str | None = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[tuple[FacultyAvailability, User]], int]:
        """
        Get faculty visible to the viewer based on visibility rules.
        Returns list of (FacultyAvailability, User) tuples and total count.
        """
        # Base query - only STAFF users with sharing enabled
        base_conditions = [
            FacultyAvailability.is_sharing_enabled == True,
            User.role == UserRole.STAFF,
            User.is_active == True
        ]
        
        # Visibility filtering based on viewer type
        if is_admin:
            # Admins can see all faculty with sharing enabled (not HIDDEN)
            base_conditions.append(
                FacultyAvailability.visibility_level != VisibilityLevel.HIDDEN
            )
        else:
            # Students - filter based on visibility level
            visibility_conditions = [
                FacultyAvailability.visibility_level == VisibilityLevel.ALL_STUDENTS
            ]
            # If student has a department, also show SAME_DEPARTMENT faculty
            if viewer_department:
                visibility_conditions.append(
                    (FacultyAvailability.visibility_level == VisibilityLevel.SAME_DEPARTMENT) &
                    (User.department == viewer_department)
                )
            
            from sqlalchemy import or_
            base_conditions.append(or_(*visibility_conditions))
        
        # Search filter
        if search_query:
            search_pattern = f"%{search_query}%"
            from sqlalchemy import or_
            base_conditions.append(
                or_(
                    User.first_name.ilike(search_pattern),
                    User.last_name.ilike(search_pattern),
                    User.department.ilike(search_pattern)
                )
            )
        
        # Department filter
        if department_filter:
            base_conditions.append(User.department == department_filter)
        
        # Count query
        count_stmt = (
            select(func.count())
            .select_from(FacultyAvailability)
            .join(User, FacultyAvailability.faculty_id == User.id)
            .where(*base_conditions)
        )
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0
        
        # Data query with pagination
        stmt = (
            select(FacultyAvailability, User)
            .join(User, FacultyAvailability.faculty_id == User.id)
            .options(selectinload(FacultyAvailability.last_seen_building))
            .where(*base_conditions)
            .order_by(User.first_name, User.last_name)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        
        return rows, total
    
    async def get_all_staff_faculty(self) -> list[tuple[FacultyAvailability | None, User]]:
        """Get all STAFF users with their availability (for admin view)."""
        # Get all staff users
        stmt = (
            select(User)
            .where(User.role == UserRole.STAFF, User.is_active == True)
            .order_by(User.first_name, User.last_name)
        )
        result = await self.db.execute(stmt)
        staff_users = list(result.scalars().all())
        
        # Get their availability records
        faculty_ids = [u.id for u in staff_users]
        avail_stmt = (
            select(FacultyAvailability)
            .options(selectinload(FacultyAvailability.last_seen_building))
            .where(FacultyAvailability.faculty_id.in_(faculty_ids))
        )
        avail_result = await self.db.execute(avail_stmt)
        avail_records = {a.faculty_id: a for a in avail_result.scalars().all()}
        
        # Combine
        return [(avail_records.get(u.id), u) for u in staff_users]
    
    async def get_faculty_stats(self) -> dict:
        """Get faculty availability statistics."""
        # Count all staff
        total_stmt = select(func.count()).select_from(User).where(
            User.role == UserRole.STAFF, User.is_active == True
        )
        total = (await self.db.execute(total_stmt)).scalar() or 0
        
        # Count by status
        stats_stmt = (
            select(
                FacultyAvailability.availability_status,
                FacultyAvailability.is_sharing_enabled,
                func.count()
            )
            .group_by(
                FacultyAvailability.availability_status,
                FacultyAvailability.is_sharing_enabled
            )
        )
        stats_result = await self.db.execute(stats_stmt)
        
        sharing_enabled = 0
        available = 0
        busy = 0
        offline = 0
        
        for status, sharing, count in stats_result.all():
            if sharing:
                sharing_enabled += count
            if status == AvailabilityStatus.AVAILABLE:
                available += count
            elif status == AvailabilityStatus.BUSY:
                busy += count
            elif status == AvailabilityStatus.OFFLINE:
                offline += count
        
        return {
            "total_faculty": total,
            "sharing_enabled_count": sharing_enabled,
            "available_count": available,
            "busy_count": busy,
            "offline_count": offline
        }
    
    async def get_faculty_departments(self) -> list[str]:
        """Get distinct departments that have faculty."""
        stmt = (
            select(User.department)
            .where(
                User.role == UserRole.STAFF,
                User.is_active == True,
                User.department.isnot(None)
            )
            .distinct()
            .order_by(User.department)
        )
        result = await self.db.execute(stmt)
        return [d for d in result.scalars().all() if d]
