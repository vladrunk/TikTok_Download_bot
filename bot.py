import aiosqlite
import asyncio
from pathlib import Path

import telebot
from telebot.async_telebot import AsyncTeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from loguru import logger as log
import moviepy.editor as mp
import moviepy.video.fx.all as mp_fx_all

from tiktok import TikTok
from config import BOT_TOKEN, ALLOWED_TIKTOK_LINKS, LOG_LAUNCH_MSG, BOT_SERVICE_CHAT_ID, BOT_SERVICE_CHAT_THREAD_ID, \
    MSG_NEW_CHAT, MSG_NEW_GROUP, KBRD_DECLINE, KBRD_DECLINE_CALL, KBRD_APPROVE_CALL, KBRD_APPROVE, TABLE

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# Primary setups
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
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


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# Regular services defs
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
async def update_listener(messages):
    for message in messages:
        log.info(message)


async def resize_video(m: telebot.types.Message, video_path: str):
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
    log.info(
        f'[chat={m.chat.id}][user={m.from_user.id}][file_id={m.video.file_id}] '
        f'Resize video - Done'
    )
    return video_path_resized


def check_tiktok_link_in_msg(m: telebot.types.Message):
    return any([m.text.startswith(b) for b in ALLOWED_TIKTOK_LINKS]) and len(m.text.split()) < 2


async def get_chat_info(m: telebot.types.Message):
    log.info(f'[chat={m.chat.id}][user={m.from_user.id}] '
             f'Get chat info from DB')
    async with aiosqlite.connect('./db/gotey.db') as db:
        async with db.execute("SELECT * FROM chats WHERE chat_id=?;", (m.chat.id,)) as cursor:
            chat_info = await cursor.fetchone()
    return chat_info


async def create_chat(m: telebot.types.Message):
    log.info(f'[chat={m.chat.id}][user={m.from_user.id}] '
             f'Add chat into DB')
    async with aiosqlite.connect('./db/gotey.db') as db:
        await db.execute(
            "INSERT INTO chats VALUES(?, ?, ?, ?, ?, ?, ?, ?);",
            (
                m.chat.id, 0, m.chat.first_name, m.chat.last_name, m.chat.username, m.chat.title,
                m.from_user.id if m.content_type == 'new_chat_members' else 0,
                0,
            )
        )
        await db.commit()


def markup_approve():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(KBRD_APPROVE, callback_data=KBRD_APPROVE_CALL))
    return markup


def markup_decline():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(KBRD_DECLINE, callback_data=KBRD_DECLINE_CALL))
    return markup


async def save_approve_msg_id(m: telebot.types.Message, approve_msg: telebot.types.Message):
    log.info(f'[chat={m.chat.id}][user={m.from_user.id}] '
             f'Save id for message approve in service chat')
    async with aiosqlite.connect('./db/gotey.db') as db:
        await db.execute("UPDATE chats SET approve_msg_id = ? WHERE chat_id = ?;", (approve_msg.message_id, m.chat.id,))
        await db.commit()


async def change_approve_status(call):
    log.info(f'[chat={call.message.chat.id}][user={call.message.from_user.id}] '
             f'Change approve status to "{call.data}"')
    async with aiosqlite.connect('./db/gotey.db') as db:
        await db.execute(
            "UPDATE chats SET approve = ? WHERE chat_id = ?;",
            (
                1 if call.data == KBRD_APPROVE_CALL else 0,
                int(call.message.text.split('ID: ')[-1]),
            )
        )
        await db.commit()


async def get_approve_status(m):
    log.info(f'[chat={m.chat.id}][user={m.from_user.id}] '
             f'Get approve status')
    async with aiosqlite.connect('./db/gotey.db') as db:
        async with db.execute("SELECT approve FROM chats WHERE chat_id=?;", (m.chat.id,)) as cursor:
            chat_approve_info = await cursor.fetchone()
    return chat_approve_info[0]


