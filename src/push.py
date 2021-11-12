import datetime
import re
import time

import pytz
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler, \
    ConversationHandler

import message
import setu
from conf import config
from logger import logger

# Define a few command handlers. These usually take the two arguments update and
# context.

chat_id = config.CHAT_ID
token = config.BOT_TOKEN


def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    logger.info("start running")
    context.job_queue.run_daily(message.get_message,
                                datetime.time(hour=12, minute=6, tzinfo=pytz.timezone('Asia/Shanghai')),
                                days=(0, 1, 2, 3, 4, 5, 6), context=update.message.chat_id)
    logger.info(f"message_push_running")
    update.message.bot.send_message(
        text=f'Hi {update.effective_user.name}!'
        f'message push module is running!',
        chat_id=update.message.chat_id
    )


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    logger.info("help running")
    update.message.bot.send_message(
        text='Help...building\n'
             'use /check to query now\n'
             'use /setu  to get setu',
        chat_id=update.message.chat_id,
        disable_notification=True)


# def echo_reply(update: Update, context: CallbackContext) -> None:
#     """Echo the user message."""
#     logger.info("echo_reply running")
#     reply = update.message.reply_to_message.text if update.message.reply_to_message is not None else []
#     all_time = re.findall('[0-9]{4}-[0-9]{2}-[0-9]{4}:[0-6][0-9]', reply) if len(reply) > 0 else []
#     if len(all_time) > 0:
#         struct_t = time.strptime(all_time[0], "%Y-%m-%d%H:%M")
#         start_time = time.mktime(struct_t)
#         now_time = time.time()
#         ms = "该签到了"
#         logger.info(f"start_time, {start_time}, now_time:{time.time()}")
#         # update.message.reply_text(text=ms, api_kwargs={"schedule_date": int(start_time)})
#         while start_time > now_time:
#             time.sleep(600)
#             now_time = time.time()
#         update.message.bot.send_message(text=ms,chat_id=update.message.chat_id)
#     else:
#         update.message.reply_text(text=f"复读机测试-您输入的内容为 '{update.message.text}'")


def bot_start() -> None:
    """Start the bot."""
    updater = Updater(token)
    dispatcher = updater.dispatcher
    logger.info(f"start- get_me: {updater.bot.get_me()}")
    updater.bot.send_message(chat_id=chat_id, text="please use /start to init the bot")
    dispatcher.add_handler(CommandHandler("start", start, pass_job_queue=True))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("check", message.check))
    dispatcher.add_handler(CommandHandler("setu", setu.setu))
    # dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo_reply))
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('blur', setu.setu_blur)],
        states={
            1: [
                CallbackQueryHandler(setu.button)
            ],
            2: [
                CallbackQueryHandler(setu.end)
            ]
        },
        fallbacks=[CommandHandler('blur', setu.setu_blur)],
    )
    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()
