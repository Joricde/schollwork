import copy

import requests
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import CallbackContext, ConversationHandler

from logger import logger


def get_specific_setu(update, data):
    results = []
    if data:
        for d in data:
            img_url = d["urls"]["regular"]
            pic = requests.get(img_url, stream=True).raw
            result_ = {'img': pic, 'pid': d['pid']}
            results.append(result_)
    if results:
        for result in results:
            pid = result['pid']
            a = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f'PID {pid}', url=f'https://www.pixiv.net/artworks/{pid}')]])
            update.message.bot.send_photo(
                photo=result['img'],
                chat_id=update.message.chat_id,
                reply_markup=a,
                disable_notification=True)
    else:
        update.message.bot.send_message(
            text="使用tag和keyword检索均未找到匹配图片，请重新调整tag/keyword",
            chat_id=update.message.chat_id,
            disable_notification=True)


def get_setu(keywords="", blur=False) -> list:
    url = r'https://api.lolicon.app/setu/v2'
    logger.info(f"keywords {keywords}, len:{len(keywords)})")
    keyword=keywords
    if not blur:
        keyword = keywords.split()
    tag_params = {
        'r18': 0,
        'tag': keyword,
        'size': "regular"
    }
    keywords_params = {
        'r18': 0,
        'keyword': keywords,
        'size': "regular"
    }
    try:
        if len(keyword) < 2:
            logger.info("search by keywords")
            resp = requests.get(url, params=keywords_params, timeout=10)
            data = resp.json()
        else:
            logger.info("search by tag")
            resp = requests.get(url, params=tag_params, timeout=10)
            data = resp.json()
        return data['data']
    except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout):
        logger.error(f'服务器响应超时, params={tag_params}')
        return []
    except Exception:
        logger.error(f'涩图信息请求失败, params={tag_params} Exception:{Exception}')
        return []


def setu(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /setu is issued."""
    user = update.effective_user
    logger.info("setu module running")
    bot_name = "@" + context.bot.get_me()["username"]
    bot_command = '/setu'
    logger.info(f"args: {context.args}")
    args = "".join(str(update.message.text).replace(bot_command, '').replace(bot_name, ''))
    data = get_setu(args)
    get_specific_setu(update, data)


def get_reply_markup(args) -> InlineKeyboardMarkup or None:
    data = get_setu(args) if args else get_setu()
    results = []
    if data:
        for d in data:
            tags = d["tags"]
            result_ = {'tags': tags}
            results.append(result_)
    if results:
        inline_buttons = []
        for result in results:
            tags = result['tags']
            count = 0
            inline_row = []
            for tag in tags:
                count += 1
                inline_row.append(
                    InlineKeyboardButton(text=f'{tag}', callback_data=str(tag)))
                if count % 3 == 0:
                    inline_buttons.append(copy.deepcopy(inline_row))
                    inline_row = []
        inline_buttons.append([InlineKeyboardButton(text=f'没有我想要的tag(随机', callback_data=f'#{args}')])
        keyboards = InlineKeyboardMarkup(inline_buttons)
        return keyboards
    return None


def setu_blur(update: Update, context: CallbackContext) -> int:
    logger.info("setu_by_words module running")
    bot_name = "@" + context.bot.get_me()["username"]
    bot_command = '/blur'
    args = "".join(str(update.message.text).replace(bot_command, '').replace(bot_name, ''))
    reply_markup = get_reply_markup(args)
    if reply_markup:
        update.message.bot.send_message(
            text='以下为模糊查找到的tag，请选择一个你认为匹配的标签',
            chat_id=update.message.chat_id,
            reply_markup=reply_markup,
            disable_notification=True)
    else:
        update.message.bot.send_message(
            text="使用tag和keyword检索均未找到匹配图片，请重新调整tag/keyword",
            chat_id=update.message.chat_id,
            disable_notification=True)
    return 1


def button(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    # logger.info(f"answer: {query.answer()}")
    # logger.info(f"id {query.message.chat_id}")
    tag = query.data
    if(tag.startswith("#")):
        reply_markup = get_reply_markup(tag.replace("#", ""))
        query.edit_message_reply_markup(reply_markup=reply_markup)
        return 1
    re = get_setu(tag.replace("#", "")[:tag.find("(")],blur=True)[0]
    data = re if re else None
    logger.info(f"query data{data}")
    if data:
        img_url = data["urls"]["regular"]
        pic = requests.get(img_url, stream=True).raw
        result = {'img': pic, 'pid': data['pid']}
        pid = data['pid']
        a = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f'PID {pid}', url=f'https://www.pixiv.net/artworks/{pid}')]])
        query.message.bot.send_photo(
            photo=pic,
            chat_id=query.message.chat_id,
            reply_markup=a,
            disable_notification=True
        )
        # get_specific_setu(update, data)
        query.delete_message()
    else:
        query.edit_message_text('not found!')
        return 0
    return 2


def end(update: Update, context: CallbackContext) -> int:
    """Returns `ConversationHandler.END`, which tells the
    ConversationHandler that the conversation is over.
    """
    query = update.callback_query
    query.answer()
    query.edit_message_text(text="See you next time!")
    return ConversationHandler.END
