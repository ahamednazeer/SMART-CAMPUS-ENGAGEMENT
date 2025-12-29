# Smart Campus Engagement System - Backend

## Tech Stack
- Python 3.11+
- FastAPI
- SQLAlchemy (async)
- PostgreSQL
- JWT Authentication

## Project Structure (Layered Architecture)
```
backend/
├── main.py
├── requirements.txt
├── app/
│   ├── core/           # Infrastructure
│   ├── models/         # ORM Models
│   ├── schemas/        # Pydantic DTOs
│   ├── repositories/   # Data Access
│   ├── services/       # Business Logic
│   ├── routers/        # API Controllers
│   └── utils/          # Helpers
```

## Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy .env.example to .env and configure
cp .env.example .env

# Run the server
uvicorn main:app --reload --port 8000
```
