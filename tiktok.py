import aiohttp
import telebot

from config import API_LINK


class TikTok:

    def __init__(self, logger):
        self.log = logger

    @staticmethod
    async def __fetch(s, url) -> dict:
        async with s.get(url) as r:
            return await r.json()

    async def get_video(self, m: telebot.types.Message) -> str | None:
        async with aiohttp.ClientSession() as session:
            self.log.info(
                f'[chat={m.chat.id}][user={m.from_user.id}][link={m.text}] '
                f'Send request to API'
            )
            json = await self.__fetch(session, API_LINK.format(link=m.text))
            self.log.info(
                f'[chat={m.chat.id}][user={m.from_user.id}][link={m.text}] '
                f'Status {json["status"]}'
            )
            if json["status"] == 'success':
                self.log.info(
                    f'[chat={m.chat.id}][user={m.from_user.id}][link={m.text}] '
                    f'Response {json["nwm_video_url_HQ"]}'
                )
                return json['nwm_video_url_HQ']
            else:
                self.log.error(
                    f'[chat={m.chat.id}][user={m.from_user.id}][link={m.text}] '
                    f'Error while getting download link from tiktok API'
                )
                return None
