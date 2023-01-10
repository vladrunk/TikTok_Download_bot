import telebot
from pathlib import Path
import asyncio
from loguru import logger as log
from telebot.async_telebot import AsyncTeleBot
import moviepy.editor as mp
import moviepy.video.fx.all as mp_fx_all
from tiktok import TikTok
from config import BOT_TOKEN, ALLOWED_TIKTOK_LINKS, LOG_LAUNCH_MSG

log.add(
    './log/{time:YYYY-MM-DD}.log',
    backtrace=True,
    diagnose=True,
    enqueue=True,
    encoding='UTF-8',
    rotation='500 MB',
    compression='zip',
    retention='10 days'
)
bot = AsyncTeleBot(token=BOT_TOKEN)
tiktok = TikTok(logger=log)


def resize_video(m, video_path: str):
    log.info(
        f'[chat={m.chat.id}][user={m.from_user.id}][file_id={m.video.file_id}] '
        f'Resize video'
    )
    clip_orig = mp.VideoFileClip(video_path)
    w, h = clip_orig.size
    if w > h:
        clip_crop = mp_fx_all.crop(clip_orig, x1=(w - h) / 2, x2=w - (w - h) / 2, y1=0, y2=h)
    else:
        clip_crop = mp_fx_all.crop(clip_orig, x1=0, x2=w, y1=(h - w) / 2, y2=h - (h - w) / 2)
    video_path_resized = f'{video_path}_resized.mp4'
    clip_crop.write_videofile(video_path_resized)
    return video_path_resized


@bot.message_handler(content_types=['video'])
async def start(m: telebot.types.Message):
    log.info(
        f'[chat={m.chat.id}][user={m.from_user.id}][file_id={m.video.file_id}] '
        f'Get request for convert video into video_note'
    )
    video_path, video_path_resized = '', ''
    if m.video.duration < 60:
        try:
            log.info(
                f'[chat={m.chat.id}][user={m.from_user.id}][file_id={m.video.file_id}] '
                f'Get file_path on server'
            )
            file_path = await bot.get_file(m.video.file_id)
            log.info(
                f'[chat={m.chat.id}][user={m.from_user.id}][file_id={m.video.file_id}] '
                f'Download video from telegram'
            )
            downloaded_file = await bot.download_file(file_path.file_path)
            file_name = m.video.file_name \
                if m.video.file_name \
                else f'{m.video.file_unique_id}.{m.video.mime_type.split("/")[1]}'
            log.info(
                f'[chat={m.chat.id}][user={m.from_user.id}][file_id={m.video.file_id}] '
                f'Download video from Telegram {file_name}'
            )
            video_path = f'./video/{file_name}'
            log.info(
                f'[chat={m.chat.id}][user={m.from_user.id}][file_id={m.video.file_id}] '
                f'Save video into SSD'
            )
            with open(video_path, 'wb') as f:
                f.write(downloaded_file)
            video_path_resized = resize_video(m, video_path)
            log.info(
                f'[chat={m.chat.id}][user={m.from_user.id}][file_id={m.video.file_id}] '
                f'Send resized video to Telegram'
            )
            with open(video_path_resized, 'rb') as f:
                await bot.send_chat_action(
                    chat_id=m.chat.id,
                    action='upload_video'
                )
                await bot.send_video_note(
                    chat_id=m.chat.id,
                    data=f,
                )
        finally:
            if video_path:
                Path(video_path).unlink()
            if video_path_resized:
                Path(video_path_resized).unlink()
    else:
        log.error(
            f'[chat={m.chat.id}][user={m.from_user.id}][file_id={m.video.file_id}] '
            f'The maximum duration of the video must be: 59 seconds. Current={m.video.duration} seconds.'
        )
        await bot.reply_to(
            message=m,
            text=f'The maximum duration of the video must be: 59 seconds. Current={m.video.duration} seconds.'
                 f'\n\n'
                 f'Error code: {m.video.file_id}'
        )


@bot.message_handler(
    func=lambda m: any([m.text.startswith(b) for b in ALLOWED_TIKTOK_LINKS]) and len(m.text.split()) < 2)
async def send_video(m: telebot.types.Message):
    log.info(
        f'[chat={m.chat.id}][user={m.from_user.id}][link={m.text}] '
        f'Download request id={m.message_id}'
    )
    m_reply = await bot.reply_to(
        message=m,
        text='Качаю видева..',
    )
    log.info(
        f'[chat={m.chat.id}][user={m.from_user.id}][link={m.text}] '
        f'Get video link'
    )
    video_link = await tiktok.get_video(m)
    if video_link:
        log.info(
            f'[chat={m.chat.id}][user={m.from_user.id}][link={m.text}] '
            f'Init send video'
        )
        await bot.send_chat_action(chat_id=m.chat.id, action='upload_video')
        log.info(
            f'[chat={m.chat.id}][user={m.from_user.id}][link={m.text}] '
            f'Load to telegram server'
        )
        m_video = await bot.send_video(
            chat_id=m.chat.id,
            video=video_link,
            caption=f'<i><a href="{m.text}">video.link</a></i>'
                    f'<b> | </b>'
                    f'<i><a href="tg://user?id={m_reply.from_user.username}">bot</a></i>',
            supports_streaming=True,
            disable_notification=True,
            parse_mode='HTML',
        )
        if m_video:
            log.info(
                f'[chat={m.chat.id}][user={m.from_user.id}][link={m.text}] '
                f'The send is successful id={m_video.message_id}'
            )
            log.info(
                f'[chat={m.chat.id}][user={m.from_user.id}][link={m.text}] '
                f'Delete requested message id={m.message_id}'
            )
            await bot.delete_message(chat_id=m.chat.id, message_id=m.message_id)
    log.info(
        f'[chat={m.chat.id}][user={m.from_user.id}][link={m.text}] '
        f'Delete reply message id={m_reply.message_id}'
    )
    await bot.delete_message(chat_id=m_reply.chat.id, message_id=m_reply.message_id)


log.warning(LOG_LAUNCH_MSG)
asyncio.run(bot.polling())
