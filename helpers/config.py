from pathlib import Path
from dotenv import load_dotenv
import os


def get_env(key, default_value):
    value = os.environ.get(key)
    return value if value is not None else default_value


cwd = Path.cwd()
load_dotenv(cwd / '.env')

BOT_TOKEN: str = get_env(key='BOT_TOKEN', default_value='42424242')
ARCHIVE_TG_ID: str = get_env(key='ARCHIVE_TG_ID', default_value='@archive42')

ALLOWED_TIKTOK_URLS = [
    'https://www.tiktok.com/',
    'https://vm.tiktok.com/',
    'https://www.instagram.com/reel/',
    # 'https://music.youtube.com/watch',
]

LOG_PATH = cwd / 'log'
VIDEO_PATH = cwd / 'video'
DB_DIR = cwd / 'db'
DB_NAME = 'gotey.db'
DB_PATH = DB_DIR / DB_NAME
