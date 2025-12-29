"""
AI Assistant Service - Smart Campus AI Companion.

Design Philosophy:
- Read-Only Intelligence: Can read allowed data, never write or modify
- Context-Restricted Access: Sees only what current user is allowed to see
- Academic Integrity First: Disabled during quizzes/evaluations
- Robust & Resilient: Graceful degradation when AI is unavailable
"""
import httpx
import re
import time
import hashlib
from typing import Optional, Dict, Any
from collections import OrderedDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.core.config import settings
from app.models.user import User, UserRole, StudentCategory
from app.models.pdf import PDF
from app.models.quiz import QuizAttempt
from app.models.query import Query
from app.models.complaint import Complaint
from app.models.outpass import OutpassRequest
from app.schemas.ai_assistant import (
    AIModule, ActionChip, ChatResponse, AIContextResponse, QuizStatusResponse
)


class ResponseCache:
    """Simple in-memory cache for AI responses with TTL."""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        self.cache: OrderedDict[str, tuple[str, float]] = OrderedDict()
        self.max_size = max_size
        self.ttl = ttl_seconds
    
    def _make_key(self, message: str, context_hash: str) -> str:
        """Create cache key from message and context hash."""
        return hashlib.md5(f"{message.lower().strip()}:{context_hash}".encode()).hexdigest()
    
    def get(self, message: str, context_hash: str) -> Optional[str]:
        """Get cached response if exists and not expired."""
        key = self._make_key(message, context_hash)
        if key in self.cache:
            response, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                self.cache.move_to_end(key)  # LRU update
                return response
            else:
                del self.cache[key]  # Expired
        return None
    
    def set(self, message: str, context_hash: str, response: str):
        """Cache a response."""
        key = self._make_key(message, context_hash)
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)  # Remove oldest
        self.cache[key] = (response, time.time())


