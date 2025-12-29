import asyncio
from app.core.database import async_session_maker
from app.models.attendance import CampusGeofence
from sqlalchemy import select

async def check_geofences():
    async with async_session_maker() as session:
        result = await session.execute(select(CampusGeofence))
        geofences = result.scalars().all()
        
        print(f"Found {len(geofences)} geofences:")
        for g in geofences:
            print(f"- ID: {g.id}, Name: {g.name}, Is Primary: {g.is_primary}, Is Active: {g.is_active}")

if __name__ == "__main__":
    asyncio.run(check_geofences())
