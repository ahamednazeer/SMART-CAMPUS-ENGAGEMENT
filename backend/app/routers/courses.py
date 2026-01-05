"""
Course management API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.services.course_service import CourseService


router = APIRouter(prefix="/courses", tags=["Courses"])


# ============== Schemas ==============

class CourseCreate(BaseModel):
    code: str
    name: str
    description: str | None = None
    department: str | None = None
    semester: int | None = None
    credits: int = 3
    faculty_id: int | None = None


class CourseUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    department: str | None = None
    semester: int | None = None
    credits: int | None = None
    faculty_id: int | None = None
    is_active: bool | None = None


class EnrollmentCreate(BaseModel):
    student_ids: list[int]
    academic_year: str | None = None


class CourseResponse(BaseModel):
    id: int
    code: str
    name: str
    description: str | None
    department: str | None
    semester: int | None
    credits: int
    faculty_id: int | None
    is_active: bool
    
    class Config:
        from_attributes = True


# ============== Admin Endpoints ==============

@router.post("", response_model=CourseResponse)
async def create_course(
    data: CourseCreate,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
    db: AsyncSession = Depends(get_db)
):
    """Create a new course (Admin/Staff only)."""
    service = CourseService(db)
    
    # Check if code already exists
    existing = await service.get_course_by_code(data.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course code already exists"
        )
    
    course = await service.create_course(**data.model_dump())
    return course


@router.get("", response_model=list[CourseResponse])
async def get_courses(
    department: str | None = None,
    semester: int | None = None,
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all courses with optional filters."""
    service = CourseService(db)
    courses = await service.get_courses(
        department=department,
        semester=semester,
        active_only=active_only
    )
    return courses


@router.get("/enrollable/students")
async def get_enrollable_students(
    department: str | None = None,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
    db: AsyncSession = Depends(get_db)
):
    """Get all students available for enrollment (Admin/Staff only)."""
    from sqlalchemy import select
    from app.models.user import User as UserModel
    
    query = select(UserModel).where(
        UserModel.role == UserRole.STUDENT,
        UserModel.is_active == True
    )
    
    if department:
        query = query.where(UserModel.department == department)
    
    query = query.order_by(UserModel.first_name, UserModel.last_name)
    
    result = await db.execute(query)
    students = result.scalars().all()
    
    return [
        {
            "id": s.id,
            "first_name": s.first_name,
            "last_name": s.last_name,
            "register_number": s.register_number,
            "department": s.department,
            "batch": s.batch,
        }
        for s in students
    ]


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a course by ID."""
    service = CourseService(db)
    course = await service.get_course(course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    return course


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    data: CourseUpdate,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
    db: AsyncSession = Depends(get_db)
):
    """Update a course (Admin/Staff only)."""
    service = CourseService(db)
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    course = await service.update_course(course_id, **update_data)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    return course


@router.delete("/{course_id}")
async def delete_course(
    course_id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a course (Admin only)."""
    service = CourseService(db)
    success = await service.delete_course(course_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    return {"message": "Course deleted successfully"}


# ============== Enrollment Endpoints ==============

@router.post("/{course_id}/enroll")
async def enroll_students(
    course_id: int,
    data: EnrollmentCreate,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
    db: AsyncSession = Depends(get_db)
):
    """Enroll students in a course (Admin/Staff only)."""
    service = CourseService(db)
    
    course = await service.get_course(course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    enrollments = await service.bulk_enroll_students(
        data.student_ids,
        course_id,
        data.academic_year
    )
    
    return {"message": f"Enrolled {len(enrollments)} students", "enrolled_count": len(enrollments)}


@router.get("/{course_id}/students")
async def get_course_students(
    course_id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
    db: AsyncSession = Depends(get_db)
):
    """Get all students enrolled in a course."""
    service = CourseService(db)
    student_ids = await service.get_course_students(course_id)
    return {"student_ids": student_ids, "count": len(student_ids)}


@router.delete("/{course_id}/students/{student_id}")
async def unenroll_student(
    course_id: int,
    student_id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
    db: AsyncSession = Depends(get_db)
):
    """Unenroll a student from a course."""
    service = CourseService(db)
    success = await service.unenroll_student(student_id, course_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found"
        )
    return {"message": "Student unenrolled successfully"}





# ============== Student Endpoints ==============

@router.get("/my/enrolled", response_model=list[CourseResponse])
async def get_my_courses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get courses the current student is enrolled in."""
    service = CourseService(db)
    courses = await service.get_student_courses(current_user.id)
    return courses

