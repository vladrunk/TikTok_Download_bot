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
from config import BOT_TOKEN, ALLOWED_TIKTOK_LINKS, BOT_SERVICE_CHAT_ID, BOT_SERVICE_CHAT_THREAD_ID, \
    TABLE, PATH_DB, DB_FULLPATH, PATH_VIDEO, ADMIN_TG_ID, ARCHIVE_TG_ID
from strings import MSG_LOG_LAUNCH, MSG_SERVICE_NEW_CHAT, MSG_SERVICE_NEW_GROUP, KBRD_DECLINE, KBRD_DECLINE_CALL, \
    KBRD_APPROVE_CALL, KBRD_APPROVE, MSG_CAPTION_VIDEO, MSG_CHAT_NEW, MSG_CHAT_OLD, MSG_CONTACT_ADMIN

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
def exist_path(path: str):
    db = Path(path)
    if db.exists():
        return True
    else:
        return False


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
    return any([m.text.startswith(link) for link in ALLOWED_TIKTOK_LINKS]) and \
        len(m.text.split()) < 2 and \
        m.chat.id != BOT_SERVICE_CHAT_ID


async def get_chat_info(m: telebot.types.Message = None, chat_id: int = None):
    chat_id, from_user_id = (m.chat.id, m.from_user.id) \
        if m else (chat_id, chat_id) \
        if chat_id else (ADMIN_TG_ID, ADMIN_TG_ID)

    log.info(f'[chat={chat_id}][user={from_user_id}] '
             f'Get chat info from DB')

    async with aiosqlite.connect('./db/gotey.db') as db:
        async with db.execute("SELECT * FROM chats WHERE chat_id=?;", (chat_id,)) as cursor:
            chat_info = await cursor.fetchone()
    return chat_info


