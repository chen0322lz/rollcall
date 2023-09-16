import hashlib
import json
import os
import random
import sqlite3
from configparser import ConfigParser
from starlette.requests import Request

from core.xxu import get_user_info


def init_db():
    if os.path.exists("data/test.db"):
        return
    print("数据库文件不存在")
    try:
        conn = sqlite3.connect("data/test.db")
        print(sqlite3.version)

        c = conn.cursor()
        # Create cookie record table
        c.execute('''CREATE TABLE cookie
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                uuid TEXT NOT NULL,
                token TEXT NOT NULL,
                userdata TEXT NOT NULL);''')
        # 创建点名记录表，有随机字符串，点名人，点名人学号，点名时间，点名数据，任课老师，课程名称，课程id,学生数目，点名结果页面hash
        c.execute('''CREATE TABLE rollcall
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    random TEXT NOT NULL,
                    rollcall TEXT NOT NULL,
                    rollcall_uid TEXT NOT NULL,
                    rollcall_time TEXT NOT NULL,
                    teacher TEXT NOT NULL,
                    course TEXT NOT NULL,
                    course_id TEXT NOT NULL,
                    student_num TEXT NOT NULL,
                    result_url TEXT NOT NULL,
                    ip TEXT NOT NULL);''')
        # 创建点名数据存储表，有点名结果页面hash，点名结果rsa加密过的base64编码
        c.execute('''CREATE TABLE rollcall_data
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    result_url TEXT NOT NULL,
                    result_data TEXT NOT NULL);''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(e)


def select_sql(command):
    conn = sqlite3.connect("data/test.db")
    c = conn.cursor()
    c.execute(command)
    result = c.fetchall()
    conn.close()
    return result


def no_result_sql(command):
    try:
        conn = sqlite3.connect("data/test.db")
        c = conn.cursor()
        c.execute(command)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(e)
        return False


def check_cookie(request: Request):
    if 'uuid' not in request.cookies or 'token' not in request.cookies:
        return {'status': False, "data": ""}
    sqlcmd = f"select * from cookie where uuid = '{request.cookies['uuid']}' and token = '{request.cookies['token']}'"
    result = select_sql(sqlcmd)
    print(result)
    if len(result) == 0:
        return {'status': False, "data": ""}
    else:
        result = json.loads(result[0][3])
        info = get_user_info(result['userToken'])
        if not info['status']:
            out_login(request.cookies['uuid'], request.cookies['token'])
            return {"status": False, "data": []}
        else:
            info['data']['login'] = result
            return {"status": True, "data": info["data"]}


def out_login(uuid, token):
    sqlcmd = "delete from cookie where uuid = '{}' and token='{}'".format(uuid, token)
    try:
        no_result_sql(sqlcmd)
    except Exception as e:
        print(e)
        return {"success": False}
    return {"success": True}
