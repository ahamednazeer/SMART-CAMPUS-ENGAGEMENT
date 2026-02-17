#!/usr/bin/env python3
"""
Seed demo data for hostel allocation:
- Create a hostel (if missing)
- Create N rooms
- Create N hosteller students
- Auto-assign students to rooms
"""
import argparse
import asyncio
import random
import sys
from pathlib import Path

# Add parent directory to path to import app modules
CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))

from sqlalchemy import select

from app.core.database import async_session_maker
from app.models.hostel import Hostel, HostelRoom, HostelType
from app.models.user import User, UserRole, StudentCategory, Gender
from app.services.hostel_service import HostelService
from app.schemas.hostel import HostelAutoAssignConfirmItem
from app.core.security import hash_password


DEPARTMENTS = [
    "CSE",
    "ECE",
    "EEE",
    "MECH",
    "CIVIL",
    "AI&DS",
    "IT",
]

DEGREES = [
    "BE",
    "BSC",
]


def pick_gender(hostel_type: HostelType, index: int, mixed: bool) -> Gender:
    if mixed:
        return Gender.MALE if index % 2 == 0 else Gender.FEMALE
    if hostel_type == HostelType.BOYS:
        return Gender.MALE
    if hostel_type == HostelType.GIRLS:
        return Gender.FEMALE
    return Gender.MALE if index % 2 == 0 else Gender.FEMALE


async def seed(
    hostel_name: str,
    rooms: int,
    students: int,
    hostel_type: HostelType,
    room_capacities: list[int],
    mixed_gender: bool,
    only_students: bool,
    only_rooms: bool,
    skip_auto_assign: bool,
) -> None:
    async with async_session_maker() as session:
        # Hostel
        result = await session.execute(select(Hostel).where(Hostel.name == hostel_name))
        hostel = result.scalar_one_or_none()

        if not hostel:
            hostel = Hostel(
                name=hostel_name,
                address=f"{hostel_name} Campus Road",
                capacity=max(rooms * 2, 1),
                hostel_type=hostel_type,
                is_active=True,
            )
            session.add(hostel)
            await session.flush()
        else:
            if hostel.hostel_type != hostel_type:
                print(
                    f"⚠️ Hostel '{hostel_name}' exists with type {hostel.hostel_type}. "
                    f"Requested type {hostel_type} will not override."
                )
            hostel_type = hostel.hostel_type

        # Rooms
        created_rooms = 0
        if not only_students:
            room_result = await session.execute(
                select(HostelRoom).where(HostelRoom.hostel_id == hostel.id)
            )
            existing_rooms = {room.room_number for room in room_result.scalars().all()}
            for i in range(1, rooms + 1):
                room_number = f"R{i:03d}"
                if room_number in existing_rooms:
                    continue
                capacity = room_capacities[(i - 1) % len(room_capacities)]
                room = HostelRoom(
                    hostel_id=hostel.id,
                    room_number=room_number,
                    floor=((i - 1) // 25) + 1,
                    capacity=capacity,
                    is_active=True,
                )
                session.add(room)
                created_rooms += 1

        # Students
        created_students = 0
        if not only_rooms:
            user_result = await session.execute(
                select(User.username, User.register_number)
                .where(User.username.like("demo_hosteller_%"))
            )
            existing_usernames = set()
            existing_registers = set()
            for username, register_number in user_result.all():
                existing_usernames.add(username)
                if register_number:
                    existing_registers.add(register_number)

            index = 1
            while created_students < students:
                current_index = index
                username = f"demo_hosteller_{current_index:03d}"
                register_number = f"DEMO{current_index:05d}"
                index += 1

                if username in existing_usernames or register_number in existing_registers:
                    continue

                gender = pick_gender(hostel_type, current_index, mixed_gender)
                study_year = random.randint(1, 4)
                degree = random.choice(DEGREES)
                department = random.choice(DEPARTMENTS)

                user = User(
                    username=username,
                    email=f"{username}@campus.edu",
                    password_hash=hash_password("student123"),
                    first_name="Demo",
                    last_name=f"Student{current_index:03d}",
                    role=UserRole.STUDENT,
                    student_category=StudentCategory.HOSTELLER,
                    register_number=register_number,
                    department=department,
                    batch=str(2026 - (4 - study_year)),
                    degree=degree,
                    study_year=study_year,
                    gender=gender,
                    is_active=True,
                )
                session.add(user)
                created_students += 1

        await session.commit()

        # Auto-assign
        if skip_auto_assign or only_students:
            result = None
        else:
            service = HostelService(session)
            preview = await service.recommend_assignments_for_hostel(hostel.id)
            confirm_items = [
                HostelAutoAssignConfirmItem(student_id=rec.student_id, room_id=rec.room_id)
                for rec in preview.recommendations
            ]
            result = await service.confirm_auto_assignments(hostel.id, confirm_items, created_by=None)

        print(
            f"✅ Hostel '{hostel.name}' ready. "
            f"Rooms created: {created_rooms}, Students created: {created_students}."
        )
        if result:
            print(
                f"Auto-assign result -> Assigned: {result.assigned_count}, Skipped: {result.skipped_count}."
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed hostel demo data.")
    parser.add_argument("--hostel-name", default="Demo Hostel", help="Hostel name")
    parser.add_argument("--rooms", type=int, default=100, help="Number of rooms")
    parser.add_argument("--students", type=int, default=100, help="Number of students")
    parser.add_argument(
        "--hostel-type",
        choices=["BOYS", "GIRLS", "CO_ED"],
        default="CO_ED",
        help="Hostel type",
    )
    parser.add_argument(
        "--room-capacities",
        default="3,5,6",
        help="Comma-separated list of room capacities to cycle through (max 6).",
    )
    parser.add_argument(
        "--mixed-gender",
        action="store_true",
        help="Generate mixed-gender students (ignores hostel type).",
    )
    parser.add_argument(
        "--only-students",
        action="store_true",
        help="Only create students (no rooms).",
    )
    parser.add_argument(
        "--only-rooms",
        action="store_true",
        help="Only create rooms (no students).",
    )
    parser.add_argument(
        "--skip-auto-assign",
        action="store_true",
        help="Skip auto-assign step.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    capacities = []
    for raw in args.room_capacities.split(","):
        raw = raw.strip()
        if not raw:
            continue
        value = int(raw)
        if value < 1 or value > 6:
            raise ValueError("Room capacity must be between 1 and 6.")
        capacities.append(value)
    if not capacities:
        raise ValueError("Provide at least one room capacity.")
    asyncio.run(
        seed(
            hostel_name=args.hostel_name,
            rooms=args.rooms,
            students=args.students,
            hostel_type=HostelType[args.hostel_type],
            room_capacities=capacities,
            mixed_gender=args.mixed_gender,
            only_students=args.only_students,
            only_rooms=args.only_rooms,
            skip_auto_assign=args.skip_auto_assign,
        )
    )
