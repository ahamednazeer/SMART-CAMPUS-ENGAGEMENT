"""
Attendance system repositories for database operations.
"""
from datetime import date, datetime, time
from typing import Optional, List
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.attendance import (
    ProfilePhoto, ProfilePhotoStatus,
    CampusGeofence, AttendanceWindow,
    AttendanceRecord, AttendanceStatus,
    AttendanceAttempt, FailureReason
)
from app.models.user import User, StudentCategory


class ProfilePhotoRepository:
    """Repository for profile photo operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, photo: ProfilePhoto) -> ProfilePhoto:
        """Create a new profile photo record."""
        self.db.add(photo)
        await self.db.flush()
        await self.db.refresh(photo)
        return photo
    
    async def get_by_id(self, photo_id: int) -> Optional[ProfilePhoto]:
        """Get profile photo by ID."""
        result = await self.db.execute(
            select(ProfilePhoto).where(ProfilePhoto.id == photo_id)
        )
        return result.scalar_one_or_none()
    
    async def get_approved_photo_for_student(self, student_id: int) -> Optional[ProfilePhoto]:
        """Get the approved profile photo for a student."""
        result = await self.db.execute(
            select(ProfilePhoto).where(
                and_(
                    ProfilePhoto.student_id == student_id,
                    ProfilePhoto.status == ProfilePhotoStatus.APPROVED
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_latest_photo_for_student(self, student_id: int) -> Optional[ProfilePhoto]:
        """Get the most recent profile photo for a student (any status)."""
        result = await self.db.execute(
            select(ProfilePhoto)
            .where(ProfilePhoto.student_id == student_id)
            .order_by(ProfilePhoto.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_pending_photos(self, skip: int = 0, limit: int = 50) -> List[ProfilePhoto]:
        """Get all pending profile photos for admin review."""
        result = await self.db.execute(
            select(ProfilePhoto)
            .where(ProfilePhoto.status == ProfilePhotoStatus.PENDING)
            .options(selectinload(ProfilePhoto.student))
            .order_by(ProfilePhoto.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def count_pending(self) -> int:
        """Count pending photos."""
        result = await self.db.execute(
            select(func.count(ProfilePhoto.id))
            .where(ProfilePhoto.status == ProfilePhotoStatus.PENDING)
        )
        return result.scalar() or 0
    
    async def update(self, photo: ProfilePhoto) -> ProfilePhoto:
        """Update a profile photo."""
        await self.db.flush()
        await self.db.refresh(photo)
        return photo


class GeofenceRepository:
    """Repository for geofence operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, geofence: CampusGeofence) -> CampusGeofence:
        """Create a new geofence."""
        self.db.add(geofence)
        await self.db.flush()
        await self.db.refresh(geofence)
        return geofence
    
    async def get_by_id(self, geofence_id: int) -> Optional[CampusGeofence]:
        """Get geofence by ID."""
        result = await self.db.execute(
            select(CampusGeofence).where(CampusGeofence.id == geofence_id)
        )
        return result.scalar_one_or_none()
    
    async def get_primary_active_geofence(self) -> Optional[CampusGeofence]:
        """Get the primary active geofence."""
        result = await self.db.execute(
            select(CampusGeofence).where(
                and_(
                    CampusGeofence.is_active == True,
                    CampusGeofence.is_primary == True
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_all_active(self) -> List[CampusGeofence]:
        """Get all active geofences."""
        result = await self.db.execute(
            select(CampusGeofence)
            .where(CampusGeofence.is_active == True)
            .order_by(CampusGeofence.is_primary.desc())
        )
        return list(result.scalars().all())
    
    async def get_all(self, skip: int = 0, limit: int = 50) -> List[CampusGeofence]:
        """Get all geofences."""
        result = await self.db.execute(
            select(CampusGeofence)
            .order_by(CampusGeofence.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def update(self, geofence: CampusGeofence) -> CampusGeofence:
        """Update a geofence."""
        await self.db.flush()
        await self.db.refresh(geofence)
        return geofence
    
    async def delete(self, geofence: CampusGeofence) -> None:
        """Delete a geofence."""
        await self.db.delete(geofence)
        await self.db.flush()


class AttendanceWindowRepository:
    """Repository for attendance window operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, window: AttendanceWindow) -> AttendanceWindow:
        """Create a new attendance window."""
        self.db.add(window)
        await self.db.flush()
        await self.db.refresh(window)
        return window
    
    async def get_by_id(self, window_id: int) -> Optional[AttendanceWindow]:
        """Get window by ID."""
        result = await self.db.execute(
            select(AttendanceWindow).where(AttendanceWindow.id == window_id)
        )
        return result.scalar_one_or_none()
    
    async def get_active_windows(
        self, 
        category: Optional[StudentCategory] = None
    ) -> List[AttendanceWindow]:
        """Get active attendance windows, optionally filtered by category."""
        query = select(AttendanceWindow).where(AttendanceWindow.is_active == True)
        
        if category:
            # Get windows that match category or have no category (applies to all)
            query = query.where(
                (AttendanceWindow.student_category == category.value) |
                (AttendanceWindow.student_category == None)
            )
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_all(self, skip: int = 0, limit: int = 50) -> List[AttendanceWindow]:
        """Get all attendance windows."""
        result = await self.db.execute(
            select(AttendanceWindow)
            .order_by(AttendanceWindow.start_time)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def update(self, window: AttendanceWindow) -> AttendanceWindow:
        """Update an attendance window."""
        await self.db.flush()
        await self.db.refresh(window)
        return window
    
    async def delete(self, window: AttendanceWindow) -> None:
        """Delete an attendance window."""
        await self.db.delete(window)
        await self.db.flush()


class AttendanceRecordRepository:
    """Repository for attendance record operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, record: AttendanceRecord) -> AttendanceRecord:
        """Create a new attendance record."""
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)
        return record
    
    async def get_by_id(self, record_id: int) -> Optional[AttendanceRecord]:
        """Get record by ID."""
        result = await self.db.execute(
            select(AttendanceRecord).where(AttendanceRecord.id == record_id)
        )
        return result.scalar_one_or_none()
    
    async def get_student_record_for_date(
        self, 
        student_id: int, 
        attendance_date: date
    ) -> Optional[AttendanceRecord]:
        """Get attendance record for a student on a specific date."""
        result = await self.db.execute(
            select(AttendanceRecord).where(
                and_(
                    AttendanceRecord.student_id == student_id,
                    AttendanceRecord.attendance_date == attendance_date
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_student_records(
        self, 
        student_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AttendanceRecord]:
        """Get attendance records for a student."""
        query = select(AttendanceRecord).where(
            AttendanceRecord.student_id == student_id
        )
        
        if start_date:
            query = query.where(AttendanceRecord.attendance_date >= start_date)
        if end_date:
            query = query.where(AttendanceRecord.attendance_date <= end_date)
        
        result = await self.db.execute(
            query.order_by(AttendanceRecord.attendance_date.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_records_for_date(
        self, 
        attendance_date: date,
        skip: int = 0,
        limit: int = 500
    ) -> List[AttendanceRecord]:
        """Get all attendance records for a specific date."""
        result = await self.db.execute(
            select(AttendanceRecord)
            .where(AttendanceRecord.attendance_date == attendance_date)
            .options(selectinload(AttendanceRecord.student))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def count_by_status_for_date(
        self, 
        attendance_date: date,
        status: AttendanceStatus
    ) -> int:
        """Count records with specific status for a date."""
        result = await self.db.execute(
            select(func.count(AttendanceRecord.id)).where(
                and_(
                    AttendanceRecord.attendance_date == attendance_date,
                    AttendanceRecord.status == status
                )
            )
        )
        return result.scalar() or 0
    
    async def update(self, record: AttendanceRecord) -> AttendanceRecord:
        """Update an attendance record."""
        await self.db.flush()
        await self.db.refresh(record)
        return record


class AttendanceAttemptRepository:
    """Repository for attendance attempt (audit log) operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, attempt: AttendanceAttempt) -> AttendanceAttempt:
        """Create a new attendance attempt log."""
        self.db.add(attempt)
        await self.db.flush()
        await self.db.refresh(attempt)
        return attempt
    
    async def get_student_attempts(
        self, 
        student_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[AttendanceAttempt]:
        """Get attempts for a student."""
        query = select(AttendanceAttempt).where(
            AttendanceAttempt.student_id == student_id
        )
        
        if start_date:
            query = query.where(AttendanceAttempt.attempted_at >= start_date)
        if end_date:
            query = query.where(AttendanceAttempt.attempted_at <= end_date)
        
        result = await self.db.execute(
            query.order_by(AttendanceAttempt.attempted_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_failed_attempts(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AttendanceAttempt]:
        """Get all failed attempts for admin review."""
        query = select(AttendanceAttempt).where(
            AttendanceAttempt.success == False
        ).options(selectinload(AttendanceAttempt.student))
        
        if start_date:
            query = query.where(AttendanceAttempt.attempted_at >= start_date)
        if end_date:
            query = query.where(AttendanceAttempt.attempted_at <= end_date)
        
        result = await self.db.execute(
            query.order_by(AttendanceAttempt.attempted_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def count_today_attempts(self, student_id: int) -> int:
        """Count attempts by a student today."""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self.db.execute(
            select(func.count(AttendanceAttempt.id)).where(
                and_(
                    AttendanceAttempt.student_id == student_id,
                    AttendanceAttempt.attempted_at >= today_start
                )
            )
        )
        return result.scalar() or 0
    
    async def count_failed_for_date(self, target_date: date) -> int:
        """Count failed attempts for a specific date."""
        start_dt = datetime.combine(target_date, time.min)
        end_dt = datetime.combine(target_date, time.max)
        
        result = await self.db.execute(
            select(func.count(AttendanceAttempt.id)).where(
                and_(
                    AttendanceAttempt.success == False,
                    AttendanceAttempt.attempted_at >= start_dt,
                    AttendanceAttempt.attempted_at <= end_dt
                )
            )
        )
        return result.scalar() or 0


class DetailedAttendanceRepository:
    """Repository for detailed attendance queries combining students and records."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_all_students_with_attendance_for_date(
        self, 
        attendance_date: date
    ) -> List[dict]:
        """
        Get all students with their attendance status for a specific date.
        Returns list of dicts with student info and attendance status.
        
        If attendance window is still open, unmarked students show as PENDING.
        After window closes, unmarked students show as ABSENT.
        """
        import json
        from datetime import datetime
        from app.models.user import User, UserRole
        
        # Get all students (including HOSTELLER and DAY_SCHOLAR roles)
        student_roles = [UserRole.STUDENT, UserRole.HOSTELLER, UserRole.DAY_SCHOLAR]
        
        # Query all active students
        students_result = await self.db.execute(
            select(User).where(
                and_(
                    User.role.in_(student_roles),
                    User.is_active == True
                )
            ).order_by(User.first_name, User.last_name)
        )
        students = list(students_result.scalars().all())
        
        # Query attendance records for the date
        records_result = await self.db.execute(
            select(AttendanceRecord).where(
                AttendanceRecord.attendance_date == attendance_date
            )
        )
        records = list(records_result.scalars().all())
        
        # Create a lookup dict for records
        records_by_student = {r.student_id: r for r in records}
        
        # Check if any attendance window is still open for today
        is_window_open = False
        if attendance_date == date.today():
            # Get active windows
            windows_result = await self.db.execute(
                select(AttendanceWindow).where(AttendanceWindow.is_active == True)
            )
            windows = list(windows_result.scalars().all())
            
            now = datetime.now()
            current_time = now.time()
            current_day = now.weekday()
            
            for window in windows:
                # Parse days of week
                days = json.loads(window.days_of_week) if isinstance(window.days_of_week, str) else window.days_of_week
                
                if current_day in days:
                    # Check if current time is before window end
                    if current_time <= window.end_time:
                        is_window_open = True
                        break
        
        # Build detailed list
        detailed_list = []
        for student in students:
            record = records_by_student.get(student.id)
            
            if record:
                # Student has a record
                status = record.status
            else:
                # No record - determine status based on window
                if is_window_open:
                    status = AttendanceStatus.PENDING
                else:
                    status = AttendanceStatus.ABSENT
            
            detailed_list.append({
                'student_id': student.id,
                'student_name': f"{student.first_name} {student.last_name}",
                'register_number': student.register_number,
                'department': student.department,
                'status': status,
                'marked_at': record.marked_at if record else None,
                'face_match_confidence': record.face_match_confidence if record else None
            })
        
        return detailed_list
    
    async def get_student_attendance_stats(
        self,
        student_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> dict:
        """
        Calculate attendance statistics for a student.
        Uses configured academic year dates from settings if no date range specified.
        """
        from datetime import timedelta
        
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            # Use configured academic year dates
            settings_repo = SettingsRepository(self.db)
            configured_start, configured_end = await settings_repo.get_academic_year_dates()
            start_date = configured_start
            # Don't go beyond end_date (today) if academic year end is in the future
            if end_date > configured_end:
                end_date = configured_end
        
        # Get all records for the student in date range
        records_result = await self.db.execute(
            select(AttendanceRecord).where(
                and_(
                    AttendanceRecord.student_id == student_id,
                    AttendanceRecord.attendance_date >= start_date,
                    AttendanceRecord.attendance_date <= end_date
                )
            ).order_by(AttendanceRecord.attendance_date.desc())
        )
        records = list(records_result.scalars().all())
        
        # Count present days
        present_count = sum(1 for r in records if r.status == AttendanceStatus.PRESENT)
        
        # Get holidays in the date range
        holiday_repo = HolidayRepository(self.db)
        holiday_dates = await holiday_repo.get_holiday_dates_in_range(start_date, end_date)
        
        # Calculate working days (excluding Sundays and holidays)
        total_working_days = 0
        current = start_date
        while current <= end_date:
            if current.weekday() != 6 and current not in holiday_dates:  # Exclude Sunday and holidays
                total_working_days += 1
            current += timedelta(days=1)
        
        absent_count = total_working_days - present_count
        if absent_count < 0:
            absent_count = 0
        
        percentage = (present_count / total_working_days * 100) if total_working_days > 0 else 0
        
        # Get holidays list
        holidays = await holiday_repo.get_holidays_in_range(start_date, end_date)
        
        # Synthesize full history including absent days
        records_by_date = {r.attendance_date: r for r in records}
        full_history = []
        current = end_date
        while current >= start_date:
            # Check if it's a working day
            if current.weekday() != 6 and current not in holiday_dates:
                if current in records_by_date:
                    full_history.append(records_by_date[current])
                elif current <= date.today():
                    # Virtual absent record
                    full_history.append({
                        'student_id': student_id,
                        'attendance_date': current,
                        'status': AttendanceStatus.ABSENT,
                        'marked_at': None,
                        'id': None
                    })
            current -= timedelta(days=1)

        return {
            'start_date': start_date,
            'end_date': end_date,
            'total_working_days': total_working_days,
            'holidays_count': len(holiday_dates),
            'present_days': present_count,
            'absent_days': absent_count,
            'attendance_percentage': round(percentage, 2),
            'records': full_history,
            'holidays': holidays
        }


class HolidayRepository:
    """Repository for holiday/calendar management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, holiday_data: dict, created_by: int) -> "Holiday":
        """Create a new holiday."""
        from app.models.attendance import Holiday
        
        holiday = Holiday(
            date=holiday_data['date'],
            name=holiday_data['name'],
            description=holiday_data.get('description'),
            holiday_type=holiday_data.get('holiday_type', 'GENERAL'),
            is_recurring=holiday_data.get('is_recurring', False),
            created_by=created_by
        )
        self.db.add(holiday)
        await self.db.commit()
        await self.db.refresh(holiday)
        return holiday
    
    async def get_by_id(self, holiday_id: int) -> Optional["Holiday"]:
        """Get holiday by ID."""
        from app.models.attendance import Holiday
        
        result = await self.db.execute(
            select(Holiday).where(Holiday.id == holiday_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_date(self, target_date: date) -> Optional["Holiday"]:
        """Get holiday by date."""
        from app.models.attendance import Holiday
        
        result = await self.db.execute(
            select(Holiday).where(
                and_(
                    Holiday.date == target_date,
                    Holiday.is_active == True
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_holidays_in_range(
        self,
        start_date: date,
        end_date: date
    ) -> List["Holiday"]:
        """Get all holidays within a date range."""
        from app.models.attendance import Holiday
        
        result = await self.db.execute(
            select(Holiday).where(
                and_(
                    Holiday.date >= start_date,
                    Holiday.date <= end_date,
                    Holiday.is_active == True
                )
            ).order_by(Holiday.date)
        )
        return list(result.scalars().all())
    
    async def get_holiday_dates_in_range(
        self,
        start_date: date,
        end_date: date
    ) -> set:
        """Get set of holiday dates within a date range."""
        holidays = await self.get_holidays_in_range(start_date, end_date)
        return {h.date for h in holidays}
    
    async def get_all_active(self, skip: int = 0, limit: int = 100) -> List["Holiday"]:
        """Get all active holidays."""
        from app.models.attendance import Holiday
        
        result = await self.db.execute(
            select(Holiday).where(Holiday.is_active == True)
            .order_by(Holiday.date.desc())
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())
    
    async def delete(self, holiday_id: int) -> bool:
        """Delete a holiday (soft delete by setting is_active=False)."""
        from app.models.attendance import Holiday
        
        result = await self.db.execute(
            select(Holiday).where(Holiday.id == holiday_id)
        )
        holiday = result.scalar_one_or_none()
        if not holiday:
            return False
        
        holiday.is_active = False
        await self.db.commit()
        return True
    
    async def hard_delete(self, holiday_id: int) -> bool:
        """Permanently delete a holiday."""
        from app.models.attendance import Holiday
        
        result = await self.db.execute(
            select(Holiday).where(Holiday.id == holiday_id)
        )
        holiday = result.scalar_one_or_none()
        if not holiday:
            return False
        
        await self.db.delete(holiday)
        await self.db.commit()
        return True


class SettingsRepository:
    """Repository for attendance settings management."""
    
    ACADEMIC_YEAR_START = "academic_year_start"
    ACADEMIC_YEAR_END = "academic_year_end"
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_setting(self, key: str) -> Optional[str]:
        """Get a setting value by key."""
        from app.models.attendance import AttendanceSettings
        
        result = await self.db.execute(
            select(AttendanceSettings).where(AttendanceSettings.key == key)
        )
        setting = result.scalar_one_or_none()
        return setting.value if setting else None
    
    async def set_setting(self, key: str, value: str, description: str = None, updated_by: int = None):
        """Set a setting value."""
        from app.models.attendance import AttendanceSettings
        
        result = await self.db.execute(
            select(AttendanceSettings).where(AttendanceSettings.key == key)
        )
        setting = result.scalar_one_or_none()
        
        if setting:
            setting.value = value
            setting.updated_by = updated_by
            if description:
                setting.description = description
        else:
            setting = AttendanceSettings(
                key=key,
                value=value,
                description=description,
                updated_by=updated_by
            )
            self.db.add(setting)
        
        await self.db.commit()
        await self.db.refresh(setting)
        return setting
    
    async def get_academic_year_dates(self) -> tuple:
        """Get the configured academic year start and end dates."""
        from datetime import datetime
        
        start_str = await self.get_setting(self.ACADEMIC_YEAR_START)
        end_str = await self.get_setting(self.ACADEMIC_YEAR_END)
        
        # Default to July 1 to June 30 if not configured
        today = date.today()
        if today.month >= 7:
            default_start = date(today.year, 7, 1)
            default_end = date(today.year + 1, 6, 30)
        else:
            default_start = date(today.year - 1, 7, 1)
            default_end = date(today.year, 6, 30)
        
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date() if start_str else default_start
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date() if end_str else default_end
        
        return start_date, end_date
    
    async def set_academic_year_dates(self, start_date: date, end_date: date, updated_by: int = None):
        """Set the academic year start and end dates."""
        await self.set_setting(
            self.ACADEMIC_YEAR_START,
            start_date.strftime("%Y-%m-%d"),
            "Academic year start date",
            updated_by
        )
        await self.set_setting(
            self.ACADEMIC_YEAR_END,
            end_date.strftime("%Y-%m-%d"),
            "Academic year end date",
            updated_by
        )
        return start_date, end_date
