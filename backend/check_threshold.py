import asyncio
from app.core.database import async_session_maker
from app.models.attendance import CampusGeofence
from sqlalchemy import select

async def check_geofence_threshold():
    async with async_session_maker() as session:
        result = await session.execute(select(CampusGeofence).where(CampusGeofence.is_primary == True))
        geofence = result.scalar_one_or_none()
        
        if geofence:
            print(f"Primary Geofence: {geofence.name}")
            print(f"Accuracy Threshold: {geofence.accuracy_threshold} meters")
            print(f"Radius: {geofence.radius_meters} meters")
        else:
            print("No primary geofence found.")

if __name__ == "__main__":
    asyncio.run(check_geofence_threshold())