async def is_new_chat(m):
    chat_info = await get_chat_info(m)
    if chat_info:
        return False, chat_info
    else:
        await create_chat(m)
        return True, await get_chat_info(m)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# Bot handlers
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
@bot.callback_query_handler(func=lambda call: call.data in [KBRD_APPROVE_CALL, KBRD_DECLINE_CALL])
async def callback_change_approve(call):
    await change_approve_status(call)
    log.info(f'[chat={call.message.chat.id}][user={call.message.from_user.id}] '
             f'Change approve button to "{call.data}" in service chat')
    await bot.edit_message_reply_markup(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup_decline() if call.data == KBRD_APPROVE_CALL else markup_approve(),
    )


@bot.message_handler(commands=['start'])
async def cmd_start(m: telebot.types.Message):
    is_new, chat = await is_new_chat(m)
    if is_new:
        log.info(f'[chat={m.chat.id}][user={m.from_user.id}] '
                 f'New user send /start')
        await bot.send_message(
            chat_id=m.chat.id,
            text='''Hello.
        To download a video from TikTok, just send a link to the video in this chat. Bot is not active for you. 
            
        To activate it, text him @vladrunk.''',
        )
    else:
        await bot.send_message(
            chat_id=m.chat.id,
            text=f'''Ah! Here We Go Again...
To download a video from TikTok, just send a link to the video in this chat. Bot is {"" if chat[TABLE["approve"]] else "not "}active for you.

{"" if chat[TABLE["approve"]] else "To activate it, text him @vladrunk. "}''',
        )

    if not chat[TABLE['approve_msg_id']]:
        log.info(f'[chat={m.chat.id}][user={m.from_user.id}] '
                 f'Send approve message')
        approve_msg = await bot.send_message(
            chat_id=BOT_SERVICE_CHAT_ID,
            message_thread_id=BOT_SERVICE_CHAT_THREAD_ID,
            text=MSG_NEW_CHAT.format(
                first_name=m.chat.first_name,
                last_name=m.chat.last_name if m.chat.last_name else '',
                username=m.chat.username,
                user_id=m.chat.id,
            ),
            parse_mode='HTML',
            reply_markup=markup_approve(),
        )
        await save_approve_msg_id(m, approve_msg)


@bot.message_handler(content_types=['new_chat_members'], func=lambda m: m.chat.id != -1001699098294)
async def ct_new_chat_members(m: telebot.types.Message):
    is_new, chat = await is_new_chat(m)
    if is_new:
        log.info(f'[chat={m.chat.id}][user={m.from_user.id}] '
                 f'First add bot to new group')
        await bot.send_message(
            chat_id=m.chat.id,
            text='''Nice group!
        To download a video from TikTok, just send a link to the video in this chat. Bot is not active for this chat. 
            
        To activate it, text him @vladrunk.''',
        )
    else:
        await bot.send_message(
            chat_id=m.chat.id,
            text=f'''Ah! Here We Go Again...
To download a video from TikTok, just send a link to the video in this chat. Bot is {"" if chat[TABLE["approve"]] else "not "}active for this chat.

{"" if chat[TABLE["approve"]] else "To activate it, text him @vladrunk. "}''',
        )

    if not chat[TABLE['approve_msg_id']]:
        log.info(f'[chat={m.chat.id}][user={m.from_user.id}] '
                 f'Send approve message')
        approve_msg = await bot.send_message(
            chat_id=BOT_SERVICE_CHAT_ID,
            message_thread_id=BOT_SERVICE_CHAT_THREAD_ID,
            text=MSG_NEW_GROUP.format(
                first_name=m.from_user.first_name,
                last_name=m.from_user.last_name if m.from_user.last_name else '',
                username=m.from_user.username,
                user_id=m.from_user.id,
                title=m.chat.title,
                chat_id=m.chat.id,
            ),
            parse_mode='HTML',
            reply_markup=markup_approve(),
        )
        await save_approve_msg_id(m, approve_msg)


