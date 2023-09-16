import base64
import hashlib
import json
import requests

lacation = "local"

if lacation == "local":
    CAS_URL = "https://cas.xxu.edu.cn"
    Authx_Service_URL = "https://authx-service.xxu.edu.cn"
    JW_URL = "https://jwapp.xxu.edu.cn"
else:
    CAS_URL = "https://cas-xxu.ggboy.link"
    Authx_Service_URL = "https://authx-service-xxu.ggboy.link"
    JW_URL = "https://jwapp-xxu.ggboy.link"


def app_headers(userToken) -> dict:
    """
    生成请求头
    :param token: 新乡学院token
    :return: 请求头
    """
    hea = {
        "User-Agent": "SWSuperApp/1.0.6(HUAWEIELS-AN00HUAWEI12)",
        "X-Id-Token": userToken,
        "Cookie": f"userToken={userToken}; Domain=stuworkapp.xxu.edu.cn; Path=/"
    }
    return hea


def jw_headers(token, userToken) -> dict:
    """
    生成请求头
    :param jwtoken: userToken
    :param token: 新乡学院token
    :return: 请求头
    """
    hea = {
        "Connection": "keep-alive",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Linux; Android 12; ELS-AN00 Build/HUAWEIELS-AN00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/99.0.4844.88 Mobile Safari/537.36 SuperApp",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://jwapp.xxu.edu.cn",
        "X-Requested-With": "com.supwisdom.xxxy",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://jwapp.xxu.edu.cn/app-web/",
        "token": token,
        "Cookie": f"INGRESSCOOKIE=a3cee41444df2b91509aeaf65e5d5e5f; userToken={userToken}; Domain=jwapp.xxu.edu.cn; Path=/"
    }
    return hea


def get_random_sign_timestamp(params, secret):
    """
    MD5签名方法

    构成：
    参数按照字典顺序排序后连接起来
    MD5(secret + '|' + param1 + '|' + ... + timestamp + '|' + random).大写()

    参数：
    - params (dict): 请求参数
    - secret (str): 密钥
    返回：
    - 随机字符串，时间戳，签名
    """
    # random_str = random.randint(100000, 900000)
    random_str = 91949
    timestamp = 1692443233060
    # timestamp = int(time.time())
    # print(params)
    param_list = [secret] + [str(params[k]) for k in sorted(params.keys())] + [str(timestamp), str(random_str)]
    # print(param_list)
    param_str = '|'.join(param_list)
    # print(param_str)
    return random_str, hashlib.md5(param_str.encode('utf-8')).hexdigest().upper(), timestamp


def create_token(stu_id, passwd) -> dict:
    """
    获取新乡学院token
    :param stu_id: 学号
    :param passwd: 密码
    :return: 返回字典类型，status为true时，token为token值，status为false时，token为空
    """
    url = f"{CAS_URL}/token/password/passwordLogin?username={stu_id}&password={passwd}&appId=com" \
          f".supwisdom.xxxy&geo=&deviceId=Yz1X0Jel2wMDAN9DBSoHMsGs&osType=android&clientId" \
          f"=b98353dc80193ffeec740e69326a9b42&mfaState="
    print(url)
    headers = {
        "User-Agent": "SWSuperApp/1.0.5(HUAWEIELS-AN00HUAWEI12)",
    }
    r = requests.post(url, headers=headers)
    print(r.status_code)
    print(r.text)
    if r.status_code == 200:
        return {"status": True, 'token': r.json()['data']['idToken']}
    else:
        return {"status": False, 'token': ""}


