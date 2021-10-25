import json
import logging

import requests
from bs4 import BeautifulSoup as bs
from pymysql import connect
from conf import config

db_table = "pu_activity"
sql_sentence = f"""
    create table if not exists {db_table}(
    id int auto_increment,
    title varchar(512),
    title_id int, 
    title_uid int,
    constraint {db_table}_pk
    primary key (id)
    );
"""

try:
    db = connect(host=config.SQL_DATA["host"],
                 password=config.SQL_DATA["password"],
                 user=config.SQL_DATA["user"],
                 database=config.SQL_DATA["database"],
                 charset=config.SQL_DATA["charset"])
    cursor = db.cursor()
    cursor.execute(sql_sentence)
    db.commit()
except Exception:
    logging.error(Exception)
    raise Exception


def get_activity():
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36 Edg/95.0.1020.30",
        "Origin": "https://ncu.pocketuni.net",
        "Pragma": "no-cache",
    }
    requests.get("https://ncu.pocketuni.net/index.php?app=home&mod=Index&act=index")
    login_content = requests.post(url="https://ncu.pocketuni.net/index.php?app=home&mod=Public&act=doLogin",
                                  allow_redirects=False,
                                  headers=header,
                                  data=config.SCHOOL
                                  )
    cookie = login_content.cookies
    end_spider = False
    query_data = get_last_record()
    if query_data is not None:
        query_title_id, query_title_uid = query_data[0], query_data[1]
    else:
        query_title_id, query_title_uid = 0, 0
    stack = []
    data_list = []
    title_dict = {}
    for num in range(1, 5):
        r1 = requests.get(f"https://ncu.pocketuni.net/index.php?app=event&mod=School&act=board&cat=all&p={num}",
                          headers=header, cookies=cookie)
        data1 = bs(r1.text, 'html.parser')
        urls = data1.find_all(class_="hd_c_left_title b")

        for url in urls:
            title_id = int(str(url.a["href"]).split("&")[3].split("=")[1])
            title_uid = int(str(url.a["href"]).split("&")[4].split("=")[1])
            title = "".join(str(url.text).split()).strip()
            title_dict = {"title": title, "title_id": title_id, "title_uid": title_uid}
            if title_id == query_title_id and title_uid == query_title_uid:
                end_spider = True
                break
            else:
                stack.append(title_dict)
            r2 = requests.get(url.a["href"], headers=header, cookies=cookie)
            data2 = bs(r2.text, 'html.parser')
            content = data2.find(class_="content_hd_c")
            address = content.find("a")["title"]
            d = {"title": title,
                 "organization": "".join(str(content.contents[2]).split()).strip(),
                 "activity_org": "".join(str(content.contents[2]).split()).strip(),
                 "address": address,
                 "grade": "".join(str(content.contents[18]).split()).strip(),
                 "activity_time": "".join(str(content.contents[22]).split()).strip(),
                 "limit_time": "".join(str(content.contents[26]).split()).strip(),
                 "remote_check": "".join(str(content.contents[30]).split()).strip()
                 }
            data_list.append(d)
            # with open("d.log", "a+") as f:
            #     f.write(json.dumps(d, ensure_ascii=False))
            #     f.write("\n")
        if end_spider:
            break

    if len(stack) > 0:
        for num2 in range(0, len(stack)):
            title_record = stack[len(stack) - num2 - 1]
            update_record(title_record)
    db.commit()
    return data_list


def get_last_record():
    cursor.execute("""select pu_activity.title_id, pu_activity.title_uid from 
    blockchaindata.pu_activity order by id desc limit 1""")
    try:
        result = cursor.fetchone()
    except Exception:
        raise Exception
    return result


def update_record(title_record):
    query = f"""
        insert into {db_table}(title, title_id, title_uid) values (%s,%s,%s)
    """
    values = (title_record["title"], title_record["title_id"], title_record["title_uid"])
    try:
        cursor.execute(query, values)
    except Exception:
        raise Exception


def read(dl: list) -> list[dict]:
    result = []
    for d in dl:
        if d["activity_org"] == "全部" and d["grade"] == "全部" and d["remote_check"] == "是":
            print(d["title"])
            result.append(d)
    return result
