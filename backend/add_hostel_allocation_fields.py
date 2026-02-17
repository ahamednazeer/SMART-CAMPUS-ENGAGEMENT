#!/usr/bin/env python3
"""
Add hostel allocation fields:
- hostels.hostel_type
- users.gender
- users.degree
- users.study_year

Run this once after pulling the latest code.
"""
import asyncio
import os
import sys

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine


async def add_columns():
    async with engine.begin() as conn:
        # Hostels: hostel_type
        await conn.execute(text("""
            ALTER TABLE hostels
            ADD COLUMN IF NOT EXISTS hostel_type VARCHAR(10) NOT NULL DEFAULT 'CO_ED';
        """))

        # Users: gender, degree, study_year
        await conn.execute(text("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS gender VARCHAR(10);
        """))
        await conn.execute(text("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS degree VARCHAR(50);
        """))
        await conn.execute(text("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS study_year INTEGER;
        """))

    print("✅ Added hostel allocation fields (if missing).")


if __name__ == "__main__":
    asyncio.run(add_columns())
