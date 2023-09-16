import base64
import json
import os
import time

import uuid
import uvicorn
from fastapi import FastAPI, Query, Body, Depends
from starlette.responses import Response, StreamingResponse
from starlette.requests import Request
from starlette.responses import HTMLResponse, FileResponse, RedirectResponse
from starlette.staticfiles import StaticFiles
from pydantic import BaseModel

from core.sqltool import *
from core.xxu import get_unscheduled_lessons, create_token, create_jw_token, get_students

app = FastAPI()


# 挂载 Ant Design 构建的静态文件到根路径
# app.mount("/ad", StaticFiles(directory="dist",html=True), name="static")
# app.mount("/ad/welcome", StaticFiles(directory="dist",html=True), name="static")
# app.mount("/scripts", StaticFiles(directory="dist/scripts", html=True), name="static")


@app.on_event("startup")
async def startup_event():
    # os.remove("install.lock")
    init_db()


@app.middleware("http")
async def handle_non_api_requests(request: Request, call_next):
    if request.url.path.startswith("/api"):
        # 如果路径以 /api 开头，则正常处理请求
        print("api")
        response = await call_next(request)
    else:
        # 否则，重定向到静态文件或首页
        path = os.path.join("dist", request.url.path[1:])
        if os.path.isfile(path):
            response = FileResponse(path)
        else:
            response = FileResponse("dist/index.html")
    return response


class LoginAccount(BaseModel):
    autoLogin: bool
    password: str
    type: str
    username: str


@app.post("/api/login/account")
async def login_account(request: Request, response: Response, account: LoginAccount):
    print(account.password)
    print(account.username)
    username = account.username
    password = account.password
    # print(username, password)
    app_login_info = create_token(username, password)
    if not app_login_info["status"]:
        return {"status": "error", "type": "account", "currentAuthority": "guest"}
    secret, token, roleId = create_jw_token(app_login_info["token"])
    userdata = {
        "secret": secret,
        "token": token,
        "roleId": roleId,
        "userToken": app_login_info["token"]
    }
    userdata = json.dumps(userdata)
    login_uuid = str(uuid.uuid4())
    login_token = str(uuid.uuid1())
    sqlcmd = f"insert into cookie (uuid,token, userdata) values ('{login_uuid}', '{login_token}', '{userdata}')"
    no_result_sql(sqlcmd)
    response.set_cookie(key="uuid", value=login_uuid)
    response.set_cookie(key="token", value=login_token)
    return {
        "status": "ok",
        "type": "account",
        "currentAuthority": "user"
    }


@app.post('/api/login/outLogin')
async def login_outLogin(request: Request):
    return out_login(request.cookies.get("uuid"), request.cookies.get("token"))


@app.get("/api/currentUser")
async def current_user(response: Response, cookie_status: dict = Depends(check_cookie)):
    print(cookie_status)
    if not cookie_status["status"]:
        response.status_code = 401
        return {
            "data": {
                "isLogin": False
            },
            "errorCode": "401",
            "errorMessage": "非法访问！",
            "showType": 9,
            "success": True
        }
    identityTypeName = cookie_status["data"]["attributes"]['identityTypeName']
    organizationName = cookie_status["data"]["attributes"]['organizationName']
    userName = cookie_status["data"]["attributes"]['userName']
    userUid = cookie_status["data"]["attributes"]['userUid']
    imageUrl = cookie_status["data"]["attributes"]['imageUrl']
    if imageUrl:
        imageUrl = "https://authx-service.xxu.edu.cn/personal/api/v1/personal/me/portrait?idToken=" + cookie_status['data']['login'][
            'userToken'] + "&imageUrl=" + imageUrl
    else:
        imageUrl = "https://www.xxu.edu.cn/dfiles/9773/images/logo_01.png"
    return {
        "success": True,
        "data": {
            "name": userName,
            "avatar": imageUrl,
            "organizationName": organizationName,
            "identityTypeName": identityTypeName,
            "userUid": userUid
        }
    }


@app.get("/api/class")
async def get_class(response: Response, cookie_status: dict = Depends(check_cookie)):
    if not cookie_status["status"]:
        response.status_code = 401
        return {
            "data": {
                "isLogin": False
            },
            "errorCode": "401",
            "errorMessage": "非法访问！",
            "showType": 9,
            "success": True
        }
    class_data = get_unscheduled_lessons(74, cookie_status['data']['login']['token'], cookie_status['data']['login']['secret'],
                                         cookie_status['data']['login']['roleId'])
    return class_data


