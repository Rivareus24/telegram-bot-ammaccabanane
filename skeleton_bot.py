import logging
from functools import wraps

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ParseMode, \
    ReplyKeyboardRemove
from telegram.ext import Filters
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


# @restricted
def start_inline(bot, update):
    keyboard = [[InlineKeyboardButton(text='Red pill', callback_data='red'),
                 InlineKeyboardButton(text='Blue pill', callback_data='blue')]]

    update.message.reply_text(text="Choose carefully...",
                              reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))


def start_reply(bot, update):
    keyboard = [[KeyboardButton(text='Start')]]

    update.message.reply_text(text="I'm a bot, please talk to me mothafucka!",
                              reply_markup=ReplyKeyboardMarkup(keyboard=keyboard,
                                                               resize_keyboard=True))


def callback_method_pattern(bot, update):
    data = update.callback_query.data

    reply_markup = ReplyKeyboardRemove()

    update.message.reply_text(text=
                              f"You chose the {data} pill!\n\n"
                              f"*BOLD*\n"
                              f"_ITALIC_\n"
                              f"- - - - - - -"
                              f"```ciao\n"
                              f"Pre\n"
                              f" Pre\n"
                              f"  Pre\n"
                              f"   Pre\n"
                              f"\t\t\t\t\t\t\tPRE"
                              f"```",
                              parse_mode=ParseMode.MARKDOWN,
                              reply_markup=reply_markup)


def callback_method(bot, update):
    data = update.callback_query.data
    text = f"0) Selected option: {data}"

    callback_id = update.callback_query.id

    if data == 'red' or data == 'blue':
        bot.answerCallbackQuery(callback_query_id=callback_id,
                                text=text)
    elif data == 'A' or data == 'B':
        bot.editMessageText(chat_id=update.message.chat_id,
                            message_id=update.message.message_id,
                            text=data)
    else:
        bot.answerCallbackQuery(callback_query_id=callback_id,
                                text="fuck off")


def echo(bot, update):
    keyboard = [[InlineKeyboardButton(text='Change to A', callback_data='A'),
                 InlineKeyboardButton(text='Change to B', callback_data='B')]]

    bot.send_message(chat_id=update.message.chat_id,
                     text=f'You text me: {update.message.text}',
                     reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))


def main():
    updater = Updater(token='',
                      use_context=True)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler(command='start_inline',
                                          callback=start_inline))

    dispatcher.add_handler(CommandHandler(command='start_reply',
                                          callback=start_reply))

    dispatcher.add_handler(CallbackQueryHandler(callback=callback_method_pattern,
                                                pattern='opt'))

    dispatcher.add_handler(CallbackQueryHandler(callback=callback_method))

    # listener on every message sent
    dispatcher.add_handler(MessageHandler(Filters.text, echo))

    # listener on unknown commands (MUST BE ADDED LAST)
    unknown_handler = MessageHandler(Filters.command, unknown_method)
    dispatcher.add_handler(unknown_handler)

    # when we buy a raspberry this line will go away
    updater.start_polling()

    # make possible to stop the bot with Ctrl + c
    updater.idle()


LIST_OF_ADMINS = [12345678, 87654321]


def restricted(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in LIST_OF_ADMINS:
            print("Unauthorized access denied for {}.".format(user_id))
            return
        return func(update, context, *args, **kwargs)

    return wrapped


if __name__ == '__main__':
    main()

    """
    quando si aggiunge un command:
    pass_args aggiunge la possibilità di passare argomenti
    pass_args=True  -->   "/command arg1 arg2 ... argn"
    nella funzione basterà aggiungere un parametro args per riceverli
    e.g. f(bot, update, args)
    """


