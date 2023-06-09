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

    async def __download_video(self, url) -> Path | None:
        self.log.debug(f'Download video by {url = }')
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                self.log.debug(f'Video {info = }')
                video_id = info['id']
                ydl.download([url])
                video_path = self.save_path / f'{video_id}.mp4'
                return video_path
            except Exception as e:
                self.log.error(f"An error occurred while downloading the video: {str(e)}")
                return None

    async def download(self, m: telebot.types.Message) -> Path | None:
        self.log.debug(f'Process message = {str(m)}')
        try:
            video_url = m.text
            self.log.debug(f'{video_url = }')
            if not video_url:
                return None

            video_path = await self.__download_video(video_url)
            if video_path:
                self.log.info(f'Video downloaded successfully = {video_path}')
                return video_path
            else:
                self.log.error(f'Failed to download the video = {video_path}')
                return None
        except Exception as e:
            self.log.error(f"An error occurred while processing the message: {str(e)}")
            return None
