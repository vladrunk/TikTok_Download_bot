ADMIN_NICKNAME = 'vladrunk'


'''                       Keyboards and buttons                              '''
# Btn text to Approve
KBRD_APPROVE = u"\U0001F7E2 Approve"
# Callback for Approve Btn
KBRD_APPROVE_CALL = "approve"

# Btn text to Decline
KBRD_DECLINE = u"\U0001F534 Decline"
# Callback for Decline Btn
KBRD_DECLINE_CALL = "decline"


'''                       Messages                              '''
# Message for new user
MSG_SERVICE_NEW_CHAT = '''<b>Fullname:</b> <code>{first_name} {last_name}</code>
<b>Username:</b> <a href="https://t.me/{username}">{username}</a>
<b>ID:</b> #id{user_id}
<b>Invited by:</b> #id{invite}'''

# Message for new group
MSG_SERVICE_NEW_GROUP = '''<b>Fullname:</b> <code>{first_name} {last_name}</code>
<b>Username:</b> <a href="https://t.me/{username}">{username}</a>
<b>ID:</b> #id{user_id}
<b>Invited by:</b> #id{invite}

Wanna add bot to chat:
<b>Title:</b> <code>{title}</code>
<b>ID:</b> <code>{chat_id}</code>'''

MSG_LOG_LAUNCH = '''LAUNCH BOT'''

MSG_CAPTION_VIDEO = '<i><a href="{text}">video.link</a></i>' \
                    '<b> | </b>' \
                    '<i><a href="https://t.me/{username}?start={invite}">bot</a></i>'

MSG_CHAT_NEW = f'''Hello.
To download a video from TikTok, just send a link to the video in this chat. Bot is not active for you. 
            
To activate it, text him @{ADMIN_NICKNAME}.'''

MSG_CHAT_OLD = 'Ah! Here We Go Again...\n' \
               'To download a video from TikTok, just send a link to the video in this chat. Bot is {active}active ' \
               'for you.\n' \
               '{approve}'

MSG_CONTACT_ADMIN = f'To activate it, text him @{ADMIN_NICKNAME}.'

MSG_REPLY_ON_LINK = 'Downloading...'

MSG_ASK_CONTACT_ADMIN = f'Sorry, this chat is not approved. Contact with @{ADMIN_NICKNAME} to approved chat.'
