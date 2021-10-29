import datetime
import pytz
import requests

import conf.config
from telegram import Update, ForceReply
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


def get_message(context) -> None:
    global chat_id
    start_time = 16
    logger.info("get_message running")
    # start_time = time.localtime().tm_hour
    # while True:
    #     if time.localtime().tm_hour % 24 == start_time:
    try:
        dl = spider.get_activity()
    except Exception:
        context.bot.send_message(chat_id=context.job.context, text=str(Exception))
        raise Exception
    result = spider.read_needs(dl)
    if len(result) > 0:
        for send in result:
            # send = json.dumps(send, ensure_ascii=False)
            send = to_str(send)
            context.bot.send_message(chat_id=context.job.context, text=send)
            time.sleep(3)
    else:
        ms = f"There are no activities that meet the query criteria \n" \
             f"Wait for next query \n" \
             f"now time: {time.localtime().tm_hour}, query time: {start_time}"
        logger.info(ms)
        context.bot.send_message(chat_id=context.job.context, text=ms)
    now_time = time.strftime("%Y-%m-%d %H:%M", time.localtime())
    logger.info(f"finish at {now_time}")


def setu(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /setu is issued."""
    user = update.effective_user

    def get_setu(keywords=""):
        url = r'https://api.lolicon.app/setu/v2'
        logger.info(f"keywords {keywords}, len:{len(keywords)})")
        if len(keywords) > 0:
            keyword = keywords.split()
            params = {
                'r18': 0,
                'tag': keyword,
                'size': "regular"
            }
        else:
            params = {
                'r18': 0,
                'size': "regular"
            }
        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            if data["data"]:
                data = data['data'][0]["urls"]["regular"]
                img = requests.get(data, stream=True).raw
                return img
            else:
                return False
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout):
            logger.error(f'服务器响应超时, params={params}')
            return "服务器响应超时"
        except Exception:
            logger.error(f'涩图信息请求失败, params={params} Exception:{Exception}')

    logger.info(context.bot.get_me())
    bot_name = "@" + context.bot.get_me()["username"]
    bot_command = '/setu'
    logger.info(f"args: {context.args}")
    args = "".join(str(update.message.text).replace(bot_command, '').replace(bot_name, ''))
    logger.info(args)
    logger.info(update.message)
    img = get_setu(args)
    if img:
        update.message.bot.send_photo(
            photo=img,
            chat_id=update.message.chat_id,
            disable_notification=True)
    else:
        update.message.bot.send_message(
            text="未找到匹配图片，请调整tag",
            chat_id=update.message.chat_id,
            disable_notification=True)


def check(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /check is issued."""
    logger.info(update.message.chat_id)
    update.message.bot.send_message(
        text=rf'checking, please wait a few minutes...',
        chat_id=update.message.chat_id
    )

    try:
        dl = spider.get_activity()
    except Exception:
        update.message.bot.send_message(
            text=str(Exception),
            chat_id=update.message.chat_id,
        )
        raise Exception
    result = spider.read_needs(dl)
    if len(result) > 0:
        for send in result:
            send = to_str(send)
            try:
                update.message.bot.send_message(
                    text=rf"{send}",
                    chat_id=update.message.chat_id,
                )
            except Exception:
                update.message.bot.send_message(
                    text=str(Exception),
                    chat_id=update.message.chat_id,
                )
                raise Exception
            time.sleep(2)
    else:
        ms = f"There are no activities that meet the query criteria now\n" \
             f"Wait for some time \n"
        try:
            update.message.bot.send_message(text=ms,
                                            chat_id=update.message.chat_id
                                            )
        except Exception:
            update.message.bot.send_message(
                text=str(Exception),
                chat_id=update.message.chat_id
            )
            raise Exception
    now_time = time.strftime("%Y-%m-%d %H:%M", time.localtime())
    logger.info(f"check finish at {now_time}")


def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    logger.info("message_push_running")
    context.job_queue.run_daily(get_message,
                                datetime.time(hour=16, minute=8, tzinfo=pytz.timezone('Asia/Shanghai')),
                                days=(0, 1, 2, 3, 4, 5, 6), context=update.message.chat_id)
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!'
        fr'message_push_running\!',
        reply_markup=ForceReply(selective=True),
    )


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help...building\n'
                              'use /check to query now\n'
                              'use /setu  to get setu'
                              )


def echo_reply(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    # logger.info(update.message)
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


def bot_start() -> None:
    """Start the bot."""
    updater = Updater(token)
    dispatcher = updater.dispatcher
    logger.info(updater.bot.get_me())
    updater.bot.send_message(chat_id=chat_id, text="please use /start to init the bot")
    dispatcher.add_handler(CommandHandler("start", start, pass_job_queue=True))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("check", check))
    dispatcher.add_handler(CommandHandler("setu", setu))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo_reply))

    updater.start_polling()
    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()
