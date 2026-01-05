# Smart Campus Engagement System

A comprehensive campus management and engagement platform featuring AI-powered quiz generation, attendance tracking, query management, maintenance complaints, and more.

## Architecture
- **Frontend**: Next.js 16 (React 19), Tailwind CSS
- **Backend**: FastAPI (Python 3.11+), SQLAlchemy (Async), PostgreSQL
- **AI Engine**: Groq Cloud API or Local LLM via Ollama

---

## Prerequisites
Before you begin, ensure you have the following installed:
- [Node.js](https://nodejs.org/) (v18+)
- [Python](https://www.python.org/) (3.11+)
- [PostgreSQL](https://www.postgresql.org/)
- [Ollama](https://ollama.com/) (Required for Local AI features)

---

## 1. Prerequisites
Before you begin, ensure you have the following installed:
- [Node.js](https://nodejs.org/) (v18+)
- [Python](https://www.python.org/) (3.11+)
- [PostgreSQL](https://www.postgresql.org/)
- [Ollama](https://ollama.com/) (Optional: for local AI features)

---

## 2. AI Setup (Groq or Ollama)
The system requires an LLM for AI quizzes, assistant, and categorization. You can use either **Groq (Cloud)** or **Ollama (Local)**.

### Option A: Groq Cloud (Recommended)
1. Sign up/login at [Groq Console](https://console.groq.com/).
2. Generate an API Key.
3. You will add this key to your backend `.env` file later.

### Option B: Ollama (Local)
1. **Install Ollama**: Download from [ollama.com](https://ollama.com/).
2. **Pull the Model**:
   ```bash
   ollama pull llama3.2
   ```
3. Keep Ollama running in the background.

---

## 3. Database Setup (PostgreSQL)
1. **Create Database**:
   ```sql
   CREATE DATABASE smart_campus;
   ```
2. **Note**: The system uses `asyncpg`, so ensure your connection string uses `postgresql+asyncpg://`.

---

## 4. Backend Setup (FastAPI)
1. **Navigate and Setup Venv**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Environment Configuration**:
   - `cp .env.example .env`
   - Edit `.env` and configure:
     - `DATABASE_URL`: Your PostgreSQL credentials.
     - `GROQ_API_KEY`: Your key (if using Groq).
     - `OLLAMA_ENABLED`: Set to `true` (if using Ollama).
4. **Run Server**:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

---

## 5. Frontend Setup (Next.js)
1. **Navigate and Install**:
   ```bash
   cd frontend
   npm install
   ```
2. **Environment Configuration**:
   - `cp .env.example .env`
   - Ensure `NEXT_PUBLIC_API_URL` is set to `http://localhost:8000`.
   - Ensure `NEXT_PUBLIC_WS_URL` is set to `ws://localhost:8000`.
3. **Run Dev Server**:
   ```bash
   npm run dev
   ```

---

## 🔑 Default Credentials
After setup, log in at [http://localhost:3000](http://localhost:3000):
- **Role**: Admin
- **Email**: `admin@campus.edu`
- **Username**: `admin`
- **Password**: `admin123`

---

## 📁 Project Structure
```text
.
├── backend/            # FastAPI Source
│   ├── app/            # Business Logic, Models, Routers
│   ├── uploads/        # Storage for uploaded materials
│   └── main.py         # App Entry Point
├── frontend/           # Next.js SRC-based project
│   ├── src/app/        # App Router (Pages)
│   └── src/components/ # UI Components
└── DEMO_GUIDE.md       # Feature walk-through guide
```
