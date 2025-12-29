"""
Attendance service for handling attendance marking with location and face verification.
"""
import os
import math
import json
import aiofiles
from datetime import date, datetime, time
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from app.core.config import settings
from app.models.attendance import (
    ProfilePhoto, ProfilePhotoStatus,
    CampusGeofence, AttendanceWindow,
    AttendanceRecord, AttendanceStatus,
    AttendanceAttempt, FailureReason
)
from app.models.user import User, StudentCategory
from app.repositories.attendance_repository import (
    ProfilePhotoRepository,
    GeofenceRepository,
    AttendanceWindowRepository,
    AttendanceRecordRepository,
    AttendanceAttemptRepository
)
from app.services.face_recognition_service import get_face_recognition_service, FaceRecognitionService
from app.schemas.attendance import (
    ProfilePhotoOut, ProfilePhotoApproval,
    GeofenceCreate, GeofenceOut, GeofenceUpdate,
    AttendanceWindowCreate, AttendanceWindowOut,
    LocationData, AttendancePreCheckOut, AttendanceMarkResult,
    AttendanceRecordOut, AttendanceAttemptOut,
    AttendanceDashboardStats
)


class AttendanceService:
    """Service for attendance operations with location and face verification."""
    
    # Maximum attempts per day
    MAX_DAILY_ATTEMPTS = 5
    
    # Upload directories
    PROFILE_PHOTOS_DIR = "profile_photos"
    ATTENDANCE_CAPTURES_DIR = "attendance_captures"
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.photo_repo = ProfilePhotoRepository(db)
        self.geofence_repo = GeofenceRepository(db)
        self.window_repo = AttendanceWindowRepository(db)
        self.record_repo = AttendanceRecordRepository(db)
        self.attempt_repo = AttendanceAttemptRepository(db)
        self.face_service = get_face_recognition_service()
    
    # ============== Helper Methods ==============
    
    def _get_upload_dir(self, subdir: str) -> str:
        """Get upload directory path."""
        path = os.path.join(settings.UPLOAD_DIR, subdir)
        os.makedirs(path, exist_ok=True)
        return path
    
    @staticmethod
    def _haversine_distance(
        lat1: float, lon1: float,
        lat2: float, lon2: float
    ) -> float:
        """
        Calculate the great-circle distance between two points on Earth.
        
        Returns distance in meters.
        """
        R = 6371000  # Earth's radius in meters
        
        # Convert to radians
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        # Haversine formula
        a = (
            math.sin(delta_phi / 2) ** 2 +
            math.cos(phi1) * math.cos(phi2) *
            math.sin(delta_lambda / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _is_within_geofence(
        self,
        location: LocationData,
        geofence: CampusGeofence
    ) -> Tuple[bool, float]:
        """
        Check if location is within geofence.
        
        Returns (is_within, distance_from_center)
        """
        distance = self._haversine_distance(
            location.latitude, location.longitude,
            geofence.latitude, geofence.longitude
        )
        is_within = distance <= geofence.radius_meters
        return is_within, distance
    
    def _is_within_time_window(
        self,
        windows: List[AttendanceWindow],
        current_time: time,
        current_day: int  # 0=Monday, 6=Sunday
    ) -> bool:
        """Check if current time is within any active window."""
        for window in windows:
            # Parse days of week
            days = json.loads(window.days_of_week) if isinstance(window.days_of_week, str) else window.days_of_week
            
            if current_day not in days:
                continue
            
            if window.start_time <= current_time <= window.end_time:
                return True
        
        return False
    
    # ============== Profile Photo Management ==============
    
    async def upload_profile_photo(
        self,
        student: User,
        file: UploadFile
    ) -> ProfilePhotoOut:
        """Upload a profile photo for face recognition reference."""
        
        # Save file
        upload_dir = self._get_upload_dir(self.PROFILE_PHOTOS_DIR)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{student.id}_{timestamp}_{file.filename}"
        file_path = os.path.join(upload_dir, safe_filename)
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Validate face in image
        is_valid, error_msg = self.face_service.validate_face_image(file_path)
        
        if not is_valid:
            # Delete the file if face validation fails
            os.remove(file_path)
            raise ValueError(f"Invalid profile photo: {error_msg}")
        
        # Extract face encoding for future matching
        encoding = self.face_service.extract_face_encoding(file_path)
        if encoding is None:
            os.remove(file_path)
            raise ValueError("Could not extract face encoding from image")
        
        # Create photo record
        photo = ProfilePhoto(
            student_id=student.id,
            file_path=file_path,
            filename=safe_filename,
            face_encoding=FaceRecognitionService.encoding_to_json(encoding),
            status=ProfilePhotoStatus.PENDING
        )
        
        photo = await self.photo_repo.create(photo)
        return ProfilePhotoOut.model_validate(photo)
    
    async def get_profile_photo_status(self, student_id: int) -> Optional[ProfilePhotoOut]:
        """Get the latest profile photo status for a student."""
        photo = await self.photo_repo.get_latest_photo_for_student(student_id)
        if photo:
            return ProfilePhotoOut.model_validate(photo)
        return None
    
    async def get_pending_photos(
        self, skip: int = 0, limit: int = 50
    ) -> Tuple[List[ProfilePhotoOut], int]:
        """Get pending photos for admin review."""
        photos = await self.photo_repo.get_pending_photos(skip, limit)
        total = await self.photo_repo.count_pending()
        return [ProfilePhotoOut.model_validate(p) for p in photos], total
    
    async def review_profile_photo(
        self,
        photo_id: int,
        reviewer: User,
        approval: ProfilePhotoApproval
    ) -> ProfilePhotoOut:
        """Admin reviews (approves/rejects) a profile photo."""
        photo = await self.photo_repo.get_by_id(photo_id)
        if not photo:
            raise ValueError("Profile photo not found")
        
        if photo.status != ProfilePhotoStatus.PENDING:
            raise ValueError("Photo has already been reviewed")
        
        if approval.approved:
            # Before approving, reject any existing approved photo for this student
            # This prevents the unique constraint violation
            existing_approved = await self.photo_repo.get_approved_photo_for_student(photo.student_id)
            if existing_approved and existing_approved.id != photo.id:
                existing_approved.status = ProfilePhotoStatus.REJECTED
                existing_approved.rejection_reason = "Replaced by new approved photo"
                await self.photo_repo.update(existing_approved)
            
            photo.status = ProfilePhotoStatus.APPROVED
        else:
            photo.status = ProfilePhotoStatus.REJECTED
            photo.rejection_reason = approval.rejection_reason or "Photo rejected by admin"
        
        photo.reviewed_by = reviewer.id
        photo.reviewed_at = datetime.now()
        
        photo = await self.photo_repo.update(photo)
        return ProfilePhotoOut.model_validate(photo)
    
    # ============== Geofence Management ==============
    
    async def create_geofence(
        self,
        data: GeofenceCreate,
        admin: User
    ) -> GeofenceOut:
        """Create a new campus geofence."""
        geofence = CampusGeofence(
            name=data.name,
            description=data.description,
            latitude=data.latitude,
            longitude=data.longitude,
            radius_meters=data.radius_meters,
            accuracy_threshold=data.accuracy_threshold,
            is_primary=data.is_primary,
            created_by=admin.id
        )
        
        # If this is primary, unset other primary geofences
        if data.is_primary:
            existing_primary = await self.geofence_repo.get_primary_active_geofence()
            if existing_primary:
                existing_primary.is_primary = False
                await self.geofence_repo.update(existing_primary)
        
        geofence = await self.geofence_repo.create(geofence)
        return GeofenceOut.model_validate(geofence)
    
    async def get_geofences(self) -> List[GeofenceOut]:
        """Get all geofences."""
        geofences = await self.geofence_repo.get_all()
        return [GeofenceOut.model_validate(g) for g in geofences]
    
    async def update_geofence(
        self,
        geofence_id: int,
        data: GeofenceUpdate
    ) -> GeofenceOut:
        """Update a geofence."""
        geofence = await self.geofence_repo.get_by_id(geofence_id)
        if not geofence:
            raise ValueError("Geofence not found")
        
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(geofence, field, value)
        
        geofence = await self.geofence_repo.update(geofence)
        return GeofenceOut.model_validate(geofence)
    
    async def delete_geofence(self, geofence_id: int) -> None:
        """Delete a geofence."""
        geofence = await self.geofence_repo.get_by_id(geofence_id)
        if not geofence:
            raise ValueError("Geofence not found")
        await self.geofence_repo.delete(geofence)
    
    # ============== Attendance Window Management ==============
    
    async def create_attendance_window(
        self,
        data: AttendanceWindowCreate
    ) -> AttendanceWindowOut:
        """Create a new attendance time window."""
        window = AttendanceWindow(
            name=data.name,
            start_time=data.start_time,
            end_time=data.end_time,
            days_of_week=json.dumps(data.days_of_week),
            student_category=data.student_category,
            is_active=data.is_active
        )
        window = await self.window_repo.create(window)
        return AttendanceWindowOut.model_validate(window)
    
    async def get_attendance_windows(self) -> List[AttendanceWindowOut]:
        """Get all attendance windows."""
        windows = await self.window_repo.get_all()
        return [AttendanceWindowOut.model_validate(w) for w in windows]
    
    async def delete_attendance_window(self, window_id: int) -> None:
        """Delete an attendance window."""
        window = await self.window_repo.get_by_id(window_id)
        if not window:
            raise ValueError("Attendance window not found")
        await self.window_repo.delete(window)
    
    # ============== Attendance Pre-Check ==============
    
    async def check_attendance_prerequisites(
        self,
        student: User
    ) -> AttendancePreCheckOut:
        """Check if student can mark attendance."""
        blockers = []
        today = date.today()
        
        # Check 0: Not Sunday
        is_sunday = today.weekday() == 6
        if is_sunday:
            blockers.append("Attendance is not required on Sundays")
        
        # Check 0.5: Not a Holiday
        from app.repositories.attendance_repository import HolidayRepository
        holiday_repo = HolidayRepository(self.db)
        holiday = await holiday_repo.get_by_date(today)
        is_holiday = holiday is not None
        if is_holiday:
            blockers.append(f"Today is a holiday: {holiday.name}")
        
        # Check 1: Profile photo approved
        approved_photo = await self.photo_repo.get_approved_photo_for_student(student.id)
        profile_approved = approved_photo is not None
        if not profile_approved:
            blockers.append("Profile photo not approved")
        
        # Check 2: Within time window
        now = datetime.now()
        current_time = now.time()
        current_day = now.weekday()
        
        windows = await self.window_repo.get_active_windows(student.student_category)
        within_time_window = self._is_within_time_window(windows, current_time, current_day)
        if not within_time_window:
            blockers.append("Outside attendance time window")
        
        # Check 3: Not already marked today
        today = date.today()
        existing_record = await self.record_repo.get_student_record_for_date(student.id, today)
        already_marked_today = (
            existing_record is not None and 
            existing_record.status == AttendanceStatus.PRESENT
        )
        if already_marked_today:
            blockers.append("Attendance already marked today")
        
        # Check 4: Attempt limit
        attempt_count = await self.attempt_repo.count_today_attempts(student.id)
        if attempt_count >= self.MAX_DAILY_ATTEMPTS:
            blockers.append(f"Maximum attempts ({self.MAX_DAILY_ATTEMPTS}) reached for today")
        
        # Check 5: Geofence exists
        primary_geofence = await self.geofence_repo.get_primary_active_geofence()
        if not primary_geofence:
            blockers.append("Campus geofence not configured")
        
        can_mark = len(blockers) == 0
        
        return AttendancePreCheckOut(
            can_mark=can_mark,
            blockers=blockers,
            profile_approved=profile_approved,
            within_time_window=within_time_window,
            already_marked_today=already_marked_today
        )
    
    # ============== Attendance Marking ==============
    
    async def mark_attendance(
        self,
        student: User,
        location: LocationData,
        image_file: UploadFile
    ) -> AttendanceMarkResult:
        """
        Mark attendance with location and face verification.
        
        This is the main attendance flow:
        1. Verify location is within campus
        2. Save captured image
        3. Verify face matches profile photo
        4. Create attendance record
        """
        today = date.today()
        now = datetime.now()
        
        # Initialize attempt log
        attempt = AttendanceAttempt(
            student_id=student.id,
            location_latitude=location.latitude,
            location_longitude=location.longitude,
            location_accuracy=location.accuracy
        )
        
        # GATE 1: Location Verification
        geofence = await self.geofence_repo.get_primary_active_geofence()
        if not geofence:
            attempt.success = False
            attempt.failure_reason = FailureReason.OUTSIDE_CAMPUS
            attempt.failure_details = "Campus geofence not configured"
            attempt.geofence_id = None
            await self.attempt_repo.create(attempt)
            return AttendanceMarkResult(
                success=False,
                message="Campus geofence not configured",
                failure_reason=FailureReason.OUTSIDE_CAMPUS
            )
        
        attempt.geofence_id = geofence.id
        
        # Check GPS accuracy
        if location.accuracy > geofence.accuracy_threshold:
            attempt.success = False
            attempt.failure_reason = FailureReason.LOW_GPS_ACCURACY
            attempt.failure_details = f"GPS accuracy {location.accuracy}m exceeds threshold {geofence.accuracy_threshold}m"
            await self.attempt_repo.create(attempt)
            return AttendanceMarkResult(
                success=False,
                message=f"GPS accuracy too low. Please move to an open area.",
                failure_reason=FailureReason.LOW_GPS_ACCURACY
            )
        
        # Check if within campus
        is_within, distance = self._is_within_geofence(location, geofence)
        if not is_within:
            attempt.success = False
            attempt.failure_reason = FailureReason.OUTSIDE_CAMPUS
            attempt.failure_details = f"Distance from campus center: {distance:.0f}m (radius: {geofence.radius_meters}m)"
            await self.attempt_repo.create(attempt)
            return AttendanceMarkResult(
                success=False,
                message="You are outside the campus boundary",
                failure_reason=FailureReason.OUTSIDE_CAMPUS
            )
        
        # GATE 2: Save and validate captured image
        upload_dir = self._get_upload_dir(self.ATTENDANCE_CAPTURES_DIR)
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        capture_filename = f"{student.id}_{timestamp}_{image_file.filename}"
        capture_path = os.path.join(upload_dir, capture_filename)
        
        async with aiofiles.open(capture_path, 'wb') as f:
            content = await image_file.read()
            await f.write(content)
        
        attempt.captured_image_path = capture_path
        
        # Validate face in captured image
        face_count = self.face_service.detect_faces(capture_path)
        
        if face_count == 0:
            attempt.success = False
            attempt.failure_reason = FailureReason.NO_FACE_DETECTED
            attempt.failure_details = "No face detected in captured image"
            await self.attempt_repo.create(attempt)
            return AttendanceMarkResult(
                success=False,
                message="No face detected. Please ensure your face is clearly visible.",
                failure_reason=FailureReason.NO_FACE_DETECTED
            )
        
        if face_count > 1:
            attempt.success = False
            attempt.failure_reason = FailureReason.MULTIPLE_FACES
            attempt.failure_details = f"{face_count} faces detected"
            await self.attempt_repo.create(attempt)
            return AttendanceMarkResult(
                success=False,
                message="Multiple faces detected. Only you should be in the frame.",
                failure_reason=FailureReason.MULTIPLE_FACES
            )
        
        # GATE 3: Face Matching
        approved_photo = await self.photo_repo.get_approved_photo_for_student(student.id)
        if not approved_photo:
            attempt.success = False
            attempt.failure_reason = FailureReason.PROFILE_NOT_APPROVED
            await self.attempt_repo.create(attempt)
            return AttendanceMarkResult(
                success=False,
                message="Profile photo not approved",
                failure_reason=FailureReason.PROFILE_NOT_APPROVED
            )
        
        # Compare faces
        is_match, similarity_score, message = self.face_service.verify_face(
            approved_photo.file_path,
            capture_path
        )
        
        attempt.face_match_score = similarity_score
        
        if not is_match:
            attempt.success = False
            attempt.failure_reason = FailureReason.FACE_MISMATCH
            attempt.failure_details = f"Face match score: {similarity_score}"
            await self.attempt_repo.create(attempt)
            return AttendanceMarkResult(
                success=False,
                message="Face verification failed. Please try again.",
                failure_reason=FailureReason.FACE_MISMATCH,
                face_match_score=similarity_score
            )
        
        # SUCCESS: All gates passed
        attempt.success = True
        await self.attempt_repo.create(attempt)
        
        # Create or update attendance record
        existing_record = await self.record_repo.get_student_record_for_date(student.id, today)
        
        if existing_record:
            existing_record.status = AttendanceStatus.PRESENT
            existing_record.marked_at = now
            existing_record.location_latitude = location.latitude
            existing_record.location_longitude = location.longitude
            existing_record.location_accuracy = location.accuracy
            existing_record.face_match_confidence = similarity_score
            await self.record_repo.update(existing_record)
        else:
            record = AttendanceRecord(
                student_id=student.id,
                attendance_date=today,
                status=AttendanceStatus.PRESENT,
                marked_at=now,
                location_latitude=location.latitude,
                location_longitude=location.longitude,
                location_accuracy=location.accuracy,
                face_match_confidence=similarity_score
            )
            await self.record_repo.create(record)
        
        return AttendanceMarkResult(
            success=True,
            message="Attendance marked successfully!",
            attendance_status=AttendanceStatus.PRESENT,
            face_match_score=similarity_score
        )
    
    # ============== Attendance Records ==============
    
    async def get_student_attendance_history(
        self,
        student_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[AttendanceRecordOut]:
        """Get attendance history for a student including synthesized Absent records."""
        from app.repositories.attendance_repository import DetailedAttendanceRepository
        
        detailed_repo = DetailedAttendanceRepository(self.db)
        stats = await detailed_repo.get_student_attendance_stats(
            student_id, start_date, end_date
        )
        
        return [
            AttendanceRecordOut.model_validate(r) if not isinstance(r, dict)
            else AttendanceRecordOut(**r)
            for r in stats['records']
        ]
    
    async def get_student_attempts(
        self,
        student_id: int
    ) -> List[AttendanceAttemptOut]:
        """Get attendance attempts for a student."""
        attempts = await self.attempt_repo.get_student_attempts(student_id)
        return [AttendanceAttemptOut.model_validate(a) for a in attempts]
    
    async def get_today_status(self, student_id: int) -> Optional[AttendanceRecordOut]:
        """Get today's attendance status for a student."""
        today = date.today()
        record = await self.record_repo.get_student_record_for_date(student_id, today)
        if record:
            return AttendanceRecordOut.model_validate(record)
        return None
    
    # ============== Admin Dashboard ==============
    
    async def get_dashboard_stats(
        self,
        target_date: date
    ) -> AttendanceDashboardStats:
        """Get attendance dashboard statistics."""
        from app.repositories.user_repository import UserRepository
        
        user_repo = UserRepository(self.db)
        
        # Get student count - count_by_role returns a dict like {"STUDENT": 10, "ADMIN": 1}
        role_counts = await user_repo.count_by_role()
        # Sum all student-type roles
        total_students = (
            role_counts.get("STUDENT", 0) +
            role_counts.get("HOSTELLER", 0) +
            role_counts.get("DAY_SCHOLAR", 0)
        )
        
        # Get attendance counts
        present_count = await self.record_repo.count_by_status_for_date(
            target_date, AttendanceStatus.PRESENT
        )
        absent_count = total_students - present_count
        
        # Get failed attempts count
        failed_count = await self.attempt_repo.count_failed_for_date(target_date)
        
        # Calculate percentage
        percentage = (present_count / total_students * 100) if total_students > 0 else 0
        
        return AttendanceDashboardStats(
            date=target_date,
            total_students=total_students,
            present_count=present_count,
            absent_count=absent_count,
            failed_attempts_count=failed_count,
            attendance_percentage=round(percentage, 2)
        )
    
    async def get_all_records_for_date(
        self,
        target_date: date
    ) -> List[AttendanceRecordOut]:
        """Get all attendance records for a date."""
        records = await self.record_repo.get_records_for_date(target_date)
        return [AttendanceRecordOut.model_validate(r) for r in records]
    
    async def get_failed_attempts(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AttendanceAttemptOut]:
        """Get all failed attempts for admin review."""
        attempts = await self.attempt_repo.get_failed_attempts(start_date, end_date)
        return [AttendanceAttemptOut.model_validate(a) for a in attempts]
    
    # ============== Detailed Attendance Methods ==============
    
    async def get_detailed_attendance_for_date(
        self,
        target_date: date
    ):
        """
        Get detailed student-by-student attendance for a date.
        Returns all students with their present/pending/absent status.
        """
        from app.repositories.attendance_repository import DetailedAttendanceRepository
        from app.schemas.attendance import StudentDetailedAttendance, DetailedAttendanceListOut
        
        detailed_repo = DetailedAttendanceRepository(self.db)
        students_data = await detailed_repo.get_all_students_with_attendance_for_date(target_date)
        
        students = [StudentDetailedAttendance(**s) for s in students_data]
        present_count = sum(1 for s in students if s.status.value == 'PRESENT')
        pending_count = sum(1 for s in students if s.status.value == 'PENDING')
        absent_count = sum(1 for s in students if s.status.value == 'ABSENT')
        
        return DetailedAttendanceListOut(
            date=target_date,
            students=students,
            present_count=present_count,
            absent_count=absent_count,
            pending_count=pending_count,
            total_students=len(students)
        )
    
    async def get_my_attendance_stats(
        self,
        student: User,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ):
        """
        Get attendance statistics for a student.
        Returns total days, present, absent, percentage, and recent records.
        """
        from app.repositories.attendance_repository import DetailedAttendanceRepository
        from app.schemas.attendance import StudentAttendanceStatsOut, AttendanceRecordOut, HolidayOut
        
        detailed_repo = DetailedAttendanceRepository(self.db)
        stats = await detailed_repo.get_student_attendance_stats(
            student.id, start_date, end_date
        )
        
        return StudentAttendanceStatsOut(
            student_id=student.id,
            student_name=f"{student.first_name} {student.last_name}",
            register_number=student.register_number,
            start_date=stats['start_date'],
            end_date=stats['end_date'],
            total_working_days=stats['total_working_days'],
            holidays_count=stats.get('holidays_count', 0),
            present_days=stats['present_days'],
            absent_days=stats['absent_days'],
            attendance_percentage=stats['attendance_percentage'],
            recent_records=[
                AttendanceRecordOut.model_validate(r) if not isinstance(r, dict)
                else AttendanceRecordOut(**r)
                for r in stats['records']
            ],
            holidays=[HolidayOut.model_validate(h) for h in stats.get('holidays', [])]
        )
    
    # ============== Holiday Calendar Methods ==============
    
    async def create_holiday(
        self,
        admin_id: int,
        holiday_data: dict
    ):
        """Create a new holiday/non-working day."""
        from app.repositories.attendance_repository import HolidayRepository
        from app.schemas.attendance import HolidayOut
        
        holiday_repo = HolidayRepository(self.db)
        
        # Check if holiday already exists for this date
        existing = await holiday_repo.get_by_date(holiday_data['date'])
        if existing:
            raise ValueError(f"Holiday already exists for {holiday_data['date']}")
        
        holiday = await holiday_repo.create(holiday_data, admin_id)
        return HolidayOut.model_validate(holiday)
    
    async def get_holidays(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ):
        """Get holidays within a date range."""
        from datetime import timedelta
        from app.repositories.attendance_repository import HolidayRepository
        from app.schemas.attendance import HolidayOut, HolidayListOut
        
        holiday_repo = HolidayRepository(self.db)
        
        if start_date and end_date:
            holidays = await holiday_repo.get_holidays_in_range(start_date, end_date)
        else:
            holidays = await holiday_repo.get_all_active()
        
        return HolidayListOut(
            holidays=[HolidayOut.model_validate(h) for h in holidays],
            total=len(holidays)
        )
    
    async def delete_holiday(self, holiday_id: int) -> bool:
        """Delete a holiday."""
        from app.repositories.attendance_repository import HolidayRepository
        
        holiday_repo = HolidayRepository(self.db)
        return await holiday_repo.delete(holiday_id)
    
    async def bulk_create_holidays(
        self,
        admin_id: int,
        text: str,
        year: int
    ) -> dict:
        """
        Parse pasted text and create multiple holidays.
        Expected format: Date\tDay\tHoliday Name (tab or comma separated)
        Example: Jan 1\tMonday\tNew Year
        """
        import re
        from datetime import datetime
        from app.repositories.attendance_repository import HolidayRepository
        
        holiday_repo = HolidayRepository(self.db)
        
        # Month name to number mapping
        month_map = {
            'jan': 1, 'january': 1,
            'feb': 2, 'february': 2,
            'mar': 3, 'march': 3,
            'apr': 4, 'april': 4,
            'may': 5,
            'jun': 6, 'june': 6,
            'jul': 7, 'july': 7,
            'aug': 8, 'august': 8,
            'sep': 9, 'sept': 9, 'september': 9,
            'oct': 10, 'october': 10,
            'nov': 11, 'november': 11,
            'dec': 12, 'december': 12,
        }
        
        lines = text.strip().split('\n')
        created = []
        errors = []
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            # Skip header line
            if 'date' in line.lower() and 'holiday' in line.lower():
                continue
            
            # Split by tab or multiple spaces or comma
            parts = re.split(r'\t+|,|  +', line)
            parts = [p.strip() for p in parts if p.strip()]
            
            if len(parts) < 2:
                errors.append(f"Line {line_num}: Invalid format - '{line}'")
                continue
            
            # Parse date (first part) - expected format: "Jan 1" or "January 1"
            date_str = parts[0]
            holiday_name = parts[-1]  # Last part is name (skip day of week if present)
            
            # Parse month and day
            date_match = re.match(r'([a-zA-Z]+)\s*(\d+)', date_str)
            if not date_match:
                errors.append(f"Line {line_num}: Could not parse date - '{date_str}'")
                continue
            
            month_str = date_match.group(1).lower()
            day = int(date_match.group(2))
            
            if month_str not in month_map:
                errors.append(f"Line {line_num}: Unknown month - '{month_str}'")
                continue
            
            month = month_map[month_str]
            
            try:
                holiday_date = date(year, month, day)
            except ValueError as e:
                errors.append(f"Line {line_num}: Invalid date - {e}")
                continue
            
            # Check if already exists
            existing = await holiday_repo.get_by_date(holiday_date)
            if existing:
                errors.append(f"Line {line_num}: Holiday already exists for {holiday_date}")
                continue
            
            # Create holiday
            try:
                holiday = await holiday_repo.create({
                    'date': holiday_date,
                    'name': holiday_name,
                    'holiday_type': 'GENERAL',
                    'is_recurring': True,
                }, admin_id)
                created.append({
                    'date': str(holiday_date),
                    'name': holiday_name
                })
            except Exception as e:
                errors.append(f"Line {line_num}: Failed to create - {e}")
        
        return {
            'created': created,
            'created_count': len(created),
            'errors': errors,
            'error_count': len(errors)
        }
    
    # ============== Academic Year Settings Methods ==============
    
    async def get_academic_year_settings(self):
        """Get the configured academic year start and end dates."""
        from app.repositories.attendance_repository import SettingsRepository
        from app.schemas.attendance import AcademicYearSettingsOut
        
        settings_repo = SettingsRepository(self.db)
        start_date, end_date = await settings_repo.get_academic_year_dates()
        
        return AcademicYearSettingsOut(
            start_date=start_date,
            end_date=end_date
        )
    
    async def update_academic_year_settings(
        self,
        admin_id: int,
        start_date: date,
        end_date: date
    ):
        """Update the academic year start and end dates."""
        from app.repositories.attendance_repository import SettingsRepository
        from app.schemas.attendance import AcademicYearSettingsOut
        
        if start_date >= end_date:
            raise ValueError("Start date must be before end date")
        
        settings_repo = SettingsRepository(self.db)
        await settings_repo.set_academic_year_dates(start_date, end_date, admin_id)
        
        return AcademicYearSettingsOut(
            start_date=start_date,
            end_date=end_date
        )
