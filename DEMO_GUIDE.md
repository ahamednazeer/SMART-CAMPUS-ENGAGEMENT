# Institution Mangement System Engagement System - Demo Guide

Welcome to the **Institution Mangement System Engagement System**, a state-of-the-art platform designed to revolutionize campus life through AI-driven learning, seamless administration, and interactive engagement.

---

## 🏗️ Architecture & Tech Stack

The system is built on a modern, high-performance stack:

- **Frontend**: [Next.js 16](https://nextjs.org/) (React 19) with [Tailwind CSS](https://tailwindcss.com/) for a sleek, responsive UI.
- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11+) providing a high-performance, asynchronous API.
- **Database**: [PostgreSQL](https://www.postgresql.org/) with [SQLAlchemy](https://www.sqlalchemy.org/) (Async) for robust data management.
- **AI Engine**: Integrated with **Groq Cloud API** and **Ollama** for local/cloud LLM capabilities.
- **Real-time**: [WebSockets](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API) for live updates and interactive features.

---

## 🎓 Student Experience

The student dashboard is the heart of the platform, offering a comprehensive suite of tools for academic success and campus integration.

### 🧠 Modern Learning Suite
- **AI Quiz Generation**: Automatically generate quizzes from uploaded PDFs or course content. Personalized difficulty levels and instant feedback.
- **Smart Flashcards**: AI-curated flashcards to reinforce memory and learning.
- **Interactive Whiteboard**: A collaborative space for sketching ideas and solving problems.
- **Knowledge Graph**: Visualize connections between different subjects and topics for a holistic understanding.
- **Reading Hub**: Access course materials and curated reading lists with AI-powered summaries.

### 📈 Academic Management
- **Attendance Tracker**: Real-time view of attendance percentages across all courses with trend analysis.
- **Results & Performance**: View exam results and track academic progress through intuitive charts.
- **Course Reviews**: Provide feedback on courses and view peer reviews to make informed academic choices.

### 🏠 Campus Life & Services
- **Hostel Management**: Submit room requests, report maintenance issues, and manage hostel-related activities.
- **Outpass System**: Apply for outpasses digitally with a streamlined approval workflow.
- **Bonafide Requests**: Apply for official bonafide certificates with just a few clicks.
- **Maintenance Complaints**: Report facility issues with photo attachments and status tracking.

### 💬 Communication & Support
- **AI Assistant**: A 24/7 companion available via chat or voice (STT) to answer campus-related queries.
- **Query Portal**: Submit queries to specific departments and receive tracked responses.
- **Study Circles**: Create or join student-led study groups for collaborative learning.
- **Streaks & Engagement**: Stay motivated with daily streaks and engagement rewards.

---

## 🛠️ Administrative Experience

Empowering administrators with powerful tools to manage the campus ecosystem effectively.

### 👥 User & Content Management
- **Unified User Management**: Create, edit, and manage profiles for Students, Faculty, and Staff.
- **PDF Content Processor**: Upload academic PDFs which are automatically parsed and converted into interactive learning materials.
- **Course Administration**: Define course curriculum, assign faculty, and manage enrollments.

### 📋 Operations & Approvals
- **Attendance Monitoring**: Faculty can mark attendance via geofencing or manual input; Admins get a bird's-eye view.
- **Request Workflows**: Approve/Reject Outpass, Hostel, and Bonafide requests through a centralized queue.
- **Complaint Resolution**: Assign and track maintenance complaints to resolution.
- **Audit Logs**: For high-level oversight of all system activities and critical changes.

### 📊 Analytics & Governance
- **Dynamic Dashboards**: Real-time statistics on student engagement, attendance trends, and system health.
- **Faculty Location Tracker**: Real-time faculty availability and location within the campus.
- **Warden Dashboard**: Specialized view for hostel wardens to manage queries and complaints specific to residential life.

---

## 🤖 AI Features Deep Dive

The system's "Smart" capabilities are driven by advanced AI integrations:

1. **AI Quiz & Flashcard Engine**: Uses LLMs (Llama 3.2 via Groq/Ollama) to analyze academic text and generate contextually accurate questions and cards.
2. **AI Voice Assistant**: Implements Speech-to-Text (STT) for natural language interactions, allowing students to ask questions hands-free.
3. **Automated Query Categorization**: Intelligently routes student queries to the correct department (Admin, Warden, Faculty) using NLP.
4. **Knowledge Graph Extraction**: Automatically identifies entities and relationships within course materials to build a visual learning map.

---

## 🚀 Getting Started for Demo

1. **Access**: [http://localhost:3000](http://localhost:3000)
2. **Default Admin**: `admin` / `admin123`
3. **Demo User**: `student_demo` / `password123` (Use a registered student for best results)

---

## 🎭 Detailed Demo Scenarios

### 1. The "Smart Learning" Flow (AI & Personalization)
*Goal: Show how AI transforms static PDFs into interactive learning.*

1. **Login as Admin**: Navigate to `PDF Management`.
2. **Upload & Assign**: Upload a sample academic PDF. Assign it to the "2024-CSE-A" batch.
3. **Login as Student**: Go to the `Reading Hub`. Open the newly assigned PDF.
4. **AI Generation**: Click "Generate AI Quiz". Watch it create personalized questions from the PDF text.
5. **Knowledge Visualization**: Go to `Knowledge Graph`. Show the new nodes created from the PDF content, highlighting "Weak Areas" that need review.
6. **Flashcards**: Navigate to `Smart Flashcards` to show AI-curated revision cards.

### 2. The "Campus Life" Flow (Institutional Operations)
*Goal: Demonstrate seamless attendance and request workflows.*

1. **Student - Mark Attendance**: 
   - Open the `Attendance` page.
   - Show the dynamic map and geofence verification.
   - Mark attendance (requires camera) and show instant status update.
2. **Student - Outpass Request**:
   - Go to `Hostel Services`.
   - Click `Apply for Outpass`. Fill in the reason (e.g., "Visiting Home") and destination.
   - Show the "Pending" status in the history tab.
3. **Admin/Warden - Approval**:
   - Login as Admin. Go to `Hostel Management`.
   - Locate the pending request and click `Approve`.
4. **Student - Digital Outpass**:
   - Return to Student Hostel page. 
   - Show the `Approved` status and the `View Digital Outpass` button (active during the approved time window).

### 3. The "Social Collaboration" Flow (Interactive Features)
*Goal: Show peer-to-peer engagement and collaborative tools.*

1. **Study Circles**:
   - Navigate to `Study Circles`. 
   - Select a circle and show the hash-based channels (like Discord/Slack).
   - Send a message and show real-time synchronization.
2. **Interactive Whiteboard**:
   - Open the `Whiteboard` from the Learning suite.
   - Create a new session. 
   - Use the drawing tools, shapes, and colors.
   - Save a "Snapshot" of the work for future reference.

### 4. The "Administrative Oversight" Flow (Analytics)
*Goal: Demonstrate governance and tracking capabilities.*

1. **Analytics Dashboard**:
   - Show the main Admin dashboard with real-time student activity trends.
2. **Faculty Tracking**:
   - Navigate to `Faculty Locations`. Show the interactive map indicating where faculty members are currently available on campus.
3. **Audit Logs**:
   - Show the `Audit Logs` to demonstrate transparent tracking of all system changes.

---

## 🛠️ Verification Checklist
- [ ] Backend server is running (`python run.py`)
- [ ] Frontend dev server is running (`npm run dev`)
- [ ] Groq/Ollama API is configured and responsive
- [ ] PostgreSQL database is connected
