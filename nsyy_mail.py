import imaplib
import email
from db_utils import DbUtil
from ssh_utils import SshUtil
from pprint import pprint
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
import datetime

# ===========================================================
# ===============        config       =======================
# ===========================================================


# IMAP Server and User Information
mail_server = '192.168.124.128'
# mail_username = 'a1@nsyy.com'
# mail_password = "Nsyy.2015"
mail_username = 'postmaster@nsyy.com'
mail_password = '111111'
mail_mailbox = 'Sent'  # You can change this to the mailbox you want to read.
# mail_mailbox = 'INBOX'  # You can change this to the mailbox you want to read.

# Email server settings
smtp_server = "192.168.124.128"
smtp_port = 587
smtp_username = 'postmaster@nsyy.com'
smtp_password = '111111'

# IMAP server settings
imap_server = "192.168.124.128"
imap_port = 993

# db config
db_host = '192.168.124.128'
db_port = 3306
db_user = 'root'
db_passwd = '111111'
db_database = 'vmail'

# SSH connection details
ssh_host = "192.168.124.128"
ssh_username = "root"
ssh_password = "111111"


# ===========================================================
# ===============         mail        =======================
# ===========================================================


"""通过邮件 id 精确读取邮件"""


def send_mail():
    # Sender and recipient email addresses
    sender_email = "postmaster@nsyy.com"
    recipient_emails = ["test1@nsyy.com", "test2@nsyy.com", "test3@nsyy.com", "test4@nsyy.com"]
    cc_emails = ["a1@nsyy.com", "a2@nsyy.com", "a3@nsyy.com", "a4@nsyy.com"]
    bcc_emails = ["yanliang@nsyy.com"]

    # Create a message container
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = ", ".join(recipient_emails)
    msg["Cc"] = ", ".join(cc_emails)
    msg["Bcc"] = ", ".join(bcc_emails)
    msg["Subject"] = "测试发送邮件" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Add the email body
    body = "Hello, this is the email body. 这是邮件内容"
    msg.attach(MIMEText(body, "plain"))

    # Attach an image
    image_path = "/Users/gaoyanliang/Pictures/test.png"
    with open(image_path, "rb") as image_file:
        image = MIMEImage(image_file.read())
        image.add_header("Content-ID", "<image1>")
        image.add_header('Content-Disposition', 'attachment', filename=image_path)
        msg.attach(image)

    # Attach a file
    file_path = "/Users/gaoyanliang/nsyy/yym-iredmail-install.md"
    attachment = open(file_path, "rb")
    part = MIMEBase("application", "octet-stream")
    part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f"attachment; filename=iredmail_install.md")
    msg.attach(part)

    try:
        # Connect to the SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)

        # Send the email
        email_text = msg.as_string()
        server.sendmail(sender_email, recipient_emails + cc_emails + bcc_emails, email_text)

        # Close the SMTP server connection
        server.quit()

        print("Email sent successfully")
    except smtplib.SMTPException as e:
        print(f"Failed to send the email: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

    # Save the just-sent email to the Sent folder
    # Connect to the IMAP server
    mail = imaplib.IMAP4_SSL(imap_server, imap_port)
    mail.login(smtp_username, smtp_password)

    # Select the "Sent" mailbox
    mailbox = "Sent"  # You may need to adjust this based on your server's folder naming
    mail.select(mailbox)

    # Append the sent email to the "Sent" folder
    email_bytes = email_text.encode('utf-8')
    mail.append(mailbox, None, None, email_bytes)

    # Close the IMAP server connection
    mail.logout()


"""通过邮件 id 精确读取邮件"""


def read_mail(email_id):
    # Connect to the IMAP server
    mail = __login_mail()

    # Fetch the email based on the ID
    __read_mail_by_mail_id(mail, email_id)

    # Close the mailbox and log out
    __close_mail(mail)


"""读取邮件列表"""


def read_mail_list():
    # Connect to the IMAP server
    mail = __login_mail()

    # Search for all emails in the mailbox. use UNSEEN search unread mail
    try:
        status, email_ids = mail.search(None, "All")
    except:

        print("Debugging: Failed to retrieve email list.")
        mail.logout()
        exit(1)

    # Get a list of email IDs
    email_id_list = email_ids[0].split()

    # Loop through the email IDs and fetch the email details
    print(f"search email count: {len(email_id_list)} \n")
    for email_id in email_id_list:
        print(f'========> email_id type: {type(email_id)}')
        # Fetch the email based on the ID
        __read_mail_by_mail_id(mail, email_id)

    # Close the mailbox and log out
    __close_mail(mail)


"""登陆邮件服务器"""


def __login_mail():
    # Connect to the IMAP server
    try:
        mail = imaplib.IMAP4_SSL(mail_server)
        print("Debugging: Successed to connect to the IMAP server.")
    except:
        print("Debugging: Failed to connect to the IMAP server.")
        exit(1)

    # Login to the email account
    try:
        mail.login(mail_username, mail_password)
        print("Debugging: Login successed. ")
    except:
        print("Debugging: Login failed. Please check your credentials.")
        mail.logout()
        exit(1)

    # list mailboxes
    typ, data = mail.list()
    print('Debugging: Response:')
    pprint(data)

    # Select the mailbox you want to read, 使用 select() 方法选择要读取的邮件文件夹
    try:
        mail.select(mail_mailbox)
    except:
        print("Debugging: Failed to select the mailbox.")
        mail.logout()
        exit(1)

    return mail


"""通过 email id 读取邮件"""


def __read_mail_by_mail_id(mail, email_id):
    # Fetch the email based on the ID
    result, message_data = mail.fetch(email_id, '(FLAGS BODY.PEEK[])')
    if result == "OK":

        # Extract email flags and Check if the email is marked as unread
        flags = message_data[0][0].decode("utf-8").split("FLAGS (")[1].split(")")[0]
        # flags = msg_data[0][0].decode("utf-8").split("FLAGS (")[1].split(")")[0] if msg_data[0][0] else ""

        is_unread = "\\Seen" not in flags

        # Parse the email message
        msg = email.message_from_bytes(message_data[0][1])

        # Print the email details
        print(f"================== mail {email_id} ==================")
        print("Unread     : {}".format('Yes' if is_unread else 'No'))
        print("Email ID   : {}".format(email_id))
        print("Subject    : {}".format(msg.get("Subject")))
        print("From       : {}".format(msg.get("From")))
        print("To         : {}".format(msg.get("To")))
        print("CC         : {}".format(msg.get("CC")))
        print("Bcc        : {}".format(msg.get("Bcc")))
        print("Priority   : {}".format(msg.get("Priority")))
        print("ReplyToList: {}".format(msg.get("ReplyToList")))
        print("Date       : {}".format(msg.get("Date")))

        # Get the email content
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    print("\nMessage:")
                    print(body)
        else:
            body = msg.get_payload(decode=True).decode()
            print("\nMessage:")
            print(body)


"""关闭邮箱相关连接"""


def __close_mail(mail):
    # Close the mailbox and log out
    mail.close()
    mail.logout()


# ===========================================================
# ===============     user manager    =======================
# ===========================================================

"""停用账户"""


def deactivate_account(deactivate_username: str):
    db = DbUtil(db_host, db_port, db_user, db_passwd, db_database)

    sql = f"update mailbox set active=0 where username='{deactivate_username}'"
    db.execute(sql)
    db.commit()

    del db


"""创建单个账户"""


def create_a_new_mail_user(mail_name: str, password: str):
    db = DbUtil(db_host, db_port, db_user, db_passwd, db_database)

    # 判断该username是否已经存在
    sql = f"select username from mailbox where username='{mail_name}'"
    user = db.query_one(sql)
    if user is not None:
        print(f'Debugging: 邮箱 {mail_name} 已经存在, 不能重复创建')
        del db
        return
    del db

    # 通过脚本创建邮箱账户
    ssh = SshUtil(ssh_host, ssh_username, ssh_password)
    ssh.execute_shell_command(
        f"bash /home/yanliang/iRedMail/tools/create_mail_user_SQL.sh '{mail_name}' '{password}'"
        f" > /tmp/create_a_new_mail_user.sql")
    ssh.execute_shell_command("mysql -uroot -p111111 vmail -e 'source /tmp/create_a_new_mail_user.sql'")
    ssh.execute_shell_command("rm /tmp/create_a_new_mail_user.sql")
    del ssh


"""批量创建账户"""


def create_multiple_mail_user(mail_name_list: list):
    db = DbUtil(db_host, db_port, db_user, db_passwd, db_database)

    for mail_name in mail_name_list:
        # 判断该username是否已经存在
        sql = f"select username from mailbox where username='{mail_name}'"
        user = db.query_one(sql)
        if user is not None:
            mail_name_list.remove(mail_name)
            print(f'Debugging: 邮箱 {mail_name} 已经存在, 不能重复创建')
            continue
    del db

    # 通过脚本创建邮箱账户
    default_password = "111111"
    ssh = SshUtil(ssh_host, ssh_username, ssh_password)
    is_first = True
    for mail_name in mail_name_list:
        if is_first:
            ssh.execute_shell_command(
                f"bash /home/yanliang/iRedMail/tools/create_mail_user_SQL.sh '{mail_name}' '{default_password}' > "
                f"/tmp/create_multiple_mail_user.sql")
            is_first = False
            continue

        ssh.execute_shell_command(
            f"bash /home/yanliang/iRedMail/tools/create_mail_user_SQL.sh '{mail_name}' '{default_password}' >> "
            f"/tmp/create_multiple_mail_user.sql")

    ssh.execute_shell_command("mysql -uroot -p111111 vmail -e 'source /tmp/create_multiple_mail_user.sql'")
    ssh.execute_shell_command("rm /tmp/create_multiple_mail_user.sql")
    del ssh


