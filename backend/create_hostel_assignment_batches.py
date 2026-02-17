#!/usr/bin/env python3
"""
Create hostel_assignment_batches table for storing auto-assign results.
Run once after pulling the latest code.
"""
import asyncio
import os
import sys

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine


async def create_table():
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS hostel_assignment_batches (
                id SERIAL PRIMARY KEY,
                hostel_id INTEGER NOT NULL REFERENCES hostels(id) ON DELETE CASCADE,
                created_by INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                assigned_count INTEGER NOT NULL DEFAULT 0,
                skipped_count INTEGER NOT NULL DEFAULT 0,
                assigned JSONB NOT NULL DEFAULT '[]'::jsonb,
                skipped JSONB NOT NULL DEFAULT '[]'::jsonb
            );
        """))

        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_hostel_assignment_batches_hostel_id
            ON hostel_assignment_batches (hostel_id);
        """))

        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_hostel_assignment_batches_created_at
            ON hostel_assignment_batches (created_at DESC);
        """))

    print("✅ hostel_assignment_batches table is ready.")


if __name__ == "__main__":
    asyncio.run(create_table())
