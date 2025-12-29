import sys
import os

# Add backend directory to path
sys.path.append("/Users/syed.ahamed/Downloads/SMART-CAMPUS-ENGAGEMENT/backend")

try:
    from app.core.config import settings
    print(f"DATABASE_URL: {settings.DATABASE_URL}")
    if "asyncpg" in settings.DATABASE_URL:
        print("SUCCESS: asyncpg driver is present.")
    else:
        print("FAILURE: asyncpg driver is MISSING.")
except Exception as e:
    print(f"Error loading settings: {e}")
