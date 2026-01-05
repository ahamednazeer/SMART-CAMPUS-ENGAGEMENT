"""
Course service for managing courses and enrollments.
"""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course, CourseEnrollment


class CourseService:
    """Service for course management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ============== Course CRUD ==============
    
    async def create_course(
        self,
        code: str,
        name: str,
        description: str | None = None,
        department: str | None = None,
        semester: int | None = None,
        credits: int = 3,
        faculty_id: int | None = None
    ) -> Course:
        """Create a new course."""
        course = Course(
            code=code,
            name=name,
            description=description,
            department=department,
            semester=semester,
            credits=credits,
            faculty_id=faculty_id
        )
        self.db.add(course)
        await self.db.flush()
        await self.db.refresh(course)
        return course
    
    async def get_course(self, course_id: int) -> Course | None:
        """Get a course by ID."""
        result = await self.db.execute(
            select(Course).where(Course.id == course_id)
        )
        return result.scalar_one_or_none()
    
    async def get_course_by_code(self, code: str) -> Course | None:
        """Get a course by code."""
        result = await self.db.execute(
            select(Course).where(Course.code == code)
        )
        return result.scalar_one_or_none()
    
    async def get_courses(
        self,
        department: str | None = None,
        semester: int | None = None,
        faculty_id: int | None = None,
        active_only: bool = True
    ) -> list[Course]:
        """Get courses with optional filters."""
        query = select(Course)
        
        if active_only:
            query = query.where(Course.is_active == True)
        if department:
            query = query.where(Course.department == department)
        if semester:
            query = query.where(Course.semester == semester)
        if faculty_id:
            query = query.where(Course.faculty_id == faculty_id)
        
        query = query.order_by(Course.code)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def update_course(
        self,
        course_id: int,
        **kwargs
    ) -> Course | None:
        """Update a course."""
        course = await self.get_course(course_id)
        if not course:
            return None
        
        for key, value in kwargs.items():
            if hasattr(course, key):
                setattr(course, key, value)
        
        await self.db.flush()
        await self.db.refresh(course)
        return course
    
    async def delete_course(self, course_id: int) -> bool:
        """Soft delete a course."""
        course = await self.get_course(course_id)
        if not course:
            return False
        
        course.is_active = False
        await self.db.flush()
        return True
    
    # ============== Enrollment Management ==============
    
    async def enroll_student(
        self,
        student_id: int,
        course_id: int,
        academic_year: str | None = None
    ) -> CourseEnrollment:
        """Enroll a student in a course."""
        enrollment = CourseEnrollment(
            student_id=student_id,
            course_id=course_id,
            academic_year=academic_year
        )
        self.db.add(enrollment)
        await self.db.flush()
        await self.db.refresh(enrollment)
        return enrollment
    
    async def bulk_enroll_students(
        self,
        student_ids: list[int],
        course_id: int,
        academic_year: str | None = None
    ) -> list[CourseEnrollment]:
        """Enroll multiple students in a course."""
        enrollments = []
        for student_id in student_ids:
            # Check if already enrolled
            existing = await self.get_enrollment(student_id, course_id)
            if not existing:
                enrollment = CourseEnrollment(
                    student_id=student_id,
                    course_id=course_id,
                    academic_year=academic_year
                )
                self.db.add(enrollment)
                enrollments.append(enrollment)
        
        await self.db.flush()
        return enrollments
    
    async def get_enrollment(
        self,
        student_id: int,
        course_id: int
    ) -> CourseEnrollment | None:
        """Get a specific enrollment."""
        result = await self.db.execute(
            select(CourseEnrollment).where(
                CourseEnrollment.student_id == student_id,
                CourseEnrollment.course_id == course_id,
                CourseEnrollment.is_active == True
            )
        )
        return result.scalar_one_or_none()
    
    async def get_student_courses(self, student_id: int) -> list[Course]:
        """Get all courses a student is enrolled in."""
        result = await self.db.execute(
            select(Course)
            .join(CourseEnrollment, CourseEnrollment.course_id == Course.id)
            .where(
                CourseEnrollment.student_id == student_id,
                CourseEnrollment.is_active == True,
                Course.is_active == True
            )
            .order_by(Course.semester, Course.code)
        )
        return list(result.scalars().all())
    
    async def get_course_students(self, course_id: int) -> list[int]:
        """Get all student IDs enrolled in a course."""
        result = await self.db.execute(
            select(CourseEnrollment.student_id).where(
                CourseEnrollment.course_id == course_id,
                CourseEnrollment.is_active == True
            )
        )
        return list(result.scalars().all())
    
    async def unenroll_student(
        self,
        student_id: int,
        course_id: int
    ) -> bool:
        """Unenroll a student from a course."""
        enrollment = await self.get_enrollment(student_id, course_id)
        if not enrollment:
            return False
        
        enrollment.is_active = False
        await self.db.flush()
        return True
    
    async def get_enrollment_count(self, course_id: int) -> int:
        """Get the number of enrolled students."""
        result = await self.db.execute(
            select(func.count(CourseEnrollment.id)).where(
                CourseEnrollment.course_id == course_id,
                CourseEnrollment.is_active == True
            )
        )
        return result.scalar() or 0
