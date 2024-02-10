import aiosqlite
from helpers.config import DB_PATH


async def create_table():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS storage(
            url TEXT,
            msg_id TEXT,
            video_id TEXT,
            file_id TEXT);''')
        await db.commit()


async def add_video(url: str, msg_id: int, file_unique_id: str, file_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO storage VALUES(?, ?, ?, ?);",
            (url, msg_id, file_unique_id, file_id)
        )
        await db.commit()


async def get_video(url: str) -> tuple | None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM storage WHERE url=?;", (url,)) as cursor:
            video_info = await cursor.fetchone()
    return video_info