async def create_chat(m: telebot.types.Message):
    log.info(f'[chat={m.chat.id}][user={m.from_user.id}] '
             f'Add chat into DB')
    async with aiosqlite.connect('./db/gotey.db') as db:
        await db.execute(
            "INSERT INTO chats VALUES(?, ?, ?, ?, ?, ?, ?, ?);",
            (
                m.chat.id,  # chat_id
                0,  # approve
                m.chat.first_name,  # first_name
                m.chat.last_name,  # last_name
                m.chat.username,  # username
                m.chat.title,  # title
                m.from_user.id if m.content_type == 'new_chat_members' else m.text.split()[-1]
                if len(m.text.split()) > 1 and m.text.split()[-1].lstrip('-').isdigit() else 0,  # invite
                0,  # approve_msg_id
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


async def get_id_from_msg_text(text: str) -> int:
    return int(text.split('ID:')[-1].split('\n')[0].replace('#id', ''))


async def change_approve_status(call):
    log.info(f'[chat={call.message.chat.id}][user={call.message.from_user.id}] '
             f'Change approve status to "{call.data}"')
    async with aiosqlite.connect('./db/gotey.db') as db:
        await db.execute(
            "UPDATE chats SET approve = ? WHERE chat_id = ?;",
            (
                1 if call.data == KBRD_APPROVE_CALL else 0,
                await get_id_from_msg_text(call.message.text),
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
    chat_info = await get_chat_info(m=m)
    if chat_info:
        return False, chat_info
    else:
        await create_chat(m)
        return True, await get_chat_info(m=m)


async def send_welcome_message(m: telebot.types.Message) -> tuple:
    is_new, chat = await is_new_chat(m)
    if is_new:
        await bot.send_message(
            chat_id=m.chat.id,
            text=MSG_CHAT_NEW,
        )
    else:
        await bot.send_message(
            chat_id=m.chat.id,
            text=MSG_CHAT_OLD.format(
                active={"" if chat[TABLE["approve"]] else "not "},
                approve={"" if chat[TABLE["approve"]] else MSG_CONTACT_ADMIN}
            ),
        )
    return chat


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

    id_who_is_approved = await get_id_from_msg_text(call.message.text)
    chat_who_is_approved = await get_chat_info(chat_id=id_who_is_approved)
    await bot.send_message(
        chat_id=chat_who_is_approved[TABLE["chat_id"]],
        text=f'Your chat is *{KBRD_APPROVE if call.data == KBRD_APPROVE_CALL else KBRD_DECLINE}d*',
        parse_mode='Markdown'
    )


@bot.message_handler(commands=['start'], chat_types=['private'])
async def cmd_start(m: telebot.types.Message):
    log.info(f'[chat={m.chat.id}][user={m.from_user.id}] '
             f'User send /start')
    chat = await send_welcome_message(m)
    if not chat[TABLE['approve_msg_id']]:
        log.info(f'[chat={m.chat.id}][user={m.from_user.id}] '
                 f'Send approve message')
        approve_msg = await bot.send_message(
            chat_id=BOT_SERVICE_CHAT_ID,
            message_thread_id=BOT_SERVICE_CHAT_THREAD_ID,
            text=MSG_SERVICE_NEW_CHAT.format(
                first_name=m.chat.first_name,
                last_name=m.chat.last_name if m.chat.last_name else '',
                username=m.chat.username if m.chat.username else '',
                user_id=m.chat.id,
                invite=chat[TABLE["invite"]],
            ),
            parse_mode='HTML',
            reply_markup=markup_approve(),
            disable_web_page_preview=True,
        )
        await save_approve_msg_id(m, approve_msg)


@bot.message_handler(content_types=['new_chat_members'], func=lambda m: m.chat.id != BOT_SERVICE_CHAT_ID)
async def ct_new_chat_members(m: telebot.types.Message):
    log.info(f'[chat={m.chat.id}][user={m.from_user.id}] '
             f'Add bot to new group')
    chat = await send_welcome_message(m)
    user = await get_chat_info(chat_id=chat[TABLE["invite"]])
    if not chat[TABLE['approve_msg_id']]:
        log.info(f'[chat={m.chat.id}][user={m.from_user.id}] '
                 f'Send approve message')
        approve_msg = await bot.send_message(
            chat_id=BOT_SERVICE_CHAT_ID,
            message_thread_id=BOT_SERVICE_CHAT_THREAD_ID,
            text=MSG_SERVICE_NEW_GROUP.format(
                first_name=m.from_user.first_name,
                last_name=m.from_user.last_name if m.from_user.last_name else '',
                username=m.from_user.username if m.from_user.username else '',
                user_id=m.from_user.id,
                invite=user[TABLE["invite"]],
                title=m.chat.title,
                chat_id=m.chat.id,
            ),
            parse_mode='HTML',
            reply_markup=markup_approve(),
            disable_web_page_preview=True,
        )
        await save_approve_msg_id(m, approve_msg)


@bot.message_handler(content_types=['video'], func=lambda m: m.chat.id == ADMIN_TG_ID)
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
                video_path = f'{PATH_VIDEO}{file_name}'
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
                message_thread_id=m.message_thread_id,
                video=video_link,
                caption=MSG_CAPTION_VIDEO.format(
                    text=m.text,
                    username=m_reply.from_user.username,
                    invite=m.from_user.id,
                ),
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

                await bot.send_video(
                    chat_id=ARCHIVE_TG_ID,
                    video=m_video.video.file_id,
                    caption=MSG_CAPTION_VIDEO.format(
                        text=m.text,
                        username=m_reply.from_user.username,
                        invite=m.from_user.id,
                    ),
                    supports_streaming=True,
                    disable_notification=True,
                    parse_mode='HTML',
                )

        log.info(f'[chat={m.chat.id}][user={m.from_user.id}][link={m.text}] '
                 f'Delete reply message id={m_reply.message_id}')
        await bot.delete_message(chat_id=m_reply.chat.id, message_id=m_reply.message_id)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# Main
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
async def main():
    if not exist_path(PATH_DB):
        Path(PATH_DB).mkdir(parents=True, exist_ok=True)
    if not exist_path(PATH_VIDEO):
        Path(PATH_DB).mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(DB_FULLPATH) as db:
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
    log.warning(MSG_LOG_LAUNCH)

    # bot.set_update_listener(update_listener)
    await bot.polling()


if __name__ == '__main__':
    asyncio.run(main())
