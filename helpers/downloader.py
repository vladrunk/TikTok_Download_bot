from pathlib import Path
import yt_dlp


class Downloader:
    def __init__(self, logger, save_path: Path):
        self.log = logger
        self.save_path = save_path
        self.ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': str(self.save_path / '%(id)s.%(ext)s'),
        }
        self.create_save_directory()

    def create_save_directory(self):
        self.log.debug(f'Prepare dir for video: {self.save_path}')
        self.save_path.mkdir(parents=True, exist_ok=True)

    async def __download_video(self, url) -> Path | None:
        self.log.debug(f'{url = }')
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                self.log.debug(f'{info = }')
                ydl.download([url])
                video_path = self.save_path / f'{info["id"]}.{info["ext"]}'
                return video_path
            except Exception as e:
                self.log.error(f"An error occurred while downloading the media: {str(e)}")
                return None

    async def download(self, url: str) -> Path | None:
        self.log.debug(f'{url = }')
        try:
            video_path = await self.__download_video(url)
            self.log.debug(f'{video_path = }')
            if video_path:
                return video_path
            else:
                self.log.error(f'Failed to download the video: {video_path = }')
                return None
        except Exception as e:
            self.log.error(f"An error occurred while download video: {str(e)}")
            return None