@app.get('/api/rollcall')
async def get_student(lesson_id, response: Response, cookie_status: dict = Depends(check_cookie)):
    if not cookie_status["status"]:
        response.status_code = 401
        return {
            "data": {
                "isLogin": False
            },
            "errorCode": "401",
            "errorMessage": "非法访问！",
            "showType": 9,
            "success": True
        }
    student_data = get_students(cookie_status['data']['login']['token'], cookie_status['data']['login']['userToken'], lesson_id,
                                cookie_status['data']['login']['secret'])
    # print(student_data)
    return student_data


@app.post('/api/result')
async def get_student(lesson_id, request: Request, response: Response, cookie_status: dict = Depends(check_cookie)):
    if not cookie_status["status"]:
        response.status_code = 401
        return {
            "data": {
                "isLogin": False
            },
            "errorCode": "401",
            "errorMessage": "非法访问！",
            "showType": 9,
            "success": True
        }
    try:
        ip = request.headers['x_forwarded_for']
    except:
        ip = request.client.host
    result_data = await request.json()
    class_data = get_unscheduled_lessons(74, cookie_status['data']['login']['token'], cookie_status['data']['login']['secret'],
                                         cookie_status['data']['login']['roleId'])
    lesson_name, teacher, student_num = ("", "", "")
    for i in class_data:
        print(i['lesson_id'])
        if i['lesson_id'] == int(lesson_id):
            print("找到了")
            lesson_name = i['course_name']
            teacher = i['teachers']
            student_num = i['teachclass_std_count']
            break
    else:
        return {"status": False, "message": "出现了错误！"}
    randomstr = random.randint(10000, 99999)
    userName = cookie_status["data"]["attributes"]['userName']
    userUid = cookie_status["data"]["attributes"]['userUid']
    rollcall_time = int(time.time())
    result_url = hashlib.md5(
        f"{randomstr}{userName}{userUid}{rollcall_time}{lesson_id}".encode("utf-8")).hexdigest()
    sql_cmd = f"insert into rollcall (random,rollcall,rollcall_uid,rollcall_time,teacher,course,course_id,student_num,result_url,ip) values('{randomstr}','{userName}','{userUid}','{rollcall_time}','{teacher}','{lesson_name}','{lesson_id}','{student_num}','{result_url}','{ip}')"
    no_result_sql(sql_cmd)
    result_datas = base64.b64encode(json.dumps(result_data, ensure_ascii=False).encode("utf-8")).decode("utf-8")
    sql_cmd = f"insert into rollcall_data (result_url,result_data) values('{result_url}','{result_datas}')"
    no_result_sql(sql_cmd)
    # with open(f"data/{randomstr}{userName}{userUid}{rollcall_time}{teacher}{course}{lesson_id}{student_num}.json", "w",
    #           encoding="utf-8") as f:
    #     f.write(json.dumps(result_data, indent=4, ensure_ascii=False))
    return {"status": True, 'data': {"result_id": result_url}}


@app.get("/api/result")
def get_result(result_id):
    result = select_sql(f"select * from rollcall_data where result_url = '{result_id}'")
    class_info = select_sql(f"select * from rollcall where result_url = '{result_id}'")
    if len(result) == 0 or len(class_info) == 0:
        return {"status": False, "message": "出现了错误！"}
    else:
        result = json.loads(base64.b64decode(result[0][2]).decode("utf-8"))
        print(result)
        leveStudent = []
        presentStudent = []
        lateStudent = []
        TeacherName = class_info[0][5]
        studentCount = class_info[0][8]
        className = class_info[0][6]
        for i in result['data']:
            if i['result'] == 'leave':
                leveStudent.append(i)
            elif i['result'] == 'present':
                presentStudent.append(i)
            elif i['result'] == 'late':
                lateStudent.append(i)
        return {"status": True, "className": className, "TeacherName": TeacherName, "presentStudent": presentStudent,
                "lateStudent": lateStudent, "leveStudent": leveStudent, "studentCount": studentCount}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
