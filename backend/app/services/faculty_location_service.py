"""Service for Faculty Location & Availability module."""
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.faculty_location_repository import FacultyLocationRepository
from app.models.faculty_location import (
    CampusBuilding, FacultyAvailability, 
    AvailabilityStatus, VisibilityLevel
)
from app.schemas.faculty_location import (
    CampusBuildingCreate, CampusBuildingUpdate,
    FacultyAvailabilityUpdate, FacultyLocationRefresh,
    FacultyLocationOut, FacultySettingsOut
)


class FacultyLocationService:
    """Service for managing faculty location and availability."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = FacultyLocationRepository(db)
    
    # ============ Campus Building Operations ============
    
    async def create_building(
        self, 
        data: CampusBuildingCreate
    ) -> CampusBuilding:
        """Create a new campus building (admin only)."""
        building = CampusBuilding(
            name=data.name,
            code=data.code.upper(),
            description=data.description,
            floor_count=data.floor_count
        )
        return await self.repo.create_building(building)
    
    async def get_all_buildings(self, include_inactive: bool = False) -> list[CampusBuilding]:
        """Get all campus buildings."""
        return await self.repo.get_all_buildings(include_inactive)
    
    async def update_building(
        self, 
        building_id: int, 
        data: CampusBuildingUpdate
    ) -> CampusBuilding:
        """Update a campus building."""
        building = await self.repo.get_building_by_id(building_id)
        if not building:
            raise ValueError("Building not found")
        
        if data.name is not None:
            building.name = data.name
        if data.code is not None:
            building.code = data.code.upper()
        if data.description is not None:
            building.description = data.description
        if data.floor_count is not None:
            building.floor_count = data.floor_count
        if data.is_active is not None:
            building.is_active = data.is_active
        
        return await self.repo.update_building(building)
    
    async def delete_building(self, building_id: int) -> bool:
        """Soft delete a campus building."""
        return await self.repo.delete_building(building_id)
    
    # ============ Faculty Availability Operations ============
    
    async def get_or_create_availability(
        self, 
        faculty_id: int
    ) -> FacultyAvailability:
        """Get or create faculty availability record."""
        availability = await self.repo.get_by_faculty_id(faculty_id)
        if not availability:
            # Create default settings (sharing OFF by default)
            availability = FacultyAvailability(
                faculty_id=faculty_id,
                is_sharing_enabled=False,
                availability_status=AvailabilityStatus.OFFLINE,
                visibility_level=VisibilityLevel.ALL_STUDENTS
            )
            availability = await self.repo.create_availability(availability)
        return availability
    
    async def get_faculty_settings(self, faculty_id: int) -> FacultyAvailability:
        """Get faculty's own settings."""
        return await self.get_or_create_availability(faculty_id)
    
    async def update_faculty_settings(
        self, 
        faculty_id: int, 
        data: FacultyAvailabilityUpdate
    ) -> FacultyAvailability:
        """Update faculty availability settings."""
        availability = await self.get_or_create_availability(faculty_id)
        
        if data.is_sharing_enabled is not None:
            availability.is_sharing_enabled = data.is_sharing_enabled
        if data.availability_status is not None:
            availability.availability_status = data.availability_status
        if data.visibility_level is not None:
            availability.visibility_level = data.visibility_level
        if data.status_message is not None:
            availability.status_message = data.status_message
        
        return await self.repo.update_availability(availability)
    
    async def refresh_location(
        self, 
        faculty_id: int, 
        data: FacultyLocationRefresh
    ) -> FacultyAvailability:
        """Manually refresh faculty's last-seen location."""
        # Verify building exists
        building = await self.repo.get_building_by_id(data.building_id)
        if not building:
            raise ValueError("Building not found")
        if not building.is_active:
            raise ValueError("Building is not active")
        
        # Validate floor
        if data.floor and data.floor > building.floor_count:
            raise ValueError(f"Floor must be between 1 and {building.floor_count}")
        
        availability = await self.repo.update_last_seen(
            faculty_id, 
            data.building_id, 
            data.floor
        )
        
        if not availability:
            # Create availability record first
            await self.get_or_create_availability(faculty_id)
            availability = await self.repo.update_last_seen(
                faculty_id, 
                data.building_id, 
                data.floor
            )
        
        return availability
    
    # ============ Student View Operations ============
    
    async def get_available_faculty(
        self,
        viewer_department: str | None = None,
        is_admin: bool = False,
        search_query: str | None = None,
        department_filter: str | None = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[FacultyLocationOut], int]:
        """Get list of visible faculty for students."""
        rows, total = await self.repo.get_visible_faculty(
            viewer_department=viewer_department,
            is_admin=is_admin,
            search_query=search_query,
            department_filter=department_filter,
            page=page,
            page_size=page_size
        )
        
        faculty_list = []
        now = datetime.now(timezone.utc)
        
        for availability, user in rows:
            # Calculate time since last seen
            last_seen_minutes_ago = None
            if availability.last_seen_at:
                delta = now - availability.last_seen_at
                last_seen_minutes_ago = int(delta.total_seconds() / 60)
            
            faculty_list.append(FacultyLocationOut(
                faculty_id=user.id,
                faculty_name=f"{user.first_name} {user.last_name}",
                department=user.department,
                availability_status=availability.availability_status,
                status_message=availability.status_message,
                last_seen_building_name=availability.last_seen_building.name if availability.last_seen_building else None,
                last_seen_floor=availability.last_seen_floor,
                last_seen_at=availability.last_seen_at,
                last_seen_minutes_ago=last_seen_minutes_ago
            ))
        
        return faculty_list, total
    
    async def get_faculty_by_id(
        self,
        faculty_id: int,
        viewer_department: str | None = None,
        is_admin: bool = False
    ) -> FacultyLocationOut | None:
        """Get specific faculty info for students."""
        availability = await self.repo.get_by_faculty_id(faculty_id)
        if not availability:
            return None
        
        # Check visibility
        if not availability.is_sharing_enabled:
            return None
        
        if availability.visibility_level == VisibilityLevel.HIDDEN:
            return None
        
        if availability.visibility_level == VisibilityLevel.ADMIN_ONLY and not is_admin:
            return None
        
        if availability.visibility_level == VisibilityLevel.SAME_DEPARTMENT:
            if not is_admin and viewer_department != availability.faculty.department:
                return None
        
        # Calculate time since last seen
        now = datetime.now(timezone.utc)
        last_seen_minutes_ago = None
        if availability.last_seen_at:
            delta = now - availability.last_seen_at
            last_seen_minutes_ago = int(delta.total_seconds() / 60)
        
        return FacultyLocationOut(
            faculty_id=availability.faculty.id,
            faculty_name=f"{availability.faculty.first_name} {availability.faculty.last_name}",
            department=availability.faculty.department,
            availability_status=availability.availability_status,
            status_message=availability.status_message,
            last_seen_building_name=availability.last_seen_building.name if availability.last_seen_building else None,
            last_seen_floor=availability.last_seen_floor,
            last_seen_at=availability.last_seen_at,
            last_seen_minutes_ago=last_seen_minutes_ago
        )
    
    # ============ Admin Operations ============
    
    async def get_all_faculty_for_admin(self) -> list:
        """Get all faculty with their settings for admin."""
        from app.schemas.faculty_location import AdminFacultyLocationOut
        
        rows = await self.repo.get_all_staff_faculty()
        result = []
        
        for availability, user in rows:
            result.append(AdminFacultyLocationOut(
                faculty_id=user.id,
                username=user.username,
                faculty_name=f"{user.first_name} {user.last_name}",
                email=user.email,
                department=user.department,
                is_sharing_enabled=availability.is_sharing_enabled if availability else False,
                availability_status=availability.availability_status if availability else AvailabilityStatus.OFFLINE,
                visibility_level=availability.visibility_level if availability else VisibilityLevel.ALL_STUDENTS,
                status_message=availability.status_message if availability else None,
                last_seen_building_name=availability.last_seen_building.name if availability and availability.last_seen_building else None,
                last_seen_at=availability.last_seen_at if availability else None,
                created_at=availability.created_at if availability else user.created_at,
                updated_at=availability.updated_at if availability else user.updated_at
            ))
        
        return result
    
    async def get_faculty_stats(self) -> dict:
        """Get faculty location statistics for admin."""
        return await self.repo.get_faculty_stats()
    
    async def get_faculty_departments(self) -> list[str]:
        """Get list of departments that have faculty."""
        return await self.repo.get_faculty_departments()
