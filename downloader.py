from pathlib import Path
import telebot
import yt_dlp


class Downloader:
    def __init__(self, logger, save_path: str):
        self.log = logger
        self.save_path = Path(save_path)
        self.ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': str(self.save_path / '%(id)s.%(ext)s'),
        }
        self.__create_save_directory()

    def __create_save_directory(self):
        self.log.debug(f'Make dir if not exist = {self.save_path}')
        self.save_path.mkdir(parents=True, exist_ok=True)

    async def __download_media(self, url) -> Path | None:
        self.log.debug(f'Download media by {url = }')
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                self.log.debug(f'Media {info = }')
                ydl.download([url])
                media_path = self.save_path / f'{info["id"]}.{info["ext"]}'
                return media_path
            except Exception as e:
                self.log.error(f"An error occurred while downloading the media: {str(e)}")
                return None

    async def download(self, m: telebot.types.Message) -> Path | None:
        self.log.debug(f'Process message = {str(m)}')
        try:
            media_url = m.text
            self.log.debug(f'{media_url = }')
            if not media_url:
                return None

            media_path = await self.__download_media(media_url)
            if media_path:
                self.log.info(f'Media downloaded successfully = {media_path}')
                return media_path
            else:
                self.log.error(f'Failed to download the media = {media_path}')
                return None
        except Exception as e:
            self.log.error(f"An error occurred while processing the message: {str(e)}")
            return None
