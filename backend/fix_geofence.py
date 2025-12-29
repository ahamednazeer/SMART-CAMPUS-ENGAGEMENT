import asyncio
from app.core.database import async_session_maker
from app.models.attendance import CampusGeofence
from sqlalchemy import select

async def fix_geofence():
    async with async_session_maker() as session:
        result = await session.execute(select(CampusGeofence).where(CampusGeofence.id == 1))
        geofence = result.scalar_one_or_none()
        
        if geofence:
            geofence.is_primary = True
            await session.commit()
            print(f"Updated geofence '{geofence.name}' to be PRIMARY.")
        else:
            print("Geofence ID 1 not found.")

if __name__ == "__main__":
    asyncio.run(fix_geofence())
