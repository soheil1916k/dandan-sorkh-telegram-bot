import aiosqlite
import asyncio
from datetime import datetime

DB_PATH = "reservations.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                full_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                specialty TEXT NOT NULL,
                date TEXT NOT NULL,          -- YYYY-MM-DD
                time TEXT NOT NULL,          -- HH:MM
                reservation_code TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def get_available_times(date: str):
    # فرض: ساعات کاری 9 تا 17 با فواصل 1.5 ساعته
    all_slots = ["09:00", "10:30", "12:00", "13:30", "15:00", "16:30"]
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT time FROM reservations WHERE date = ?", (date,))
        booked = {row[0] for row in await cursor.fetchall()}
    return [slot for slot in all_slots if slot not in booked]

async def create_reservation(user_id, full_name, phone, specialty, date, time, code):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO reservations (user_id, full_name, phone, specialty, date, time, reservation_code)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, full_name, phone, specialty, date, time, code))
        await db.commit()

async def get_reservation_by_code(code):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT * FROM reservations WHERE reservation_code = ?", (code,))
        return await cursor.fetchone()

async def delete_reservation_by_code(code):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM reservations WHERE reservation_code = ?", (code,))
        await db.commit()
        return db.total_changes > 0

async def get_user_reservations(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT * FROM reservations WHERE user_id = ?", (user_id,))
        return await cursor.fetchall()