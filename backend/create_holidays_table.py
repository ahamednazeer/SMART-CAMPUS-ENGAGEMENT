"""
Create holidays table for working day calendar.
Run this script to add the holidays table to the database.
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def create_holidays_table():
    """Create holidays table if it doesn't exist."""
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS holidays (
                id SERIAL PRIMARY KEY,
                date DATE NOT NULL UNIQUE,
                name VARCHAR(200) NOT NULL,
                description VARCHAR(500),
                holiday_type VARCHAR(50) DEFAULT 'GENERAL',
                is_recurring BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_holidays_date ON holidays(date)
        """))
        print("Holidays table created successfully!")

if __name__ == "__main__":
    asyncio.run(create_holidays_table())
