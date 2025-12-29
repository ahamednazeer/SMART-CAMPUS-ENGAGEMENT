"""
Create attendance_settings table for admin configuration.
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def create_settings_table():
    """Create attendance_settings table if it doesn't exist."""
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS attendance_settings (
                id SERIAL PRIMARY KEY,
                key VARCHAR(100) NOT NULL UNIQUE,
                value VARCHAR(500) NOT NULL,
                description VARCHAR(500),
                updated_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_attendance_settings_key ON attendance_settings(key)
        """))
        print("Attendance settings table created successfully!")

if __name__ == "__main__":
    asyncio.run(create_settings_table())
