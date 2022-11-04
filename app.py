from flask import Flask, request, jsonify
import json
import hashlib
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from notification_interface_api import wecom_webhook_push_notification, send_email, send_sms
import config
import time


app = Flask(__name__)
app.config.from_object(config)
db_mysql = SQLAlchemy()


class Log(db_mysql.Model):
    __tablename__ = "Log"
    id = db_mysql.Column(db_mysql.Integer, primary_key=True, autoincrement=True)
    request_ip = db_mysql.Column(db_mysql.String(255), nullable=False)
    operation = db_mysql.Column(db_mysql.String(255), nullable=False)
    status = db_mysql.Column(db_mysql.String(255), nullable=False)
    time = db_mysql.Column(db_mysql.String(255), nullable=False)
    messages = db_mysql.Column(db_mysql.String(255), nullable=False)


db_mysql.init_app(app)
with app.app_context():
    db_mysql.create_all()

migrate = Migrate(app, db_mysql)


def save_log(request_ip, action, status, messages):
    date = time.strftime('%Y-%m-%d %H:%M:%S')
    dev_log = Log(request_ip=request_ip, operation=action, status=status, time=date, messages=messages)
    try:
        db_mysql.session.add(dev_log)
        db_mysql.session.commit()
    except Exception as err:
        print(err)


@app.route('/v1/notification_interface', methods=['GET', 'POST'])
def notification_interface():  # put application's code here
    if request.method == 'GET':
        return 'Receive WRONG request, not POST method. '

    elif request.method == 'POST':
        # 创建一个secret print(hashlib.sha256("wqwe21##$$dadad".encode()).hexdigest())
        secret_list = ['************************']
        try:
            record = json.loads(request.data)
            request_ip = request.remote_addr
            if 'SECRET' in record and 'operation_code' in record:
                secret = record['SECRET']
                operation_code = record['operation_code']

                if hashlib.sha256(secret.encode()).hexdigest() in secret_list:
                    # 发送企业微信
                    if operation_code == 1:
                        try:
                            wecom_url = record['wecom_url']
                            wecom_info = record['wecom_info']

                            try:
                                result = wecom_webhook_push_notification(wecom_url, wecom_info)
                                if result["status"] == "ok":
                                    save_log(request_ip, "wecom_hook", "ok", "no error")
                                    return jsonify(code=200,
                                                   msg="ok",
                                                   data=result["data"])

                                else:
                                    save_log(request_ip, "wecom_hook", "err", result["data"])
                                    return jsonify(code=403,
                                                   msg="err",
                                                   data=result["data"])
                            except Exception as err:
                                save_log(request_ip, "wecom_hook", "err", str(err))
                                return jsonify(code=403,
                                               msg="err",
                                               data="企业微信信息推送失败，原因是: {}".format(err))

                        except Exception as err:
                            save_log(request_ip, "wecom_hook", "err", "Failed to get parameters")
                            return jsonify(code=403,
                                           msg="err",
                                           data="企业微信信息推送失败，原因是 {} 字段不能为空".format(err))

                    # 发送邮件
                    elif operation_code == 2:
                        try:
                            email_title = record['email_title']
                            receive_email = record['receive_email']
                            email_info = record['email_info']
                            try:
                                result = send_email(email_title, receive_email, email_info)
                                if result["status"] == "ok":
                                    save_log(request_ip, "send_email", "ok", "no error")
                                    return jsonify(code=200,
                                                   msg="ok",
                                                   data=result["data"])
                                else:
                                    save_log(request_ip, "send_email", "err", result["data"])
                                    return jsonify(code=403,
                                                   msg="err",
                                                   data=result["data"])
                            except Exception as err:
                                save_log(request_ip, "send_email", "err", str(err))
                                return jsonify(code=403,
                                               msg="err",
                                               data="邮件信息推送失败，原因是: {}".format(err))

                        except Exception as err:
                            save_log(request_ip, "send_email", "err", "Failed to get parameters")
                            return jsonify(code=403,
                                           msg="err",
                                           data="邮件信息推送失败，原因是 {} 字段不能为空".format(err))

                    # 发送短信
                    elif operation_code == 3:
                        try:
                            sms_info = record['sms_info']
                            receive_phone = record['receive_phone']
                            try:
                                result = send_sms(receive_phone, sms_info)
                                if result["status"] == "ok":
                                    save_log(request_ip, "send_msm", "ok", "no error")
                                    return jsonify(code=200,
                                                   msg="ok",
                                                   data=result["data"])
                                else:
                                    save_log(request_ip, "send_msm", "err", result["data"])
                                    return jsonify(code=403,
                                                   msg="err",
                                                   data=result["data"])
                            except Exception as err:
                                save_log(request_ip, "send_msm", "err", str(err))
                                return jsonify(code=403,
                                               msg="err",
                                               data="短信推送失败，原因是: {}".format(err))
                        except Exception as err:
                            save_log(request_ip, "send_msm", "err", "Failed to get parameters")
                            return jsonify(code=403,
                                           msg="err",
                                           data="短信推送失败，原因是 {} 字段不能为空".format(err))

                    else:
                        save_log(request_ip, "noe", "err", "operation_code is error")
                        return jsonify(code=403,
                                       msg="err",
                                       data="operation_code is error must is 1-3")

                else:
                    save_log(request_ip, str(operation_code), "err", "SECRET EMPTY or SECRET ERROR")
                    return jsonify(code=403,
                                   msg="err",
                                   data="SECRET ERROR")
            else:
                save_log(request_ip, "none", "err", "SECRET or operation_code is empty")
                return jsonify(code=403,
                               msg="err",
                               data="SECRET or operation_code is empty")

        except Exception as err:
            save_log(request.remote_addr, "none", "err", "Failed to get parameters")
            return jsonify(code=403,
                           msg="err",
                           data=err)


if __name__ == '__main__':
    app.run()
