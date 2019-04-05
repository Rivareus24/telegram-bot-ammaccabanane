import json
import logging
import os
import pickle
import sys
from datetime import timedelta
from threading import Event, Thread
from time import time

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import InputTextMessageContent, InlineQueryResultArticle, ChatAction
from telegram import KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler, CallbackQueryHandler

import util

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

JOBS_PICKLE = 'job_tuples.pickle'


def load_jobs(jq):
    now = time()

    with open(JOBS_PICKLE, 'rb') as fp:
        while True:
            try:
                next_t, job = pickle.load(fp)
            except EOFError:
                break  # Loaded all job tuples

            # Create threading primitives
            enabled = job._enabled
            removed = job._remove

            job._enabled = Event()
            job._remove = Event()

            if enabled:
                job._enabled.set()

            if removed:
                job._remove.set()

            next_t -= now  # Convert from absolute to relative time

            jq._put(job, next_t)


def save_jobs(jq):
    if jq:
        job_tuples = jq._queue.queue
    else:
        job_tuples = []

    with open(JOBS_PICKLE, 'wb') as fp:
        for next_t, job in job_tuples:
            # Back up objects
            _job_queue = job._job_queue
            _remove = job._remove
            _enabled = job._enabled

            # Replace un-pickleable threading primitives
            job._job_queue = None  # Will be reset in jq.put
            job._remove = job.removed  # Convert to boolean
            job._enabled = job.enabled  # Convert to boolean

            # Pickle the job
            pickle.dump((next_t, job), fp)

            # Restore objects
            job._job_queue = _job_queue
            job._remove = _remove
            job._enabled = _enabled


def save_jobs_job(context):
    save_jobs(context.job_queue)


# ma se lo metto dentro al metodo, cosa cambia?
@util.send_action(ChatAction.TYPING)
def start(update, context):

    # Prende i veri admin del bot
    if update.message.from_user.id in util.get_admin_ids(context.bot, update.message.chat_id):
        print("You are an admin")  # admin only

    location_keyboard = KeyboardButton(text="send_location", request_location=True)

    contact_keyboard = KeyboardButton(text="send_contact", request_contact=True)

    custom_keyboard = [[location_keyboard, contact_keyboard]]

    reply_markup = ReplyKeyboardMarkup(keyboard=custom_keyboard, resize_keyboard=True)

    update.message.reply_text(text="Would you mind sharing your location and contact with me?",
                              reply_markup=reply_markup)


def test(update, context):
    """Apre una keyboard inline per chiamare edit_text_method"""
    keyboard = [[InlineKeyboardButton(text='Change to A', callback_data='A'),
                 InlineKeyboardButton(text='Change to B', callback_data='B')]]

    context.bot.send_message(chat_id=update.message.chat_id,
                             text=f'You text me: {update.message.text}',
                             reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))


def edit_text_method(update, context):
    """Cambia il testo del messaggio sopra"""
    keyboard = [[InlineKeyboardButton(text='Change to A', callback_data='A'),
                 InlineKeyboardButton(text='Change to B', callback_data='B')]]

    context.bot.editMessageText(chat_id=update.effective_chat.id,
                                message_id=update.effective_message.message_id,
                                text=f"You clicked {update.callback_query.data}",
                                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))


def echo(update, context):
    update.message.reply_text(text=f"You wrote: [{update.message.text}]")


def caps(update, context):
    """Prende gli args e li restituisce in maiuscolo"""
    text_caps = ' '.join(context.args).upper()
    update.message.reply_text(text=text_caps)


def inline_caps(update, context):
    query = update.inline_query.query

    if not query:
        return

    # http

    results = list()

    articles = (
        InlineQueryResultArticle(
            id=1,
            title='Caps',
            input_message_content=InputTextMessageContent(query.upper())
        ),
        InlineQueryResultArticle(
            id=2,
            title='Lowers',
            input_message_content=InputTextMessageContent(query.lower())
        ),
        InlineQueryResultArticle(
            id=3,
            title='pippo',
            input_message_content=InputTextMessageContent(query.lower())
        )
    )
    results.extend(articles)

    context.bot.answer_inline_query(update.inline_query.id, results)


def unknown(update, context):
    """Funzione in util che ti crea una tastiera dinamicamente"""
    button_list = [
        InlineKeyboardButton("col1", callback_data=...),
        InlineKeyboardButton("col2", callback_data=...),
        InlineKeyboardButton("row 2", callback_data=...)
    ]
    reply_markup = InlineKeyboardMarkup(util.build_menu(button_list, n_cols=2))
    update.message.reply_text(text="Sorry, I didn't understand that command.")
    # reply_markup=reply_markup)


def main():
    with open('telegram.json', 'r') as f:
        datastore = json.load(f)

    ammaccabanane_token = datastore['ammaccabanane']

    updater = Updater(token=ammaccabanane_token, use_context=True)

    dispatcher = updater.dispatcher

    job_queue = updater.job_queue

    # Periodically save jobs
    job_queue.run_repeating(save_jobs_job, timedelta(minutes=1))

    try:
        load_jobs(job_queue)

    except FileNotFoundError:
        # First run
        pass

    dispatcher.add_handler(CommandHandler(command='start',
                                          callback=start))
    dispatcher.add_handler(CommandHandler(command='test',
                                          callback=test))

    dispatcher.add_handler(CallbackQueryHandler(callback=edit_text_method))

    dispatcher.add_handler(CommandHandler('caps', caps))

    dispatcher.add_handler(InlineQueryHandler(inline_caps))

    """questi due handler li mette nel main, ma non funzionano"""

    def stop_and_restart():
        """Gracefully stop the Updater and replace the current process with a new one"""
        updater.stop()
        os.execl(sys.executable, sys.executable, *sys.argv)

    def restart(update, context):
        update.message.reply_text('Bot is restarting...')
        Thread(target=stop_and_restart).start()

    dispatcher.add_handler(CommandHandler('r', restart, filters=Filters.user(username='@rivareus24')))

    dispatcher.add_handler(MessageHandler(Filters.text, echo))

    dispatcher.add_handler(MessageHandler(Filters.command, unknown))

    updater.start_polling()

    # make possible to stop the bot with Ctrl + c
    updater.idle()

    save_jobs(job_queue)


if __name__ == '__main__':
    main()

    """
    quando si aggiunge un command:
    pass_args aggiunge la possibilità di passare argomenti
    pass_args=True  -->   "/command arg1 arg2 ... argn"
    nella funzione basterà aggiungere un parametro args per riceverli
    e.g. f(bot, update, args)
    """
