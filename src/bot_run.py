import logging
import sys
import time
import spider
import telegram
from conf import config

# logging.addLevelName("info")
logging.basicConfig(level="INFO")

def to_str(li: list[str, str]):
    s = "标题: {}\n" \
        "组织: {}\n" \
        "可参与学院: {}\n" \
        "地址: {}\n" \
        "年级: {}\n" \
        "活动时间: {}\n" \
        "截止时间: {}\n" \
        "外勤打卡: {}\n".format(li["title"], li["organization"], li["activity_org"], li["address"],
                            li["grade"], li["activity_time"], li["limit_time"],
                            li["remote_check"], li["organization"])
    return s


chat_id = config.CHAT_ID
token = config.CHAT_TOKEN
bot = telegram.Bot(token=token)
dl = spider.get_activity()
start_time = time.localtime().tm_hour
while True:
    if time.localtime().tm_hour == start_time:
        result = spider.read(dl)
        if len(result) > 0:
            for send in result:
                # send = json.dumps(send, ensure_ascii=False)
                send = to_str(send)
                bot.send_message(chat_id=chat_id, text=send)
        print(2333)
        logging.info(f"finish at {time.localtime().tm_mday}")
    time.sleep(2400)
