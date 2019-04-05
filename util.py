import json
from functools import wraps

from telegram import KeyboardButton, ParseMode

from mwt import MWT

with open('telegram.json', 'r') as f:
    store = json.load(f)

LIST_OF_ADMINS = store['users_id']


@MWT(timeout=60 * 60)
def get_admin_ids(bot, chat_id):
    """Returns a list of admin IDs for a given chat. Results are cached for 1 hour."""
    return [admin.user.id for admin in bot.get_chat_administrators(chat_id)]


def restricted(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in LIST_OF_ADMINS:
            print(f"Unauthorized access denied for {user_id}.")
            return
        return func(update, context, *args, **kwargs)

    return wrapped


OFFSET = 127462 - ord('A')


def flag(code):
    """Return the flag (emoticon) of the country"""
    code = code.upper()
    return chr(ord(code[0]) + OFFSET) + chr(ord(code[1]) + OFFSET)


def get_data_buttons():
    """It gets an Inline Menu buttons"""
    some_strings = ["col1", "col2", "row2"]
    return [[KeyboardButton(s)] for s in some_strings]


def build_menu(buttons,
               n_cols,
               header_buttons=None,
               footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


def send_action(action):
    """Sends `action` while processing func command."""

    def decorator(func):
        @wraps(func)
        def command_func(update, context, *args, **kwargs):
            context.bot.send_chat_action(chat_id=update.effective_message.chat_id,
                                         action=action)

            return func(update, context, *args, **kwargs)

        return command_func

    return decorator


def send_stuff(update, context):
    chat_id = update.message.chat_id

    update.message.reply_text(text="*bold* _italic_ `fixed width font` [link](http://google.com).",
                              parse_mode=ParseMode.MARKDOWN)

    update.message.reply_text(text='<b>bold</b> <i>italic</i> <a href="http://google.com">link</a>.',
                              parse_mode=ParseMode.HTML)

    context.bot.send_photo(chat_id=chat_id, photo=open('tests/test.png', 'rb'))

    context.bot.send_voice(chat_id=chat_id, voice=open('tests/telegram.ogg', 'rb'))

    context.bot.send_audio(chat_id=chat_id, audio=open('tests/test.mp3', 'rb'))

    context.bot.send_document(chat_id=chat_id, document=open('tests/test.zip', 'rb'))
