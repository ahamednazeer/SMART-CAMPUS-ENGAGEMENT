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

## 1. Setup Local LLM (Ollama)
The system uses LLMs for quiz generation and query categorization. 

1. **Install Ollama**: Download and install from [ollama.com](https://ollama.com/).
2. **Pull the Model**:
   ```bash
   ollama pull llama3.2
   ```
3. **Keep Ollama running** in the background while using the application.

---

## 2. Database Setup (PostgreSQL)
1. **Create Database**:
   ```sql
   CREATE DATABASE smart_campus;
   ```
2. **Note**: The backend will automatically create the required tables upon startup.

---

## 3. Backend Setup (FastAPI)
1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```
2. **Create and activate Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Environment Configuration**:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - If using **Ollama**, update these settings in `.env`:
     ```env
     OLLAMA_ENABLED=true
     OLLAMA_BASE_URL=http://localhost:11434
     OLLAMA_MODEL=llama3.2
     ```
   - Configure your `DATABASE_URL` in `.env`:
     ```env
     DATABASE_URL=postgresql+asyncpg://postgres:PASSWORD@localhost:5432/smart_campus
     ```
5. **Run the Server**:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

---

## 4. Frontend Setup (Next.js)
1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```
2. **Install Dependencies**:
   ```bash
   npm install
   ```
3. **Environment Configuration**:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Ensure the API URL is correct:
     ```env
     NEXT_PUBLIC_API_URL=http://localhost:8000
     ```
4. **Run the Development Server**:
   ```bash
   npm run dev
   ```
   Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 5. Admin Credentials
The system initializes a default administrator account on first run:
- **Username**: `admin`
- **Password**: `admin123`
- **Email**: `admin@campus.edu`

---

## Project Structure
```text
.
├── backend/            # FastAPI Project
│   ├── app/            # Source Code
│   ├── uploads/        # PDF and Image storage
│   └── main.py         # Entry point
├── frontend/           # Next.js App (src-based)
│   ├── src/app/        # App Router Pages
│   └── src/components/ # Reusable UI Components
└── README.md           # This file
```
