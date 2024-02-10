1. Создайте Telegram-бота, используя [@BotFather](https://botfather.t.me/), и получите токен.
2. Создайте файл `.env` рядом с файлом `bot.py`.
3. Вставьте токен в файл `.env`.
4. Вставьте ID канала, в котором бот будет хранить видео, в файл `.env`.
5. Содержимое файла `.env`:
    ```ini
   BOT_TOKEN=8421803249:FFHyXOZLs45BKxu_JlJiQhVcqPw2vlBlgvV
   ARCHIVE_TG_ID=@archive_chanel_for_bot
   ```
   
6. Создайте виртуальное окружение (venv):
   ```shell
   python -m venv .venv
   ```
   
7. Активируйте виртуальное окружение:
   ```shell
   . ./venv/bin/activate
   ```
   
8. Установите зависимости pip:
   ```shell
   pip install -r requirements.txt
   ```
   
9. Запустите бота:
   ```shell
   python bot.py
   ```