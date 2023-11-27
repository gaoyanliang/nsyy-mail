from flask import Flask, jsonify, request, json, render_template, redirect, url_for, send_file
from mail_service import fetch_attachment
import mail_service

app = Flask(__name__)

# ===========================================================
# ===============     mail manager    =======================
# ===========================================================


"""发送邮件"""


@app.route('/send_email', methods=['POST'])
def send_email():
    from_email = request.form['from']
    recipient = request.form['recipient']
    cc = request.form['cc']
    bcc = request.form['bcc']
    subject = request.form['subject']
    message = request.form['message']
    attachment = request.files['attachment']

    mail_service.send_email(from_email, recipient, cc, bcc, subject,  message, attachment)

    return redirect(url_for('index'))


"""读取邮件列表"""


@app.route('/read_mail_list', methods=['GET'])
def fetch_mail_list():
    pers_id = request.args.get("pers_id")
    email_account = request.args.get("email_account")
    page_size = request.args.get("page_size")
    page_number = request.args.get("page_number")
    email_list = []
    if request.method == 'GET':
        email_list = mail_service.read_mail_list(int(pers_id), email_account, int(page_size), int(page_number))
    return render_template('display_emails.html', email_data=email_list)


@app.route('/download_attachment', methods=['GET'])
def download_attachment():
    attachment_name = request.args.get("attachment_name")
    pers_id = request.args.get("pers_id")
    email_account = request.args.get("email_account")
    email_id = request.args.get("email_id")

    attachments = list(fetch_attachment(int(pers_id), email_account, email_id))

    for attachment in attachments:
        if attachment_name.__contains__(attachment[0]):
            # Save the attachment to a file
            with open(attachment[0], 'wb') as file:
                file.write(attachment[1])

            return "Attachment saved as: " + attachment[0]
            # data_stream = BytesIO(attachment[1])
            # return send_file(data_stream, as_attachment=True, download_name=attachment[0])

    return "Attachment not found", 404

# ===========================================================
# ===============  mail user manager  =======================
# ===========================================================


"""
创建用户
通过指定用户名和密码来创建邮箱账户
"""


@app.route('/create_a_new_mail_user', methods=['POST'])
def create_a_new_mail_user():
    data = request.json
    print(data)
    mail_service.create_a_new_mail_user(data.get('username'), data.get('password'))
    return "<p>Hello, World!</p>"


"""
批量创建用户
目前仅支持，传递邮箱名列表，密码默认 111111
"""


@app.route('/create_multiple_mail_user', methods=['POST'])
def create_multiple_mail_user():
    data = request.json
    print(data)
    mail_service.create_multiple_mail_user(data.get('mail_name_list'))
    return "<p>Hello, World!</p>"


"""
更新用户密码
"""


@app.route('/update_mail_user_password', methods=['PUT'])
def update_mail_user_password():
    data = request.json
    print(data)
    mail_service.update_mail_user_password(data.get('mail_user'), data.get('new_password'))
    return f"update mail user {data.get('mail_user')} password successful."


# ===========================================================
# =============== contact group manager =====================
# ===========================================================

# 。。。。。。

"""测试接口"""


@app.route('/')
def index():
    return render_template('email_from.html')


@app.route('/returnjson', methods=['GET'])
def return_json():
    if request.method == 'GET':
        data = {
            "Modules": 15,
            "Subject": "Data Structures and Algorithms",
        }

        data1 = {
            "data": data
        }

        return jsonify(data1)

    # Press the green button in the gutter to run the script.


if __name__ == '__main__':
    app.run(debug=True)
