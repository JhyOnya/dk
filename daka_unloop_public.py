# coding=utf-8

# from datetime import timezone, datetime, timedelta
import random, traceback, sys, datetime
from pytz import timezone

import smtplib
from email.mime.text import MIMEText
# import csv

import requests, json, time, re
from bs4 import BeautifulSoup


def datetime_as_timezone(date_time, time_zone):
    tz = timezone(time_zone)
    utc = timezone('UTC')
    return date_time.replace(tzinfo=utc).astimezone(tz)


def get_time(need_hour=False):
    date_time = datetime.datetime.utcnow()
    tz = timezone('Asia/Taipei')  # US/Eastern
    utc = timezone('UTC')
    date_time_tzone = date_time.replace(tzinfo=utc).astimezone(tz)
    if need_hour:
        return '{0:%Y-%m-%d %H:%M}'.format(date_time_tzone), date_time_tzone.hour
    else:
        return '{0:%Y-%m-%d %H:%M}'.format(date_time_tzone)


requests.packages.urllib3.disable_warnings()

# not_test = False  # 测试=False 正式=True
not_test = True  # 测试=False 正式=True


def send_message(addr, context):
    if addr == "":
        return
    if not not_test:
        return
    print(get_time(), "发送邮件", context, flush=True)
    smtp_server = 'smtp.163.com'  # smt.qq.com

    msg_mail = MIMEText(context + "\n" + get_time() + "\n\n\n    Sent by Onya")
    msg_mail['Subject'] = context
    msg_mail['From'] = fromMail
    msg_mail['To'] = "%s;%s" % (fromMail, addr)  # 接收消息的邮箱
    # msg_mail['To'] = fromMail + ";" + msg["toMail"]  # 接收消息的邮箱

    try:
        s = smtplib.SMTP()
        s.connect(smtp_server)
        s = smtplib.SMTP_SSL('smtp.163.com', 465)
        s.login(fromMail, mailPass)
        # s.sendmail(fromMail, msg["toMail"], msg_mail.as_string())
        s.sendmail(fromMail, [fromMail, addr], msg_mail.as_string())
        s.quit()

    except Exception as e:
        print('发送失败', str(e), end=' ', flush=True)


requests.packages.urllib3.disable_warnings()

login_url = 'https://ehall.jlu.edu.cn/sso/login'
form_url = 'https://ehall.jlu.edu.cn/infoplus/form/YJSMRDK/start'
start_url = 'https://ehall.jlu.edu.cn/infoplus/interface/start'
render_url = 'https://ehall.jlu.edu.cn/infoplus/interface/render'
action_url = 'https://ehall.jlu.edu.cn/infoplus/interface/doAction'
logout_url = "https://ehall.jlu.edu.cn/taskcenter/logout"

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36 Edg/87.0.664.47'


def get_formurl_by_grade(grade):
    url = 'https://ehall.jlu.edu.cn/infoplus/form/' + grade.upper() + 'MRDK/start'
    return url


def check(username, password, grade):
    while True:
        try:
            s = requests.Session()
            s.verify = False

            headers = {'User-Agent': UA}

            # login_html = s.get(url=logout_url)
            login_html = s.get(url=login_url, headers=headers)
            soup = BeautifulSoup(login_html.text, 'lxml')
            pid = soup.find(name="input", attrs={"name": "pid"}).get('value')

            # login
            data = {'username': username, 'password': password, 'pid': pid, 'source': ''}
            s.post(url=login_url, data=data, headers=headers)

            # get csrf_token
            form_html = s.get(url=get_formurl_by_grade(grade), headers=headers)
            soup = BeautifulSoup(form_html.text, 'lxml')
            csrf_token = soup.find(name="meta", attrs={"itemscope": "csrfToken"}).get('content')

            # get addr
            headers = {'User-Agent': UA, 'Referer': get_formurl_by_grade(grade)}
            data = {'idc': grade.upper() + 'MRDK', 'csrfToken': csrf_token}
            start_json = s.post(url=start_url, data=data, headers=headers)
            step_id = re.search('(?<=form/)\\d*(?=/render)', start_json.text)[0]
            csrf_token = soup.find(name="meta", attrs={"itemscope": "csrfToken"}).get('content')

            # get msg
            data = {'stepId': step_id, 'csrfToken': csrf_token}
            render = s.post(url=render_url, data=data, headers=headers)
            render_info = json.loads(render.content)['entities'][0]['data']
            render_info["fieldZtw"] = "1"
            if grade == "BKS":
                render_info["fieldDJXXyc"] = "1"

            # dk
            data = {
                'actionId': 1,
                'formData': json.dumps(render_info),
                'nextUsers': '{}',
                'stepId': step_id,
                'timestamp': int(time.time()),
                'csrfToken': csrf_token,
                'lang': 'zh'
            }
            print("  ", data)

            headers["Connection"] = "close"
            res = s.post(url=action_url, data=data, headers=headers)
            time.sleep(1)
            s.keep_alive = False
            s.close()
            time.sleep(1)

            if json.loads(res.content)['ecode'] == 'SUCCEED':
                return
            else:
                print(f"{get_time()} {username} failed.")

        except Exception as e:
            print(get_time(), e)
            print(get_time(), "Retrying...")
            time.sleep(5)


if __name__ == "__main__":
    print()
    print("完成情况", "https://ehall.jlu.edu.cn/taskcenter/wechat/done")
    print("\n---------------------------------------------------\n")

    fromMail = sys.argv[1]  
    mailPass = sys.argv[2] 
    msg = sys.argv[3]

    data = []
    for pre in msg.split("^^^"):
        data.append(pre.split(","))
        
    time.sleep(2*60)

    pre_time, pre_hour = get_time(need_hour=True)
    msg_fl = "msg_jian.csv"
    print("当前时间", pre_time, pre_hour)
    if pre_hour > 5 and pre_hour < 12:
        sign_time = "早签到"
    elif pre_hour > 18 and pre_hour < 24:
        sign_time = "晚签到"

    for pre_msg in data:
        usname = pre_msg[0]
        passwd = pre_msg[1]
        type = pre_msg[2]
        mail = pre_msg[3]
        need_night = pre_msg[4]
        print("\n\n")
        
        if need_night == '0' and sign_time == "晚签到":
            print("无需晚签到")
            continue

        while True:

            print(get_time(), sign_time)

            try:

                check(usname, passwd, type)
                print(get_time(), usname, "签到完毕")

                fresh_time = 1
                fresh_time_equal = 1

                send_message(mail, sign_time + "  成功")

                break

            except Exception:
                print("\n  error", end=' - ', flush=True)
                print(str(traceback.format_exc()).replace("\n", "        "))
                fresh_time += 1
            print("\n---------------------------------------------------\n")
            time.sleep(random.randint(30, 100))
    send_message(mail, sign_time + "全部打卡成功")
