# Schemas
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.schemas.user import UserCreate, UserUpdate, UserOut, UserListOut, BulkImportRequest, BulkImportResponse, PasswordChange
from app.schemas.pdf import PDFCreate, PDFUpdate, PDFOut, PDFListOut, AssignmentCreate, AssignmentOut, StudentPDFOut
from app.schemas.reading import SessionStart, SessionEvent, SessionEnd, SessionOut, DailyLogOut, ReadingProgressOut, ReadingHistoryOut
from app.schemas.streak import StreakOut, StreakDashboard, RecoveryRequestCreate, RecoveryRequestOut, RecoveryReview, StreakAnalytics
from app.schemas.quiz import QuestionCreate, QuestionOut, QuestionFullOut, QuizCreate, QuizUpdate, QuizOut, QuizFullOut, QuizStudentOut, AttemptSubmit, AttemptOut, AttemptResultOut
from app.schemas.attendance import (
    ProfilePhotoUpload, ProfilePhotoOut, ProfilePhotoApproval, ProfilePhotoListOut,
    GeofenceCreate, GeofenceUpdate, GeofenceOut, GeofenceListOut,
    AttendanceWindowCreate, AttendanceWindowUpdate, AttendanceWindowOut, AttendanceWindowListOut,
    LocationData, AttendanceMarkRequest, AttendancePreCheckOut, AttendanceMarkResult,
    AttendanceRecordOut, AttendanceRecordListOut,
    AttendanceAttemptOut, AttendanceAttemptListOut,
    AttendanceDashboardStats, StudentAttendanceSummary
)
from app.schemas.faculty_location import (
    CampusBuildingCreate, CampusBuildingUpdate, CampusBuildingOut,
    FacultyAvailabilityUpdate, FacultyLocationRefresh, FacultySettingsOut,
    FacultyLocationOut, FacultyLocationListOut,
    AdminFacultyLocationOut, AdminFacultyListOut, FacultyLocationStats
)

__all__ = [
    # Auth
    "LoginRequest", "TokenResponse", "UserResponse",
    # User
    "UserCreate", "UserUpdate", "UserOut", "UserListOut", "BulkImportRequest", "BulkImportResponse", "PasswordChange",
    # PDF
    "PDFCreate", "PDFUpdate", "PDFOut", "PDFListOut", "AssignmentCreate", "AssignmentOut", "StudentPDFOut",
    # Reading
    "SessionStart", "SessionEvent", "SessionEnd", "SessionOut", "DailyLogOut", "ReadingProgressOut", "ReadingHistoryOut",
    # Streak
    "StreakOut", "StreakDashboard", "RecoveryRequestCreate", "RecoveryRequestOut", "RecoveryReview", "StreakAnalytics",
    # Quiz
    "QuestionCreate", "QuestionOut", "QuestionFullOut", "QuizCreate", "QuizUpdate", "QuizOut", "QuizFullOut", "QuizStudentOut", "AttemptSubmit", "AttemptOut", "AttemptResultOut",
    # Attendance
    "ProfilePhotoUpload", "ProfilePhotoOut", "ProfilePhotoApproval", "ProfilePhotoListOut",
    "GeofenceCreate", "GeofenceUpdate", "GeofenceOut", "GeofenceListOut",
    "AttendanceWindowCreate", "AttendanceWindowUpdate", "AttendanceWindowOut", "AttendanceWindowListOut",
    "LocationData", "AttendanceMarkRequest", "AttendancePreCheckOut", "AttendanceMarkResult",
    "AttendanceRecordOut", "AttendanceRecordListOut",
    "AttendanceAttemptOut", "AttendanceAttemptListOut",
    "AttendanceDashboardStats", "StudentAttendanceSummary",
    # Faculty Location
    "CampusBuildingCreate", "CampusBuildingUpdate", "CampusBuildingOut",
    "FacultyAvailabilityUpdate", "FacultyLocationRefresh", "FacultySettingsOut",
    "FacultyLocationOut", "FacultyLocationListOut",
    "AdminFacultyLocationOut", "AdminFacultyListOut", "FacultyLocationStats",
]

