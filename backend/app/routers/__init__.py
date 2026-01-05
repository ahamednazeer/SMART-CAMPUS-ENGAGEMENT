# Routers
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.pdfs import router as pdfs_router
from app.routers.reading import router as reading_router
from app.routers.streaks import router as streaks_router
from app.routers.quizzes import router as quizzes_router
from app.routers.admin import router as admin_router
from app.routers.attendance import router as attendance_router
from app.routers.admin_attendance import router as admin_attendance_router
from app.routers.hostel import router as hostel_router
from app.routers.outpass import router as outpass_router
from app.routers.warden import router as warden_router
from app.routers.ai_assistant import router as ai_assistant_router
from app.routers.faculty_location import router as faculty_location_router

# Hybrid Learning Module Routers
from app.routers.courses import router as courses_router
from app.routers.study_circles import router as study_circles_router
from app.routers.flashcards import router as flashcards_router
from app.routers.doubt_sessions import router as doubt_sessions_router
from app.routers.whiteboard import router as whiteboard_router
from app.routers.course_reviews import router as course_reviews_router
from app.routers.knowledge_graph import router as knowledge_graph_router

__all__ = [
    "auth_router",
    "users_router",
    "pdfs_router",
    "reading_router",
    "streaks_router",
    "quizzes_router",
    "admin_router",
    "attendance_router",
    "admin_attendance_router",
    "hostel_router",
    "outpass_router",
    "warden_router",
    "ai_assistant_router",
    "faculty_location_router",
    # Hybrid Learning Module
    "courses_router",
    "study_circles_router",
    "flashcards_router",
    "doubt_sessions_router",
    "whiteboard_router",
    "course_reviews_router",
    "knowledge_graph_router",
]
