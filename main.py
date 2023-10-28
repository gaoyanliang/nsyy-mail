from flask import Flask, jsonify, request, json
import nsyy_mail

# ===========================================================
# ===============        Flask        =======================
# ===========================================================


app = Flask(__name__)

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
