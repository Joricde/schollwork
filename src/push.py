import conf.config
from telegram import Update, ForceReply, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from logger import logger
import spider
from conf import config
import re
import time


# Define a few command handlers. These usually take the two arguments update and
# context.

chat_id = config.CHAT_ID
token = config.BOT_TOKEN


def to_str(li):
    s = "标题: {}\n" \
        "组织: {}\n" \
        "可参与学院: {}\n" \
        "地址: {}\n" \
        "年级: {}\n" \
        "活动时间: {}\n" \
        "截止时间: {}\n" \
        "外勤打卡: {}\n".format(li["title"], li["organization"], li["activity_org"], li["address"],
                            li["grade"], li["activity_time"], li["limit_time"],
                            li["remote_check"])
    return s


def get_message():
    bot = Bot(token=token)
    start_time = 16
    # start_time = time.localtime().tm_hour
    while True:
        if time.localtime().tm_hour % 24 == start_time:
            dl = spider.get_activity()
            result = spider.read(dl)
            if len(result) > 0:
                for send in result:
                    # send = json.dumps(send, ensure_ascii=False)
                    send = to_str(send)
                    bot.send_message(chat_id=chat_id, text=send)
                    time.sleep(5)
            now_time = time.strftime("%Y-%m-%d %H:%M", time.localtime())
            logger.info(f"finish at {now_time}")
        else:
            logger.info(f"wait  Wait for next query , now time: {time.localtime().tm_hour}, query time: {start_time}")
        time.sleep(2400)


def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!',
        reply_markup=ForceReply(selective=True),
    )


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help...building')


def echo_reply(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    logger.info(update.message)
    reply = update.message.reply_to_message.text if update.message.reply_to_message is not None else []
    all_time = re.findall('[0-9]{4}-[0-9]{2}-[0-9]{4}:[0-6][0-9]', reply) if len(reply) > 0 else []
    if len(all_time) > 0:
        struct_t = time.strptime(all_time[0], "%Y-%m-%d%H:%M")
        start_time = time.mktime(struct_t)
        now_time = time.time()
        ms = "该签到了"
        logger.info(f"start_time, {start_time}, now_time:{time.time()}")
        # update.message.reply_text(text=ms, api_kwargs={"schedule_date": int(start_time)})
        while start_time > now_time:
            time.sleep(600)
            now_time = time.time()
        update.message.reply_text(text=ms)
    else:
        update.message.reply_text(text=update.message.text)


# def message_push(update: Update, context: CallbackContext) -> None:
#     result = push.get_message()
#     if len(result) > 0:
#         for send in result:
#             # send = json.dumps(send, ensure_ascii=False)
#             send = push.to_str(send)
#             time.sleep(5)
#             update.message.reply_text(text=send)


def bot_start() -> None:
    """Start the bot."""
    updater = Updater(token)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo_reply))
    updater.start_polling()
    get_message()
    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()
