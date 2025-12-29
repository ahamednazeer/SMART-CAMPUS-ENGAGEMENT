
import asyncio
import random
from datetime import datetime, timedelta, date, time
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.models.user import User, UserRole
from app.models.attendance import AttendanceRecord, AttendanceAttempt, AttendanceStatus, FailureReason
from app.models.attendance import CampusGeofence

async def seed_data():
    async with async_session_factory() as db:
        print("Seeding attendance data...")
        
        # Get all students
        result = await db.execute(select(User).where(User.role == UserRole.STUDENT))
        students = result.scalars().all()
        
        if not students:
            print("No students found. Please create some students first.")
            return

        # Get primary geofence for reference
        result = await db.execute(select(CampusGeofence).where(CampusGeofence.is_primary == True))
        geofence = result.scalar_one_or_none()
        
        # Date range: Last 30 days
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        records_to_add = []
        attempts_to_add = []
        
        current_date = start_date
        while current_date <= end_date:
            # Skip Sundays
            if current_date.weekday() == 6:
                current_date += timedelta(days=1)
                continue
                
            print(f"Processing {current_date}...")
            
            for student in students:
                # 85% chance of being present
                status_roll = random.random()
                
                if status_roll < 0.85:
                    # PRESENT
                    # Random time between 8:30 AM and 9:30 AM
                    check_in_time = datetime.combine(current_date, time(8, 30)) + timedelta(minutes=random.randint(0, 60))
                    
                    record = AttendanceRecord(
                        student_id=student.id,
                        attendance_date=current_date,
                        status=AttendanceStatus.PRESENT,
                        location_latitude=12.9716 + (random.random() - 0.5) * 0.001, # Roughly near center
                        location_longitude=77.5946 + (random.random() - 0.5) * 0.001,
                        location_accuracy=random.uniform(5, 20),
                        face_match_confidence=random.uniform(75, 99),
                        marked_at=check_in_time
                    )
                    records_to_add.append(record)
                    
                    # Also add a successful attempt log
                    attempt = AttendanceAttempt(
                        student_id=student.id,
                        attempted_at=check_in_time,
                        success=True,
                        location_latitude=record.location_latitude,
                        location_longitude=record.location_longitude,
                        location_accuracy=record.location_accuracy,
                        face_match_score=record.face_match_confidence,
                        geofence_id=geofence.id if geofence else None
                    )
                    attempts_to_add.append(attempt)
                    
                elif status_roll < 0.95:
                    # ABSENT (No record, or marked explicit absent if needed, but usually just missing record implies absent until EOD job runs)
                    # Let's create an explicit ABSENT record for completed days
                    if current_date < date.today():
                         record = AttendanceRecord(
                            student_id=student.id,
                            attendance_date=current_date,
                            status=AttendanceStatus.ABSENT
                        )
                         records_to_add.append(record)
                
                else:
                    # FAILED ATTEMPT (Tried but failed)
                    fail_time = datetime.combine(current_date, time(9, 0)) + timedelta(minutes=random.randint(0, 30))
                    
                    reasons = [
                        (FailureReason.OUTSIDE_CAMPUS, "Distance from campus center: 600m"),
                        (FailureReason.LOW_GPS_ACCURACY, "GPS accuracy 65m exceeds threshold 50m"),
                        (FailureReason.Face_MISMATCH, "Face match score: 35.5"),
                        (FailureReason.NO_FACE_DETECTED, "No face detected in captured image")
                    ]
                    reason, detail = random.choice(reasons)
                    
                    attempt = AttendanceAttempt(
                        student_id=student.id,
                        attempted_at=fail_time,
                        success=False,
                        failure_reason=reason if reason != FailureReason.Face_MISMATCH else FailureReason.FACE_MISMATCH, # Typo fix in list above if needed
                        failure_details=detail,
                        location_latitude=12.9716 + (random.random() - 0.5) * 0.01,
                        location_longitude=77.5946 + (random.random() - 0.5) * 0.01,
                        location_accuracy=random.uniform(50, 100) if reason == FailureReason.LOW_GPS_ACCURACY else random.uniform(5, 20),
                        face_match_score=random.uniform(10, 40) if reason == FailureReason.FACE_MISMATCH else None,
                        geofence_id=geofence.id if geofence else None
                    )
                    attempts_to_add.append(attempt)
                    
                    # Assume they didn't try again and were marked Absent
                    if current_date < date.today():
                        record = AttendanceRecord(
                            student_id=student.id,
                            attendance_date=current_date,
                            status=AttendanceStatus.ABSENT
                        )
                        records_to_add.append(record)

            current_date += timedelta(days=1)
            
        print(f"Adding {len(records_to_add)} records and {len(attempts_to_add)} attempts...")
        db.add_all(records_to_add)
        db.add_all(attempts_to_add)
        await db.commit()
        print("Done!")

if __name__ == "__main__":
    asyncio.run(seed_data())
