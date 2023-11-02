from flask import Flask, jsonify, request, json
import nsyy_mail

app = Flask(__name__)

# ===========================================================
# ===============     mail manager    =======================
# ===========================================================


"""根据邮件id读取邮件"""


@app.route('/send_mail', methods=['GET'])
def send_mail():
    nsyy_mail.send_mail()

    return "<p>Hello, World!</p>"


"""根据邮件id读取邮件"""


@app.route('/read_mail', methods=['GET'])
def read_mail():
    email_id = request.args.get("email_id")
    if request.method == 'GET':
        nsyy_mail.read_mail(email_id)

    return "<p>Hello, World!</p>"


"""读取邮件列表"""


@app.route('/read_mail_list', methods=['GET'])
def fetch_mail_list():
    if request.method == 'GET':
        nsyy_mail.read_mail_list()

    return "<p>Hello, World!</p>"


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
    nsyy_mail.create_a_new_mail_user(data.get('username'), data.get('password'))
    return "<p>Hello, World!</p>"


"""
批量创建用户
目前仅支持，传递邮箱名列表，密码默认 111111
"""


@app.route('/create_multiple_mail_user', methods=['POST'])
def create_multiple_mail_user():
    data = request.json
    print(data)
    nsyy_mail.create_multiple_mail_user(data.get('mail_name_list'))
    return "<p>Hello, World!</p>"


"""
更新用户密码
"""


@app.route('/update_mail_user_password', methods=['PUT'])
def update_mail_user_password():
    data = request.json
    print(data)
    nsyy_mail.update_mail_user_password(data.get('mail_user'), data.get('new_password'))
    return f"update mail user {data.get('mail_user')} password successful."


# ===========================================================
# ===============  mail list manager  =======================
# ===========================================================

"""查询目前创建了哪些 mail list"""


@app.route("/mail_lists", methods=['GET'])
def query_mail_lists():
    mail_lists = nsyy_mail.get_mail_lists()
    return jsonify(mail_lists)


"""查询 mail list 有哪些订阅者"""


@app.route("/mail_list_all_subscribers", methods=['GET'])
def query_mail_list_all_subscribers():
    mail_list_name = request.args.get("mail_list_name")
    subscribers = nsyy_mail.get_mail_list_all_subscribers(mail_list_name)
    return subscribers


"""Create a new mailing list account"""


@app.route("/create_new_mail_list_account", methods=['POST'])
def create_new_mail_list_account():
    data = request.json
    print(data)
    subscribers = nsyy_mail.create_new_mail_list_account(data.get('mail_list_name'))
    return subscribers


"""Get settings of an existing mailing list account"""


@app.route("/query_mail_list_settings", methods=['GET'])
def query_mail_list_settings():
    mail_list_name = request.args.get("mail_list_name")
    output = nsyy_mail.get_mail_list_settings(mail_list_name)
    return output


"""Delete an existing mailing list account"""


@app.route("/delete_mail_list", methods=['POST'])
def delete_mail_list():
    data = request.json
    print(data)
    mail_list_name = data.get("mail_list_name")
    output = nsyy_mail.delete_mail_list(mail_list_name)
    return output


"""Check whether mailing list has given subscriber."""


@app.route("/check_has_subscriber", methods=['GET'])
def check_whether_mail_list_has_subscriber():
    mail_list_name = request.args.get("mail_list_name")
    subscriber = request.args.get("subscriber")
    output = nsyy_mail.check_whether_mail_list_has_subscriber(mail_list_name, subscriber)
    return output


"""Show all subscribed lists of a given subscriber."""


@app.route("/show_all_subscribed", methods=['GET'])
def show_all_subscribed_of_subscriber():
    subscriber = request.args.get("subscriber")
    output = nsyy_mail.show_all_subscribed_of_subscriber(subscriber)
    return output


"""Add new subscribers to mailing list."""


@app.route("/add_subscribers", methods=['POST'])
def add_subscribers_to_mail_list():
    data = request.json
    print(data)
    mail_list_name = data.get("mail_list_name")
    subscribers = data.get("subscribers")
    output = nsyy_mail.add_subscribers_to_mail_list(mail_list_name, subscribers)
    return output


"""Remove existing subscribers from mailing list."""


@app.route("/remove_subscribers", methods=['POST'])
def remove_subscribers_from_mail_list():
    data = request.json
    print(data)
    mail_list_name = data.get("mail_list_name")
    subscribers = data.get("subscribers")
    output = nsyy_mail.remove_subscribers_from_mail_list(mail_list_name, subscribers)
    return output


"""测试接口"""


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


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