def create_jw_token(userToken):
    """
    获取教务处token
    :param headers: 携带新乡学院app token的请求头
    :return: 返回的第一个值为教务处sign值的拼接md5，第二值为教务处的token
    """
    url = f'{JW_URL}/app-ws/ws/app-service/super/app/login-token'
    headers = {
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Linux; Android 12; ELS-AN00 Build/HUAWEIELS-AN00; wv) AppleWebKit/537.36 (KHTML, "
                      "like Gecko) Version/4.0 Chrome/92.0.4515.105 Mobile Safari/537.36 SuperApp",
        "Content-Type": "application/x-www-form-urlencoded",
        'userToken': userToken,
        "Cookie": f"userToken={userToken};"
    }
    secret = "supwisdom_eams_app_secret"
    params = {
        "userToken": userToken
    }
    # print(params)
    # headers['userToken'] = userToken
    randomstr, sign, timestamp = get_random_sign_timestamp(params, secret)
    r = requests.post(url, headers=headers, data=f'random={randomstr}&timestamp={timestamp}&userToken={userToken}')
    # print(r.status_code)
    # print(r.json())
    jw_data = r.json()['business_data']
    jw_data = json.loads(base64.b64decode(jw_data).decode("utf-8"))
    jwtoken = jw_data['token']
    secret = jw_data['secret']
    roleId = jw_data['roleId']
    return secret, jwtoken, roleId


def get_user_info(token) -> dict:
    """
    获取用户信息
    :param token: 新乡学院token
    :return: 返回字典类型，status为true时，token为token值，status为false时，token为空
    """
    try:
        url = f"{Authx_Service_URL}/personal/api/v1/personal/me/user"
        headers = {
            "X-Device-Info": "HUAWEIELS-AN001.9.9.81096",
            "Accept": "application/json",
            "X-Device-Infos": "{\"packagename\":__UNI__AA068AD,\"version\":1.0.6,\"system\":Android 12}",
            "X-Id-Token": token,
            "X-Terminal-Info": "app",
            "Content-Type": "application/json",
            "user-agent": "Mozilla/5.0 (Linux; Android 12; ELS-AN00 Build/HUAWEIELS-AN00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/92.0.4515.105 Mobile Safari/537.36 uni-app Html5Plus/1.0 (Immersed/42.566036)",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip"
        }
        r = requests.get(url, headers=headers)
        # print(r.status_code)
        print(r.json())
        if r.status_code == 200:
            return {"status": True, 'data': r.json()['data']}
        else:
            return {"status": False, 'data': ""}
    except Exception as e:
        # print(e)
        return {"status": False, 'data': ""}


# get_user_info(token)

def get_students(token, userToken, lesson_id, secret):
    """

    :return:
    """
    try:
        headers = jw_headers(token, userToken)
        url = f"{JW_URL}/app-ws/ws/app-service/course/schedule/lesson/get-students"
        param = {
            "lessonId": lesson_id,
            "token": token
        }
        randomstr, sign, timestamp = get_random_sign_timestamp(param, secret)
        data = f"lesson_id={lesson_id}&random={randomstr}&sign={sign}&timestamp={timestamp}&token={token}"
        r = requests.post(url, headers=headers, data=data)
        # print(r.status_code)
        r_data = r.json()["business_data"]
        r_data = json.loads(base64.b64decode(r_data).decode("utf-8"))
        # print(r_data)
        return r_data
    except Exception as e:
        # print(e)
        return []


def get_unscheduled_lessons(semester_id, token, secret, roleId):
    try:
        param = {
            "biz_type_id": 1,
            "semester_id": semester_id,
            "token": token
        }
        if roleId == "1":
            role = "student"
        elif roleId == "2":
            role = "teacher"
        else:
            return []
        randomstr, sign, timestamp = get_random_sign_timestamp(param, secret)
        headers = jw_headers(token, "")
        url = f"{JW_URL}/app-ws/ws/app-service/{role}/course/schedule/get-unscheduled-lessons"
        data = f"biz_type_id=1&semester_id={semester_id}&sign={sign}&timestamp={timestamp}&token={token}&random={randomstr}"
        r = requests.post(url, headers=headers, data=data)
        # print(r.status_code)
        r_data = r.json()["business_data"]
        r_data = json.loads(base64.b64decode(r_data).decode("utf-8"))['arrange_lessons']
        # print(r_data)
        return r_data
    except Exception as e:
        # print(e)
        return []

# secret = "00b0309b5ea047ea96d661e6f40dc30f"
# userToken = ""
# lesson_id = "162110"
# token = "be6a4c979b004ed8a67318be41cbd89f"
# semester_id = 54
# get_unscheduled_lessons(semester_id, token, secret)
