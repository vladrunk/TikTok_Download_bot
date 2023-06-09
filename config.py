from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv(Path('.env'))


def get_env(key, default_value):
    value = os.environ.get(key)
    return value if value is not None else default_value


BOT_TOKEN = get_env(key='BOT_TOKEN', default_value='42424242')
# Group: "Bot Service"
BOT_SERVICE_CHAT_ID = get_env(key='BOT_SERVICE_CHAT_ID', default_value=42)
# ID for Admin bot
ADMIN_TG_ID = get_env(key='ADMIN_TG_ID', default_value=42)
# ID for Archive chat
ARCHIVE_TG_ID = get_env(key='ARCHIVE_TG_ID', default_value=42)


ALLOWED_TIKTOK_LINKS = ['https://www.tiktok.com/', 'https://vm.tiktok.com/', 'https://www.instagram.com/reel/', ]
# True if Prod mode | False is Dev mode
PROD = False
if PROD:
    # Thread: "Approve" in group: "Bot Service"
    BOT_SERVICE_CHAT_THREAD_ID = 2
else:
    # Thread: "Approve DevBot" in group: "Bot Service"
    BOT_SERVICE_CHAT_THREAD_ID = 46

TABLE = {
    'chat_id': 0,
    'approve': 1,
    'first_name': 2,
    'last_name': 3,
    'username': 4,
    'title': 5,
    'invite': 6,
    'approve_msg_id': 7,
}
# Path to dir with video
PATH_VIDEO = './video/'
# Path to dir with db
PATH_DB = './db/'
# Name of the DB
DB_NAME = 'gotey.db'
# Full path to DB
DB_FULLPATH = f'{PATH_DB}{DB_NAME}'
