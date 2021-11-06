import time

from telegram import Update
from telegram.ext import CallbackContext

from src import spider
from src.logger import logger


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
    start_time = 12
    logger.info("get_message running")
    try:
        dl = spider.get_activity()
    except Exception:
        context.bot.send_message(chat_id=context.job.context, text=str(Exception))
        raise Exception
    result = spider.read_needs(dl)
    if len(result) > 0:
        for send in result:
            send = to_str(send)
            context.bot.send_message(chat_id=context.job.context, text=send)
            time.sleep(3)
    else:
        ms = f"There are no activities that meet the query criteria \n" \
             f"Wait for next query \n" \
             f"now time: {time.localtime().tm_hour}, query cycle: {start_time}"
        logger.info(ms)
        context.bot.send_message(chat_id=context.job.context, text=ms)
    now_time = time.strftime("%Y-%m-%d %H:%M", time.localtime())
    logger.info(f"finish at {now_time}")


def check(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /check is issued."""
    logger.info(f"checking...command from {update.message.chat_id}")
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
