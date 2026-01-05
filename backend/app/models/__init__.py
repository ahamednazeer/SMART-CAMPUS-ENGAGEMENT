# Models
from app.models.user import User, UserRole, StudentCategory
from app.models.audit_log import AuditLog
from app.models.notification import Notification, NotificationType
from app.models.pdf import PDF, PDFAssignment
from app.models.reading import ReadingSession, DailyReadingLog
from app.models.streak import Streak, StreakRecoveryRequest, RecoveryStatus
from app.models.quiz import Quiz, QuizQuestion, QuizAttempt
from app.models.attendance import (
    ProfilePhoto, ProfilePhotoStatus,
    CampusGeofence, AttendanceWindow,
    AttendanceRecord, AttendanceStatus,
    AttendanceAttempt, FailureReason
)
from app.models.hostel import Hostel, HostelRoom, HostelAssignment
from app.models.outpass import OutpassRequest, OutpassStatus, OutpassLog
from app.models.maintenance import HostelMaintenance, MaintenanceCategory, MaintenanceStatus
from app.models.bonafide import BonafideCertificate, CertificateType, CertificatePurpose, CertificateStatus
from app.models.query import Query, QueryCategory, QueryStatus
from app.models.complaint import Complaint, ComplaintCategory, ComplaintStatus, ComplaintPriority
from app.models.faculty_location import (
    CampusBuilding, FacultyAvailability, 
    AvailabilityStatus, VisibilityLevel
)

# Hybrid Learning Module - New Models
from app.models.course import Course, CourseEnrollment, CourseSemester
from app.models.study_circle import (
    StudyCircle, CircleChannel, CircleMember, CircleMessage,
    ChannelType, MemberRole
)
from app.models.doubt_session import (
    DoubtSession, SessionParticipant, SessionQuestion, SessionSummary,
    SessionStatus, QuestionStatus
)
from app.models.whiteboard import (
    WhiteboardSession, WhiteboardParticipant, WhiteboardSnapshot,
    WhiteboardStatus, WhiteboardPermission
)
from app.models.flashcard import (
    FlashcardSet, Flashcard, FlashcardBattle, BattleParticipant, FlashcardLeaderboard,
    BattleType, BattleStatus
)
from app.models.course_review import (
    CourseReview, CourseReviewAggregate, ReviewWindow,
    ReviewStatus
)
from app.models.knowledge_graph import (
    KnowledgeTopic, TopicDependency, StudentTopicProgress,
    LearningPath, LearningPathTopic,
    DependencyStrength, ProgressStatus
)

__all__ = [
    # User
    "User",
    "UserRole",
    "StudentCategory",
    # Audit
    "AuditLog",
    # Notification
    "Notification",
    "NotificationType",
    # PDF
    "PDF",
    "PDFAssignment",
    # Reading
    "ReadingSession",
    "DailyReadingLog",
    # Streak
    "Streak",
    "StreakRecoveryRequest",
    "RecoveryStatus",
    # Quiz
    "Quiz",
    "QuizQuestion",
    "QuizAttempt",
    # Attendance
    "ProfilePhoto",
    "ProfilePhotoStatus",
    "CampusGeofence",
    "AttendanceWindow",
    "AttendanceRecord",
    "AttendanceStatus",
    "AttendanceAttempt",
    "FailureReason",
    # Hostel
    "Hostel",
    "HostelRoom",
    "HostelAssignment",
    # Outpass
    "OutpassRequest",
    "OutpassStatus",
    "OutpassLog",
    # Maintenance
    "HostelMaintenance",
    "MaintenanceCategory",
    "MaintenanceStatus",
    # Bonafide Certificate
    "BonafideCertificate",
    "CertificateType",
    "CertificatePurpose",
    "CertificateStatus",
    # Query
    "Query",
    "QueryCategory",
    "QueryStatus",
    # Complaint
    "Complaint",
    "ComplaintCategory",
    "ComplaintStatus",
    "ComplaintPriority",
    # Faculty Location
    "CampusBuilding",
    "FacultyAvailability",
    "AvailabilityStatus",
    "VisibilityLevel",
    # Course
    "Course",
    "CourseEnrollment",
    "CourseSemester",
    # Study Circle
    "StudyCircle",
    "CircleChannel",
    "CircleMember",
    "CircleMessage",
    "ChannelType",
    "MemberRole",
    # Doubt Session
    "DoubtSession",
    "SessionParticipant",
    "SessionQuestion",
    "SessionSummary",
    "SessionStatus",
    "QuestionStatus",
    # Whiteboard
    "WhiteboardSession",
    "WhiteboardParticipant",
    "WhiteboardSnapshot",
    "WhiteboardStatus",
    "WhiteboardPermission",
    # Flashcard
    "FlashcardSet",
    "Flashcard",
    "FlashcardBattle",
    "BattleParticipant",
    "FlashcardLeaderboard",
    "BattleType",
    "BattleStatus",
    # Course Review
    "CourseReview",
    "CourseReviewAggregate",
    "ReviewWindow",
    "ReviewStatus",
    # Knowledge Graph
    "KnowledgeTopic",
    "TopicDependency",
    "StudentTopicProgress",
    "LearningPath",
    "LearningPathTopic",
    "DependencyStrength",
    "ProgressStatus",
]
