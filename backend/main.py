from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.core.security import hash_password
from app.routers import (
    auth_router,
    users_router,
    pdfs_router,
    reading_router,
    # streaks_router,  # COMMENTED OUT - Reading Streak feature disabled
    quizzes_router,
    admin_router,
    attendance_router,
    admin_attendance_router,
    hostel_router,
    outpass_router,
    warden_router,
    ai_assistant_router,
    faculty_location_router,
)
from app.routers.bonafide import router as bonafide_router
from app.routers.queries import router as queries_router
from app.routers.complaints import router as complaints_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    await init_db()
    await create_default_admin()
    
    # COMMENTED OUT - Reading Streak feature disabled
    # # Initialize Scheduler
    # from apscheduler.schedulers.asyncio import AsyncIOScheduler
    # from apscheduler.triggers.cron import CronTrigger
    # from app.services.streak_service import StreakService
    # from app.core.database import async_session_maker
    # 
    # scheduler = AsyncIOScheduler()
    # 
    # async def nightly_streak_evaluation():
    #     """Run nightly evaluation for all active streaks/logs."""
    #     print("Starting nightly streak evaluation...")
    #     async with async_session_maker() as session:
    #         try:
    #             from sqlalchemy import select, and_
    #             from app.models.reading import DailyReadingLog
    #             from datetime import date
    #             
    #             result = await session.execute(
    #                 select(DailyReadingLog).where(
    #                     DailyReadingLog.is_locked == False,
    #                     DailyReadingLog.log_date < date.today()
    #                 )
    #             )
    #             logs = result.scalars().all()
    #             for log in logs:
    #                 await StreakService(session).evaluate_student_pending_logs(log.student_id)
    #                 
    #             await session.commit()
    #             print("Nightly evaluation completed.")
    #         except Exception as e:
    #             print(f"Nightly evaluation failed: {e}")
    # 
    # scheduler.add_job(nightly_streak_evaluation, CronTrigger(hour=23, minute=59))
    # scheduler.start()
    
    yield
    # Shutdown
    # scheduler.shutdown()  # COMMENTED OUT - Reading Streak feature disabled


app = FastAPI(
    title=settings.APP_NAME,
    description="Smart Campus Engagement System API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(pdfs_router)
app.include_router(reading_router)
# app.include_router(streaks_router)  # COMMENTED OUT - Reading Streak feature disabled
app.include_router(quizzes_router)
app.include_router(admin_router)
app.include_router(attendance_router)
app.include_router(admin_attendance_router)
app.include_router(hostel_router)
app.include_router(outpass_router)
app.include_router(warden_router)
app.include_router(bonafide_router)
app.include_router(queries_router)
app.include_router(complaints_router)
app.include_router(ai_assistant_router)
app.include_router(faculty_location_router)

# Mount static files (uploads)
from fastapi.staticfiles import StaticFiles
import os

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=settings.UPLOAD_DIR), name="static")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Smart Campus Engagement System API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


async def create_default_admin():
    """Create default admin user if not exists."""
    from app.core.database import async_session_maker
    from app.models.user import User, UserRole
    from sqlalchemy import select
    
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.username == "admin")
        )
        admin = result.scalar_one_or_none()
        
        if admin is None:
            admin = User(
                username="admin",
                email="admin@campus.edu",
                password_hash=hash_password("admin123"),
                first_name="System",
                last_name="Admin",
                role=UserRole.ADMIN,
                is_active=True,
            )
            session.add(admin)
            await session.commit()
            print("Default admin user created: admin / admin123")
