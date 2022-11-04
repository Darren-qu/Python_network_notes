import requests
import smtplib
import json
from email.mime.text import MIMEText
import hashlib
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest


def wecom_webhook_push_notification(wecom_url, wecom_infos,):
    try:
        headers = {"Content-Type": "text/plain"}
        result = requests.post(wecom_url, headers=headers, json=wecom_infos)
        if result.status_code == 200:
            if result.json()["errcode"] == 0:
                return {"status": "ok", "data": result.json()}
            return {"status": "error", "data": result.json()["errmsg"]}

        return {"status": "error", "data": result.json()}

    except Exception as err:
        return {"status": "error", "data": err}


def send_email(email_title, receive_email, email_info):
    message = MIMEText(email_info)
    message['Subject'] = email_title
    message['From'] = 'eit_script_running_status_notification'
    message['To'] = receive_email

    try:
        smtp_obj = smtplib.SMTP("smtp.gmail.com", 587)
        smtp_obj.starttls()
        # 配置发送邮箱账户密码
        smtp_obj.login('123@gmail.com', 'xxx')
        smtp_obj.sendmail('123@gmail.com', receive_email, message.as_string())
        smtp_obj.close()
        return {"status": "ok", "data": "None"}

    except smtplib.SMTPException as err:
        return {"status": "error", "data": err}


def unicom_send_sms_china(phonenumber, sms_text):
    try:
        headers = {"Content-Type": "text/plain"}
        cpcode = 'xxxx'
        msg = str(sms_text).encode(encoding='utf-8').decode()
        mobiles = phonenumber
        excode = 'xxxx'
        templetid = 'xxxx'
        key = 'xxxx'
        sign_text = '%s%s%s%s%s%s' % (cpcode, msg, mobiles, excode, templetid, key)
        sign = hashlib.md5(sign_text.encode(encoding='utf-8')).hexdigest()
        print(sign)
        data = {
            'cpcode': cpcode,
            'msg': msg,
            'mobiles': mobiles,
            'excode': excode,
            'templetid': templetid,
            'sign': sign
        }
        request = requests.post(url="https://rcsapi.wo.cn:8043/umcinterface/sendtempletmsg", json=data)
        return {"status": "ok", "data": request.text}

    except Exception as err:
        return {"status": "error", "data": err}


def aliyun_sent_sms_oversea(to_address, message):
    try:
        # 在阿里云申请账户信息
        client = AcsClient('xxxx', 'xxxx', 'xxx')
        aliyun_request = CommonRequest()
        aliyun_request.set_accept_format('json')
        aliyun_request.set_domain('dysmsapi.ap-southeast-1.aliyuncs.com')
        aliyun_request.set_method('POST')
        aliyun_request.set_version('2018-05-01')
        aliyun_request.set_action_name('SendMessageToGlobe')
        aliyun_request.add_query_param('To', to_address)
        aliyun_request.add_query_param('Message', message)
        print(message)
        response = client.do_action(aliyun_request)
        return {"status": "ok", "data": str(response, encoding='utf-8')}

    except Exception as err:
        return {"status": "error", "data": err}


def send_sms(phone_number, send_sms_txt):
    # 通过+86判断使用联通还是阿里云发送。
    if '+86' in phone_number:
        phone_number = phone_number[3:]
        if len(phone_number) == 11:
            unicom_result = unicom_send_sms_china(phone_number, send_sms_txt)
            return unicom_result

        return {"status": "error", "data": "国内短信发送失败，请检查国家号或长度"}

    else:
        aliyun_result = aliyun_sent_sms_oversea(phone_number, send_sms_txt)
        return aliyun_result