@bot.message_handler(content_types=['video'])
async def convert_to_video_note(m: telebot.types.Message):
    approved = await get_approve_status(m)
    if not approved:
        text = 'Sorry, this chat is not approved. Contact with @vladrunk to approved chat.'
        await bot.reply_to(m, text)
    else:
        log.info(f'[chat={m.chat.id}][user={m.from_user.id}][file_id={m.video.file_id}] '
                 f'Get request for convert video into video_note')
        video_path, video_path_resized = '', ''
        if m.video.duration < 60:
            try:
                log.info(f'[chat={m.chat.id}][user={m.from_user.id}][file_id={m.video.file_id}] '
                         f'Get file_path on server')
                file_path = await bot.get_file(m.video.file_id)
                log.info(f'[chat={m.chat.id}][user={m.from_user.id}][file_id={m.video.file_id}] '
                         f'Download video from telegram')
                downloaded_file = await bot.download_file(file_path.file_path)
                file_name = m.video.file_name \
                    if m.video.file_name \
                    else f'{m.video.file_unique_id}.{m.video.mime_type.split("/")[1]}'
                log.info(f'[chat={m.chat.id}][user={m.from_user.id}][file_id={m.video.file_id}] '
                         f'Download video from Telegram {file_name}')
                video_path = f'./video/{file_name}'
                log.info(f'[chat={m.chat.id}][user={m.from_user.id}][file_id={m.video.file_id}] '
                         f'Save video into SSD')
                with open(video_path, 'wb') as f:
                    f.write(downloaded_file)
                video_path_resized = await resize_video(m, video_path)
                log.info(f'[chat={m.chat.id}][user={m.from_user.id}][file_id={m.video.file_id}] '
                         f'Send resized video to Telegram')
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
            log.error(f'[chat={m.chat.id}][user={m.from_user.id}][file_id={m.video.file_id}] '
                      f'The maximum duration of the video must be: 59 seconds. Current={m.video.duration} seconds.')
            await bot.reply_to(
                message=m,
                text=f'The maximum duration of the video must be: 59 seconds. Current={m.video.duration} seconds.'
                     f'\n\n'
                     f'Error code: {m.video.file_id}'
            )


@bot.message_handler(func=check_tiktok_link_in_msg)
async def download_tiktok_video(m: telebot.types.Message):
    approved = await get_approve_status(m)
    if not approved:
        text = 'Sorry, this chat is not approved. Contact with @vladrunk to approved chat.'
        await bot.reply_to(m, text)
    else:
        log.info(f'[chat={m.chat.id}][user={m.from_user.id}][link={m.text}] '
                 f'Download request id={m.message_id}')
        m_reply = await bot.reply_to(
            message=m,
            text='Just a moment..',
        )
        log.info(f'[chat={m.chat.id}][user={m.from_user.id}][link={m.text}] '
                 f'Get video link')
        video_link = await tiktok.get_video(m)
        if video_link:
            log.info(f'[chat={m.chat.id}][user={m.from_user.id}][link={m.text}] '
                     f'Init send video')
            await bot.send_chat_action(chat_id=m.chat.id, action='upload_video')
            log.info(f'[chat={m.chat.id}][user={m.from_user.id}][link={m.text}] '
                     f'Load to telegram server')
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
                log.info(f'[chat={m.chat.id}][user={m.from_user.id}][link={m.text}] '
                         f'The send is successful id={m_video.message_id}')
                log.info(f'[chat={m.chat.id}][user={m.from_user.id}][link={m.text}] '
                         f'Delete requested message id={m.message_id}')
                await bot.delete_message(chat_id=m.chat.id, message_id=m.message_id)
        log.info(f'[chat={m.chat.id}][user={m.from_user.id}][link={m.text}] '
                 f'Delete reply message id={m_reply.message_id}')
        await bot.delete_message(chat_id=m_reply.chat.id, message_id=m_reply.message_id)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# Main
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
async def main():
    async with aiosqlite.connect('./db/gotey.db') as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS chats(
            chat_id INT PRIMARY KEY,
            approve INT,
            first_name TEXT,
            last_name TEXT,
            username TEXT,
            title TEXT,
            invite INT,
            approve_msg_id INT);''')
        await db.commit()
    log.warning(LOG_LAUNCH_MSG)
    # bot.set_update_listener(update_listener)
    await bot.polling()


if __name__ == '__main__':
    asyncio.run(main())
