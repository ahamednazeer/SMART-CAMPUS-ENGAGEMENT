#!/usr/bin/env python3
"""
Script to add WARDEN and MAINTENANCE_STAFF to the PostgreSQL userrole enum.
Run this script once to update the database schema.
"""
import asyncio
import os
import sys

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from sqlalchemy import text

async def add_enum_values():
    """Add WARDEN and MAINTENANCE_STAFF to the userrole enum in PostgreSQL."""
    async with engine.begin() as conn:
        # Check current enum values
        result = await conn.execute(text("""
            SELECT enumlabel FROM pg_enum 
            WHERE enumtypid = 'userrole'::regtype
            ORDER BY enumsortorder;
        """))
        current_values = [row[0] for row in result.fetchall()]
        print(f"Current enum values: {current_values}")
        
        # Add WARDEN if not exists
        if 'WARDEN' not in current_values:
            await conn.execute(text("ALTER TYPE userrole ADD VALUE 'WARDEN';"))
            print(" Added WARDEN to userrole enum")
        else:
            print("ℹ️ WARDEN already exists in userrole enum")
        
        # Add MAINTENANCE_STAFF if not exists
        if 'MAINTENANCE_STAFF' not in current_values:
            await conn.execute(text("ALTER TYPE userrole ADD VALUE 'MAINTENANCE_STAFF';"))
            print(" Added MAINTENANCE_STAFF to userrole enum")
        else:
            print("ℹ️ MAINTENANCE_STAFF already exists in userrole enum")
        
        # Verify the changes
        result = await conn.execute(text("""
            SELECT enumlabel FROM pg_enum 
            WHERE enumtypid = 'userrole'::regtype
            ORDER BY enumsortorder;
        """))
        updated_values = [row[0] for row in result.fetchall()]
        print(f"Updated enum values: {updated_values}")
    
    print("\n Database enum update complete!")

if __name__ == "__main__":
    asyncio.run(add_enum_values())