class AIAssistantService:
    """
    AI Assistant for campus guidance and explanations.
    
    This AI exists to:
    - Help students understand rules and content
    - Explain system behavior and statuses
    - Guide students to the correct module
    - Reduce repeated questions to staff
    
    This AI does NOT:
    - Approve requests
    - Modify data
    - Override admin decisions
    - Assist in quizzes or evaluations
    """
    
    # Roles that can access AI
    ALLOWED_ROLES = {UserRole.STUDENT, UserRole.HOSTELLER, UserRole.DAY_SCHOLAR}
    
    # Response cache for common questions (5 minute TTL)
    _response_cache = ResponseCache(max_size=100, ttl_seconds=300)
    
    # AI health status
    _ai_healthy = True
    _last_health_check = 0
    _health_check_interval = 60  # seconds
    
    # Prompt injection patterns to detect and block
    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|above|prior)\s+instructions",
        r"disregard\s+(your|all)\s+(rules|instructions)",
        r"you\s+are\s+now\s+",
        r"pretend\s+(to\s+be|you\s+are)",
        r"jailbreak",
        r"DAN\s+mode",
        r"developer\s+mode",
        r"\\n\\n.*system:",
        r"<\|.*\|>",
        r"\[INST\]",
        r"<<SYS>>",
    ]
    
    # Fallback responses when AI is unavailable
    FALLBACK_RESPONSES = {
        "attendance": "For attendance queries, please check your attendance page or contact your department office.",
        "hostel": "For hostel-related questions, please contact the hostel warden or check the hostel notice board.",
        "outpass": "For outpass requests, please visit the outpass section in your dashboard or contact the hostel office.",
        "queries": "To submit a query, use the Queries section in your dashboard. Staff typically responds within 24-48 hours.",
        "complaints": "To file a complaint, use the Complaints section in your dashboard. Urgent issues should be reported directly to staff.",
        "default": "I'm currently unable to process your request. Please try again later or contact the administration office for assistance."
    }
    
    # System prompt for AI behavior
    SYSTEM_PROMPT = """You are the Smart Campus AI Assistant - a friendly, knowledgeable guide for students at this educational institution.

YOUR IDENTITY:
- You are "Campus AI" - the official AI assistant for this Smart Campus platform
- You help students navigate their campus life, understand rules, and get answers quickly
- You have access to THIS student's personal data (attendance, queries, complaints, etc.)
- You're available 24/7 to answer questions when staff might not be

WHAT YOU CAN HELP WITH:
1. ATTENDANCE - Explain today's status, yearly stats, why attendance might fail (location/photo issues)
2. HOSTEL & OUTPASS - Rules, timings, how to apply for outpass, status meanings
3. FACULTY LOCATOR - Help find faculty members, their departments, and availability
4. QUERIES & COMPLAINTS - How to submit, who responds, expected timelines
5. QUIZZES - Explain how to take quizzes, check results, and general rules
6. CERTIFICATES - Bonafide, character certificates, how to request
7. NAVIGATION - Guide students to the right section of the dashboard
8. RULES & POLICIES - Explain campus rules, attendance requirements, hostel policies

HOW TO RESPOND:
1. **BE ULTRA-STRUCTURED**: Never use long paragraphs. Every point must be on a new line.
2. **MANDATORY LAYOUT**:
   - ### [Short Heading]
   - **Main Answer/Status** (e.g., "Your outpass is **Approved**")
   - **Key Details** (Use 2-3 bullet points)
   - **Next Steps** (Use a numbered list if sequential)
3. **FORMATTING**:
   - Use `###` for headings.
   - Use `**bold**` for key statuses, dates, or numbers.
   - Use separate lines with `-` or `1.` for lists.
4. **NO FILLER**: Start immediately with the structured answer. Avoid "As your assistant..." or "I'd like to explain...".

STRICT RULES:
1. **NO PARAGRAPHS**: A paragraph must never exceed 2 sentences. Use line breaks liberally.
2. **DATA ONLY**: Only use provided context. Do not invent details.
3. **READ-ONLY**: Cannot perform actions.
4. **NO CHEATING**: Refuse quiz help.

EXAMPLE STRUCTURE:
### Attendance Update
**Current Status**: 82% (Above required 75%)
- Present: 45 days
- Absent: 10 days
**Next Step**: Maintain this regularity to avoid penalties. 

WHEN ASKED "What can you help with?":
"### I can help with:
- 📊 **Attendance**: Status, stats, rules
- 🏠 **Hostel**: Room info, outpass requests
- 📍 **Faculty**: Finding faculty locations
- ❓ **Queries**: Submitting questions/complaints
- 📝 **Quizzes**: General info and history
- 📋 **Certificates**: Requesting documents
What can I assist you with today?" """

    @classmethod
    def _get_api_config(cls) -> tuple[str, dict, str]:
        """Get API URL, headers, and model for AI requests."""
        if settings.OLLAMA_ENABLED:
            return (
                f"{settings.OLLAMA_BASE_URL}/v1/chat/completions",
                {"Content-Type": "application/json"},
                settings.OLLAMA_MODEL
            )
        else:
            if not settings.GROQ_API_KEY:
                raise ValueError("No AI backend configured")
            return (
                "https://api.groq.com/openai/v1/chat/completions",
                {
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                settings.GROQ_MODEL
            )
    
    @classmethod
    def _detect_prompt_injection(cls, message: str) -> bool:
        """Detect potential prompt injection attempts."""
        message_lower = message.lower()
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, message_lower, re.IGNORECASE):
                print(f"Prompt injection detected: {pattern}")
                return True
        return False
    
    @classmethod
    async def _check_ai_health(cls) -> bool:
        """Check if AI service is healthy with periodic checks."""
        current_time = time.time()
        
        # Use cached health status if recent
        if current_time - cls._last_health_check < cls._health_check_interval:
            return cls._ai_healthy
        
        cls._last_health_check = current_time
        
        try:
            api_url, headers, model = cls._get_api_config()
            timeout = 10.0  # Quick health check timeout
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                # Light request to check connectivity
                response = await client.post(
                    api_url,
                    headers=headers,
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": "hi"}],
                        "max_tokens": 5
                    }
                )
                cls._ai_healthy = response.status_code == 200
        except Exception as e:
            print(f"AI health check failed: {e}")
            cls._ai_healthy = False
        
        return cls._ai_healthy
    
    @classmethod
    def _get_fallback_response(cls, module: AIModule) -> str:
        """Get a fallback response for the given module when AI is unavailable."""
        return cls.FALLBACK_RESPONSES.get(module.value, cls.FALLBACK_RESPONSES["default"])
    
    @classmethod
    def _get_context_hash(cls, context: str) -> str:
        """Create a hash of the context for cache key."""
        return hashlib.md5(context[:500].encode()).hexdigest()[:8]
    
    @classmethod
    async def check_access(cls, user: User, db: AsyncSession) -> tuple[bool, str | None]:
        """
        Check if user can access AI Assistant.
        Returns (can_access, reason_if_blocked)
        """
        # Check role
        if user.role not in cls.ALLOWED_ROLES:
            return False, "AI Assistant is only available for students"
        
        # Check for active quiz
        has_quiz, quiz_id = await cls.check_active_quiz(user.id, db)
        if has_quiz:
            return False, "AI Assistant is disabled during quizzes to maintain fairness"
        
        return True, None
    
    @classmethod
    async def check_active_quiz(cls, user_id: int, db: AsyncSession) -> tuple[bool, int | None]:
        """Check if user has an active (in-progress) quiz attempt."""
        stmt = select(QuizAttempt).where(
            and_(
                QuizAttempt.student_id == user_id,
                QuizAttempt.is_completed == False
            )
        )
        result = await db.execute(stmt)
        attempt = result.scalar_one_or_none()
        
        if attempt:
            return True, attempt.quiz_id
        return False, None
    
    @classmethod
    async def get_quiz_status(cls, user: User, db: AsyncSession) -> QuizStatusResponse:
        """Get quiz mode status for the user."""
        has_quiz, quiz_id = await cls.check_active_quiz(user.id, db)
        
        if has_quiz:
            return QuizStatusResponse(
                has_active_quiz=True,
                quiz_id=quiz_id,
                ai_blocked=True,
                message="AI Assistant is disabled during quizzes to maintain fairness."
            )
        
        return QuizStatusResponse(
            has_active_quiz=False,
            ai_blocked=False,
            message="AI Assistant is available"
        )
    
    @classmethod
    async def get_context(
        cls, 
        user: User, 
        module: AIModule, 
        db: AsyncSession,
        pdf_id: Optional[int] = None
    ) -> AIContextResponse:
        """Get AI context and availability for a module."""
        can_access, reason = await cls.check_access(user, db)
        
        if not can_access:
            return AIContextResponse(
                is_available=False,
                is_blocked=True,
                blocked_reason=reason,
                module=module
            )
        
        # Check module-specific availability
        if module == AIModule.QUIZ:
            return AIContextResponse(
                is_available=False,
                is_blocked=True,
                blocked_reason="AI Assistant is disabled during quizzes to maintain fairness.",
                module=module
            )
        
        # For reading module, check if PDF is assigned
        can_explain_pdf = False
        active_pdf = None
        
        if module == AIModule.READING and pdf_id:
            # Verify PDF is assigned to this student (not just that it exists)
            from app.models.pdf import PDFAssignment
            stmt = (
                select(PDF)
                .join(PDFAssignment, PDFAssignment.pdf_id == PDF.id)
                .where(PDF.id == pdf_id, PDFAssignment.student_id == user.id)
            )
            result = await db.execute(stmt)
            pdf = result.scalar_one_or_none()
            if pdf:
                can_explain_pdf = True
                active_pdf = pdf_id
        
        return AIContextResponse(
            is_available=True,
            is_blocked=False,
            module=module,
            can_explain_pdf=can_explain_pdf,
            active_pdf_id=active_pdf
        )
    
    @classmethod
    async def get_student_context(cls, user: User, db: AsyncSession) -> str:
        """Get context about the student for personalized responses."""
        context_parts = []
        
        # Basic info
        category = "hosteller" if user.student_category == StudentCategory.HOSTELLER else "day scholar"
        context_parts.append(f"Student is a {category}")
        
        if user.department:
            context_parts.append(f"from {user.department} department")
        
        if user.register_number:
            context_parts.append(f"Register No: {user.register_number}")
            
        if user.batch:
            context_parts.append(f"Batch: {user.batch}")
        
        # Get recent request statuses for context
        try:
            # Outpass Summary
            if user.student_category == StudentCategory.HOSTELLER:
                from app.models.outpass import OutpassRequest
                stmt = select(OutpassRequest).where(OutpassRequest.student_id == user.id).order_by(OutpassRequest.created_at.desc()).limit(1)
                result = await db.execute(stmt)
                outpass = result.scalar_one_or_none()
                if outpass:
                    start_date = outpass.start_datetime.strftime("%d %b")
                    context_parts.append(f"Latest Outpass: {outpass.status.value} for {outpass.destination} ({start_date})")
                
                # Hostel Assignment
                from app.models.hostel import HostelAssignment, Hostel, HostelRoom
                stmt = (
                    select(Hostel.name, HostelRoom.room_number)
                    .join(HostelAssignment, HostelAssignment.hostel_id == Hostel.id)
                    .join(HostelRoom, HostelAssignment.room_id == HostelRoom.id)
                    .where(HostelAssignment.student_id == user.id, HostelAssignment.is_active == True)
                )
                result = await db.execute(stmt)
                hostel_data = result.first()
                if hostel_data:
                    context_parts.append(f"Hostel: {hostel_data[0]}, Room: {hostel_data[1]}")

            # Primary Geofence
            from app.models.attendance import CampusGeofence
            stmt = select(CampusGeofence.name).where(CampusGeofence.is_primary == True, CampusGeofence.is_active == True)
            result = await db.execute(stmt)
            prim_gf = result.scalar_one_or_none()
            if prim_gf:
                context_parts.append(f"Campus Geofence: {prim_gf}")
            
            # Query & Complaint details and status
            from app.models.query import Query, QueryStatus
            from app.models.complaint import Complaint, ComplaintStatus
            
            stmt = select(Query.description, Query.status, Query.response).where(Query.student_id == user.id).order_by(Query.created_at.desc()).limit(1)
            result = await db.execute(stmt)
            query = result.first()
            if query:
                # Use value if it's an enum
                q_status = query[1].value if hasattr(query[1], 'value') else str(query[1])
                context_parts.append(f"Latest Query: '{query[0][:100]}' (Status: {q_status})")
                if query[2]:
                    context_parts.append(f"Admin Response to Query: {query[2]}")
                
            stmt = select(Complaint.description, Complaint.status, Complaint.resolution_notes).where(Complaint.student_id == user.id).order_by(Complaint.created_at.desc()).limit(1)
            result = await db.execute(stmt)
            complaint = result.first()
            if complaint:
                c_status = complaint[1].value if hasattr(complaint[1], 'value') else str(complaint[1])
                context_parts.append(f"Latest Complaint: '{complaint[0][:100]}' (Status: {c_status})")
                if complaint[2]:
                    context_parts.append(f"Complaint Resolution: {complaint[2]}")
            
            # Certificates
            from app.models.bonafide import BonafideCertificate
            stmt = select(BonafideCertificate.certificate_type, BonafideCertificate.status).where(BonafideCertificate.student_id == user.id).order_by(BonafideCertificate.created_at.desc()).limit(1)
            result = await db.execute(stmt)
            cert = result.first()
            if cert:
                context_parts.append(f"Certificate: {cert[0].value} is {cert[1].value}")

            # Attendance stats
            from app.repositories.attendance_repository import DetailedAttendanceRepository
            from datetime import date
            
            detailed_repo = DetailedAttendanceRepository(db)
            stats = await detailed_repo.get_student_attendance_stats(user.id)
            
            if stats:
                total_days = stats['total_working_days']
                present_days = stats['present_days']
                absent_days = stats['absent_days']
                percentage = stats['attendance_percentage']
                
                # Today's status check
                today = date.today()
                records = stats['records']
                today_status = "Not Recorded"
                from app.repositories.attendance_repository import HolidayRepository
                h_repo = HolidayRepository(db)
                is_holiday = await h_repo.get_by_date(today)
                if is_holiday: today_status = "Holiday"
                elif today.weekday() == 6: today_status = "Sunday"
                else:
                    for r in records:
                        r_date = r['attendance_date'] if isinstance(r, dict) else r.attendance_date
                        if r_date == today:
                            today_status = r['status'].value if isinstance(r, dict) else r.status.value
                            break
                
                context_parts.append(f"Attendance: Today is {today_status}. Year Stats: {present_days}/{total_days} days ({percentage}%).")
            
            # Streaks & Reading
            from app.models.streak import Streak
            from app.models.pdf import PDFAssignment, PDF
            stmt = select(func.sum(Streak.current_streak), func.max(Streak.max_streak)).where(Streak.student_id == user.id)
            result = await db.execute(stmt)
            streak_totals = result.first()
            if streak_totals and streak_totals[0] is not None:
                context_parts.append(f"Streaks: Total {streak_totals[0]}, Best {streak_totals[1]}")

            stmt = select(PDF.title).join(PDFAssignment).where(PDFAssignment.student_id == user.id)
            result = await db.execute(stmt)
            titles = result.scalars().all()
            if titles:
                context_parts.append(f"Assigned PDFs: {', '.join(titles[:3])}{'...' if len(titles) > 3 else ''}")

            # Quizzes
            from app.models.quiz import QuizAttempt
            stmt = select(func.count(QuizAttempt.id), func.avg(QuizAttempt.score), func.avg(QuizAttempt.total_questions)).where(QuizAttempt.student_id == user.id, QuizAttempt.is_completed == True)
            result = await db.execute(stmt)
            quiz_st = result.first()
            if quiz_st and quiz_st[0] > 0:
                context_parts.append(f"Quizzes: {quiz_st[0]} completed. Avg: {round(quiz_st[1], 1)}/{round(quiz_st[2], 1)}")

            # Latest Notifications
            from app.models.notification import Notification
            stmt = select(Notification.title).where(Notification.user_id == user.id, Notification.is_read == False).order_by(Notification.created_at.desc()).limit(3)
            result = await db.execute(stmt)
            notifications = result.scalars().all()
            if notifications:
                context_parts.append(f"Unread Notifications: {', '.join(notifications)}")
                
        except Exception as e:
            print(f"Error getting student context: {e}")
            pass  # Context is optional, don't fail if queries fail
        
        return ". ".join(context_parts)
    
    @classmethod
    async def find_pdf_by_name(cls, user: User, search_term: str, db: AsyncSession) -> tuple[int | None, str | None]:
        """
        Find a PDF by name that the student has access to.
        Returns (pdf_id, pdf_title) if found, (None, None) otherwise.
        """
        from app.models.pdf import PDFAssignment
        
        search_lower = search_term.lower().strip()
        
        try:
            # Get PDFs assigned to this student
            stmt = (
                select(PDF)
                .join(PDFAssignment, PDFAssignment.pdf_id == PDF.id)
                .where(PDFAssignment.student_id == user.id)
            )
            result = await db.execute(stmt)
            assigned_pdfs = result.scalars().all()
            
            for pdf in assigned_pdfs:
                title_lower = (pdf.title or "").lower()
                # Match by title or ID
                if search_lower in title_lower or title_lower in search_lower:
                    return pdf.id, pdf.title
                # Match "test-1", "pdf 1", etc. to PDF with ID 1
                if search_lower.replace("-", " ").replace("pdf", "").replace("test", "").strip() == str(pdf.id):
                    return pdf.id, pdf.title
            
            # Try loose matching
            for pdf in assigned_pdfs:
                title_words = (pdf.title or "").lower().split()
                search_words = search_lower.split()
                if any(sw in title_words or any(sw in tw for tw in title_words) for sw in search_words):
                    return pdf.id, pdf.title
                    
        except Exception as e:
            print(f"Error finding PDF by name: {e}")
        
        return None, None
    
    @classmethod
    async def extract_pdf_reference(cls, message: str, user: User, db: AsyncSession) -> tuple[int | None, str | None]:
        """
        Check if message references a specific PDF and return its ID and content.
        Patterns detected: "from test-1", "in PDF test-1", "from Smart Campus", etc.
        """
        import re
        
        message_lower = message.lower()
        
        # Patterns to detect PDF references
        patterns = [
            r'from\s+(?:pdf\s+)?["\']?(\w[\w\s-]+)["\']?',  # "from test-1", "from PDF test-1"
            r'in\s+(?:pdf\s+)?["\']?(\w[\w\s-]+)["\']?',    # "in test-1"
            r'about\s+(?:pdf\s+)?["\']?(\w[\w\s-]+)["\']?', # "about test-1"
            r'(?:pdf|document)\s+["\']?(\w[\w\s-]+)["\']?', # "PDF test-1"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                pdf_name = match.group(1).strip()
                # Skip generic words
                if pdf_name in ['the', 'this', 'that', 'my', 'a', 'an']:
                    continue
                pdf_id, pdf_title = await cls.find_pdf_by_name(user, pdf_name, db)
                if pdf_id:
                    return pdf_id, pdf_title
        
        return None, None
    
    @classmethod
    async def get_pdf_content_sample(cls, pdf_id: int, db: AsyncSession) -> str | None:
        """Get a larger sample of PDF content for explanation context."""
        try:
            stmt = select(PDF).where(PDF.id == pdf_id)
            result = await db.execute(stmt)
            pdf = result.scalar_one_or_none()
            
            if not pdf or not pdf.file_path:
                return None
            
            # Import AI Quiz service to use PDF extraction
            from app.services.ai_service import AIQuizService
            
            text = await AIQuizService.extract_text_from_pdf(pdf.file_path)
            
            # Return first 8000 chars as sample (increased for better context)
            if len(text) > 8000:
                return text[:8000] + "\n... [document continues]"
            return text
        except Exception as e:
            print(f"Error extracting PDF content: {e}")
            return None
    
    @classmethod
    def _get_module_context_prompt(cls, module: AIModule) -> str:
        """Get module-specific context for the AI."""
        module_contexts = {
            AIModule.DASHBOARD: """Student is on the main dashboard viewing their overview.
You can help with:
- Understanding their overall stats (attendance, performance)
- Navigating to specific sections
- Quick answers about any campus topic
- Suggesting what to do next based on their data""",

            AIModule.READING: """Student is reading a PDF document. IMPORTANT: You have access to the document content below.
When the student asks questions about the document:
1. STRUCTURE YOUR ANSWER: Use clear headings or bullet points to break down complex explanations
2. SEARCH the provided PDF content to find relevant information
3. Quote or reference specific details from the document (e.g., "According to section 2.1...")
4. If asked about 'tech stack', 'technologies', 'tools' etc., provide a categorized list
5. Give specific answers based on what's IN the document, not generic advice
6. If the information isn't in the provided content, say so clearly
You are an expert tutor helping them master the material through clear, structured explanation.""",

            AIModule.ATTENDANCE: """Student is viewing their attendance page.
You can explain:
- Today's attendance status (from context)
- Overall attendance percentage and stats
- Why attendance might fail: wrong location, face not detected, outside geofence
- Attendance requirements and policies
You CANNOT mark, retry, or modify attendance - that requires their action.""",

            AIModule.HOSTEL: """Student is in the hostel section.
You can explain:
- Hostel rules and timings (curfew, visitors, etc.)
- Room and hostel assignment details (from context)
- How to request maintenance
- Common hostel policies
Guide them to appropriate sections for specific actions.""",

            AIModule.OUTPASS: """Student is viewing outpass requests.
You can explain:
- How to apply for an outpass (Go to Outpass page, fill form)
- Status meanings: Pending, Approved, Rejected, Expired
- Outpass rules (advance notice, emergency procedures)
- Their current/recent outpass status (from context)
You CANNOT approve or modify outpasses - only staff can do that.""",

            AIModule.QUERIES: """Student is in the queries section.
Help them understand:
- Query = question needing clarification (academic, admin, general)
- Complaint = problem needing resolution (facilities, services)
- How to submit: fill the form with clear description
- Expected response time: usually 24-48 hours
If they describe an issue, help classify if it's a Query or Complaint.""",

            AIModule.COMPLAINTS: """Student is viewing complaints.
You can explain:
- Complaint stages: Submitted → Assigned → In Progress → Resolved
- Resolution timeline depends on issue type
- Their complaint status (from context)
- How to follow up or add more details
You CANNOT assign staff or close complaints - only admin can.""",

            AIModule.PROFILE: """Student is viewing their profile.
You can help with:
- Understanding their profile information
- Photo upload requirements (clear face, proper background)
- How profile updates work
- Department and category information""",

            AIModule.CERTIFICATES: """Student is in the certificates section.
You can explain:
- Available certificates: Bonafide, Character Certificate, etc.
- How to request: fill the form, wait for admin approval
- Processing time: usually 3-5 working days
- Their certificate request status (from context)""",

            AIModule.QUIZ: """Student is in the quizzes section listing available assessments.
You can explain:
- How quizzes work: time limit, no retakes once submitted
- How scoring is calculated
- Their previous quiz performance (from context)
- General quiz policies
IMPORTANT: If they are currently TAKING a quiz, the AI is blocked by the system.""",

            AIModule.STREAK: """(Note: Streak feature is currently inactive)""",

            AIModule.FACULTY: """Student is using the Faculty Locator.
You can help with:
- Finding a faculty member's department
- Checking if a faculty is currently in their cabin (if data available)
- Explaining how to contact faculty
- Directing to specific faculty pages""",

            AIModule.NOTIFICATIONS: """Student is viewing their notifications.
You can help with:
- Explaining specific notification types (Attendance alerts, Query responses, outpass approval)
- Helping identify which notifications need immediate action
- Directing them to relevant modules related to a notification""",

            AIModule.SETTINGS: """Student is in the settings page.
You can help with:
- Explaining account settings
- How to update preferences
- Information about the platform and version"""
        }
        return module_contexts.get(module, "Help the student with their question. Use context data when available.")
    
    @classmethod
    def _get_action_chips(cls, module: AIModule, user: User) -> list[ActionChip]:
        """Get relevant action chips based on module and user."""
        base_path = "/dashboard/student"
        
        # Common navigation suggestions
        if module == AIModule.DASHBOARD:
            chips = [
                ActionChip(label="Check Attendance", url=f"{base_path}/attendance"),
                ActionChip(label="Find Faculty", url=f"{base_path}/faculty"),
            ]
            if user.student_category == StudentCategory.HOSTELLER:
                chips.append(ActionChip(label="Request Outpass", url=f"{base_path}/hostel/outpass"))
            return chips
        
        if module == AIModule.QUERIES:
            return [
                ActionChip(label="Raise Complaint", url=f"{base_path}/complaints"),
                ActionChip(label="View My Queries", url=f"{base_path}/queries"),
            ]
        
        if module == AIModule.COMPLAINTS:
            return [
                ActionChip(label="Submit Query", url=f"{base_path}/queries"),
                ActionChip(label="My Complaints", url=f"{base_path}/complaints"),
            ]

        if module == AIModule.ATTENDANCE:
            return [
                ActionChip(label="Dashboard", url=f"{base_path}"),
                ActionChip(label="Faculty Locations", url=f"{base_path}/faculty"),
            ]

        if module == AIModule.HOSTEL:
            chips = [ActionChip(label="My Room", url=f"{base_path}/hostel")]
            if user.student_category == StudentCategory.HOSTELLER:
                chips.append(ActionChip(label="Apply Outpass", url=f"{base_path}/hostel/outpass"))
            return chips

        if module == AIModule.PROFILE:
            return [
                ActionChip(label="Update Photo", url=f"{base_path}/profile"),
                ActionChip(label="My Certificates", url=f"{base_path}/certificates"),
            ]

        if module == AIModule.CERTIFICATES:
            return [
                ActionChip(label="My Profile", url=f"{base_path}/profile"),
                ActionChip(label="Raise Query", url=f"{base_path}/queries"),
            ]

        if module == AIModule.FACULTY:
            return [
                ActionChip(label="Check Attendance", url=f"{base_path}/attendance"),
                ActionChip(label="Dashboard", url=f"{base_path}"),
            ]
        
        # Default chips for others
        return [
            ActionChip(label="Dashboard", url=f"{base_path}"),
            ActionChip(label="Help?", url=f"{base_path}/queries"),
        ]
    
    @classmethod
    async def chat(
        cls,
        user: User,
        message: str,
        module: AIModule,
        db: AsyncSession,
        history: Optional[list] = None,
        pdf_id: Optional[int] = None,
        additional_context: Optional[str] = None
    ) -> ChatResponse:
        """
        Main chat method for AI Assistant.
        
        Flow:
        1. Check access (role + quiz mode)
        2. Build context (student info + module context)
        3. Generate response with history
        4. Add action chips if relevant
        """
        # Check access
        can_access, reason = await cls.check_access(user, db)
        if not can_access:
            return ChatResponse(
                response="",
                is_blocked=True,
                blocked_reason=reason
            )
        
        # Input validation and sanitization
        message = message.strip()
        
        # Limit message length to prevent abuse (max 2000 chars)
        if len(message) > 2000:
            return ChatResponse(
                response="Your message is too long. Please keep it under 2000 characters.",
                is_blocked=False
            )
        
        if not message:
            return ChatResponse(
                response="Please enter a message.",
                is_blocked=False
            )
        
        # Check for abuse patterns
        message_lower = message.lower()
        abuse_keywords = ["quiz answer", "exam answer", "cheat", "bypass", "hack", "test answer", "give me answers"]
        if any(kw in message_lower for kw in abuse_keywords):
            return ChatResponse(
                response="I can't help with that. Please follow academic rules.",
                is_blocked=False
            )
        
        # Check for prompt injection attempts
        if cls._detect_prompt_injection(message):
            return ChatResponse(
                response="I detected an unusual pattern in your message. Please rephrase your question normally.",
                is_blocked=False
            )
        
        # Check AI health - use fallback if AI is down
        if not await cls._check_ai_health():
            return ChatResponse(
                response=cls._get_fallback_response(module),
                is_blocked=False
            )
        
        # Build context
        student_context = await cls.get_student_context(user, db)
        module_context = cls._get_module_context_prompt(module)
        
        # Add PDF context - either from current reading or from message reference
        pdf_context = ""
        referenced_pdf_title = None
        
        # First check if user referenced a PDF by name in their message
        if not pdf_id:
            ref_pdf_id, ref_pdf_title = await cls.extract_pdf_reference(message, user, db)
            if ref_pdf_id:
                pdf_id = ref_pdf_id
                referenced_pdf_title = ref_pdf_title
        
        # Now get PDF content if we have an ID (either from reading page or message reference)
        if pdf_id:
            pdf_content = await cls.get_pdf_content_sample(pdf_id, db)
            if pdf_content:
                if referenced_pdf_title:
                    pdf_context = f"\n\n[PDF Reference Detected: '{referenced_pdf_title}']\nDocument content:\n{pdf_content}"
                else:
                    pdf_context = f"\n\nCurrent PDF content:\n{pdf_content}"
        
        # Build full context
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        day_of_week = datetime.now().strftime("%A")
        
        full_context = f"""Current Time: {current_time} ({day_of_week})
Student Context: {student_context}
Current Module: {module.value}
{module_context}
{pdf_context}
{additional_context or ''}"""

        # Check cache for repeated questions (only for simple questions without history)
        context_hash = cls._get_context_hash(full_context)
        if not history or len(history) == 0:
            cached_response = cls._response_cache.get(message, context_hash)
            if cached_response:
                print(f"Cache hit for message: {message[:50]}...")
                return ChatResponse(
                    response=cached_response,
                    is_blocked=False,
                    action_chips=cls._get_action_chips(module, user)
                )

        # Generate response
        response_error = False
        try:
            response_text = await cls._generate_response(message, full_context, history)
            
            # Cache successful responses (only for simple queries without history)
            if not history or len(history) == 0:
                cls._response_cache.set(message, context_hash, response_text)
        except Exception as e:
            print(f"AI Assistant error for user {user.id}: {e}")
            response_text = "I'm having trouble processing your request right now. Please try again or contact staff if the issue persists."
            response_error = True
        
        # Get action chips only if response was successful
        action_chips = [] if response_error else cls._get_action_chips(module, user)
        
        return ChatResponse(
            response=response_text,
            is_blocked=False,
            action_chips=action_chips
        )
    
    @classmethod
    async def _generate_response(cls, message: str, context: str, history: Optional[list] = None) -> str:
        """Generate AI response using configured backend with history."""
        import asyncio
        
        api_url, headers, model = cls._get_api_config()
        
        # Build messages array - use single system message for best compatibility
        # Some AI models don't handle multiple system messages well
        system_content = f"""{cls.SYSTEM_PROMPT}

---
CURRENT SESSION CONTEXT:
{context}
---"""
        
        messages = [
            {"role": "system", "content": system_content}
        ]
        
        # Add history if provided (with validation)
        if history:
            for msg in history:
                role = None
                content = None
                
                if hasattr(msg, 'role') and hasattr(msg, 'content'):
                    role = msg.role
                    content = msg.content
                elif isinstance(msg, dict):
                    role = msg.get('role')
                    content = msg.get('content')
                
                # Skip invalid history items
                if role and content and role in ['user', 'assistant']:
                    messages.append({"role": role, "content": str(content)})
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        timeout = 60.0 if settings.OLLAMA_ENABLED else 30.0
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(api_url, headers=headers, json=payload)
                    
                    # Handle rate limiting
                    if response.status_code == 429:
                        retry_after = int(response.headers.get('retry-after', 2))
                        print(f"AI API rate limited. Retrying after {retry_after}s...")
                        await asyncio.sleep(retry_after)
                        continue
                    
                    if response.status_code != 200:
                        error_body = response.text[:500]  # Limit error body size
                        print(f"AI API error {response.status_code}: {error_body}")
                        raise ValueError(f"AI API error: {response.status_code}")
                    
                    # Safe JSON parsing
                    try:
                        data = response.json()
                        choices = data.get("choices", [])
                        if not choices:
                            raise ValueError("No choices in AI response")
                        content = choices[0].get("message", {}).get("content", "").strip()
                        if not content:
                            raise ValueError("Empty content in AI response")
                        return content
                    except (KeyError, IndexError, TypeError) as e:
                        print(f"AI response parsing error: {e}, response: {response.text[:200]}")
                        raise ValueError(f"Failed to parse AI response: {e}")
                        
            except httpx.TimeoutException:
                print(f"AI API timeout (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    raise ValueError("AI request timed out after retries")
                await asyncio.sleep(1)
            except httpx.ConnectError as e:
                print(f"AI API connection error: {e}")
                if attempt == max_retries - 1:
                    raise ValueError("Could not connect to AI service")
                await asyncio.sleep(2)
            except Exception as e:
                print(f"AI API unexpected error: {e}")
                raise
        
        raise ValueError("AI request failed after all retries")
    
    @classmethod
    async def explain_pdf_content(
        cls,
        user: User,
        pdf_id: int,
        question: str,
        db: AsyncSession
    ) -> ChatResponse:
        """
        Explain content from a specific PDF.
        
        This is used when student is reading and asks about the content.
        """
        # Check access
        can_access, reason = await cls.check_access(user, db)
        if not can_access:
            return ChatResponse(
                response="",
                is_blocked=True,
                blocked_reason=reason
            )
        
        # Get PDF content
        pdf_content = await cls.get_pdf_content_sample(pdf_id, db)
        
        if not pdf_content:
            return ChatResponse(
                response="I couldn't access the PDF content. Please make sure you have the PDF open.",
                is_blocked=False
            )
        
        # Check for quiz-related questions
        question_lower = question.lower()
        quiz_keywords = ["quiz", "exam", "test", "answer", "question paper", "what will be asked"]
        if any(kw in question_lower for kw in quiz_keywords):
            return ChatResponse(
                response="I can help explain the content, but I cannot predict quiz questions or provide answers. What concept would you like me to explain?",
                is_blocked=False
            )
        
        # Build explanation prompt
        context = f"""The student is reading a PDF document. They asked: "{question}"

PDF Content Sample:
{pdf_content}

Help explain the concept or content they're asking about. Focus on:
1. Clear, simple explanations
2. Key points from the document
3. Do NOT predict quiz questions or give exam shortcuts"""

        response_text = await cls._generate_response(question, context)
        
        return ChatResponse(
            response=response_text,
            is_blocked=False
        )
    
    @classmethod
    async def classify_intent(cls, message: str) -> str:
        """
        Classify if a message is a QUERY, COMPLAINT, or general question.
        Used to guide students to the correct module.
        """
        try:
            api_url, headers, model = cls._get_api_config()
            
            prompt = f"""Classify this student message into one of these categories:
- QUERY: Asking a question about rules, timings, policies, procedures
- COMPLAINT: Reporting a problem with facilities, maintenance issues
- GENERAL: General conversation or greeting

Message: "{message}"

Reply with ONLY ONE WORD: QUERY, COMPLAINT, or GENERAL"""

            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You classify messages. Reply with one word only."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 10
            }
            
            timeout = 30.0 if settings.OLLAMA_ENABLED else 15.0
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(api_url, headers=headers, json=payload)
                if response.status_code == 200:
                    result = response.json()["choices"][0]["message"]["content"].strip().upper()
                    if "COMPLAINT" in result:
                        return "COMPLAINT"
                    if "QUERY" in result:
                        return "QUERY"
        except Exception:
            pass
        
        return "GENERAL"
