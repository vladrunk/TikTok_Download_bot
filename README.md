1. Create a Telegram bot using [@BotFather](https://botfather.t.me/) and obtain the token.
2. Create `.env` file near `bot.py` file.
3. Insert the Token into the `.env` file.
4. Insert the ID of the channel where the bot will store the videos into the `.env` file.
5. Contents of the file `.env`:
    ```ini
   BOT_TOKEN=8421803249:FFHyXOZLs45BKxu_JlJiQhVcqPw2vlBlgvV
   ARCHIVE_TG_ID=@archive_chanel_for_bot
   ```
   
6. Create a venv: 
   ```shell
   python -m venv .venv
   ```
   
7. Activate the venv:  
   ```shell
   . ./venv/bin/activate
   ```
   
8. Install pip requirements: 
   ```shell
   pip install -r requirements.txt
   ```
   
9. Run the bot:
   ```shell
   python bot.py
   ```