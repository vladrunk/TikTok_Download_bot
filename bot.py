# region Imports
import asyncio
from pathlib import Path
from collections import namedtuple

from telebot.async_telebot import AsyncTeleBot
from telebot.types import User, Message
from loguru import logger as log

from helpers.db import create_table, add_video, get_video
from helpers.downloader import Downloader
from helpers.config import BOT_TOKEN, ALLOWED_TIKTOK_URLS, DB_DIR, VIDEO_PATH, ARCHIVE_TG_ID, LOG_PATH
from helpers.strings import MSG_CAPTION_VIDEO

# endregion


# region Primary setups
log.add(
    (LOG_PATH / '{time:YYYY-MM-DD hh-mm-ss}.log').as_posix(),
    backtrace=True,
    diagnose=True,
    enqueue=True,
    encoding='UTF-8',
    rotation='500 MB',
    compression='zip',
    retention='10 days'
)
bot_info: User | None = None
Video = namedtuple('Video', ('url', 'message_id', 'file_unique_id', 'file_id'))

log.debug('Initializing Telegram Bot')
bot = AsyncTeleBot(token=BOT_TOKEN)
log.debug('Initializing TikTok Downloader')
tiktok = Downloader(logger=log, save_path=VIDEO_PATH)


# endregion


# region Regular services defs
async def update_listener(messages):
    for message in messages:
        log.debug(message)


def check_url_in_msg(msg: Message) -> bool:
    log.info('Check if message contain right url')
    log.debug(f'{msg.text = }')
    return any([msg.text.startswith(url) for url in ALLOWED_TIKTOK_URLS]) and len(msg.text.split()) < 2


async def add_video_to_db(msg: Message, msg_video: Message):
    log.debug(f'{msg.text = }')
    log.debug(f'msg_video = {msg_video}')
    await add_video(
        url=msg.text,
        msg_id=msg_video.message_id,
        file_unique_id=msg_video.video.file_unique_id,
        file_id=msg_video.video.file_id
    )


async def send_video_to_archive(msg: Message, video_path: Path) -> Message:
    log.debug(f'{video_path = }')
    log.debug(f'{msg.text = }')

    log.debug('Send request to send video')
    msg_video = await bot.send_video(
        chat_id=ARCHIVE_TG_ID, video=video_path.open('rb'),
        supports_streaming=True, disable_notification=True, parse_mode='HTML',
        caption=MSG_CAPTION_VIDEO.format(url=msg.text, bot_username=bot_info.username, archive_username=ARCHIVE_TG_ID)
    )
    log.debug(f'msg_video = {msg_video}')
    return msg_video


async def forward_video_to_chat(msg: Message, msg_video: Message | None = None, video: Video | None = None):
    log.debug(f'{msg.chat = }')
    log.debug(f'{msg.text = }')
    log.debug(f'{msg_video.video.file_id = }') if msg_video else None
    log.debug(f'{video = }') if video else None

    log.debug('Send chat action "upload_video"')
    await bot.send_chat_action(chat_id=msg.chat.id, action='upload_video')

    log.debug('Send request to forward video')
    file_id = msg_video.video.file_id if not video else video.file_id
    await bot.send_video(
        chat_id=msg.chat.id, message_thread_id=msg.message_thread_id, video=file_id,
        supports_streaming=True, disable_notification=True, parse_mode='HTML',
        caption=MSG_CAPTION_VIDEO.format(url=msg.text, bot_username=bot_info.username, archive_username=ARCHIVE_TG_ID),
        reply_to_message_id=msg.message_id,
    )


async def get_video_from_db(msg: Message) -> Video | None:
    log.debug(f'{msg.text = }')
    video_info = await get_video(url=msg.text)
    log.debug(f'{video_info = }')
    video_info = Video(*video_info) if video_info else None
    return video_info


# endregion


# region Bot handlers
@bot.message_handler(func=check_url_in_msg)
async def handler_download_video_by_url(msg: Message):
    log.info(f'Message with url: {msg.text}')

    log.info('Search video in DB')
    video_data: Video | None = await get_video_from_db(msg)

    if not video_data:
        log.info(f'Download video from TikTok to server')
        video_path: Path | None = await tiktok.download(url=msg.text)

        if video_path:
            log.info('Send video to archive chat')
            msg_video = await send_video_to_archive(msg=msg, video_path=video_path)
            log.info(f'Delete video from server')
            video_path.unlink(missing_ok=True)

            if msg_video:
                log.info('Add video to DB')
                await add_video_to_db(msg, msg_video)
                log.info('Forward video to chat')
                await forward_video_to_chat(msg=msg, msg_video=msg_video)
    else:
        log.info('Forward video to chat')
        await forward_video_to_chat(msg=msg, video=video_data)


# endregion


# region Main
@log.catch
async def main():
    log.info('Prepare dir for DB')
    log.debug(f'{DB_DIR = }')
    DB_DIR.mkdir(parents=True, exist_ok=True)

    log.info("Create table in DB if it doesn't exist")
    await create_table()

    # bot.set_update_listener(update_listener)

    log.info('Get info about bot')
    global bot_info
    bot_info = await bot.get_me()
    log.debug(f'bot_info = {bot_info}')

    log.info('Bot polling')
    await bot.polling()


# endregion


if __name__ == '__main__':
    log.info('Bot launching')
    asyncio.run(main())
    log.info('Bot stopping')
