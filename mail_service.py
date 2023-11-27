import imaplib
import email
from db_utils import DbUtil
from ssh_utils import SshUtil
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
from email.header import decode_header
import datetime
from unified_logger import UnifiedLogger


log = UnifiedLogger()

# ===========================================================
# ===============        config       =======================
# ===========================================================


# IMAP Server and User Information
mail_server = '192.168.124.128'
# mail_username = 'a1@nsyy.com'
# mail_password = "Nsyy.2015"
mail_username = 'postmaster@nsyy.com'
mail_password = '111111'
# mail_mailbox = 'Sent'  # You can change this to the mailbox you want to read.
mail_mailbox = 'INBOX'  # You can change this to the mailbox you want to read.

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


"""发送邮件"""


def send_email(*args):
    # Sender and recipient email addresses
    sender_email = args[0]
    recipient_emails = [args[1]]
    cc_emails = [args[2]]
    bcc_emails = [args[3]]

    # Create a message container
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = ", ".join(recipient_emails)
    msg["Cc"] = ", ".join(cc_emails)
    msg["Bcc"] = ", ".join(bcc_emails)
    msg["Subject"] = args[4] + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Add a custom "Delivery-Data" header
    msg.add_header('X-Contact-Groups', '[1, 2]')

    # # Set the "Disposition-Notification-To" header  已读回执
    # msg["Disposition-Notification-To"] = sender_email

    # Add the email body
    msg.attach(MIMEText(args[5], "plain"))

    attachment = args[6]
    if attachment is not None:
        filename = attachment.filename
        # 获取上传文件的MIME类型
        mime_type = attachment.mimetype
        if mime_type.startswith('image/'):
            # 文件是图像
            image = MIMEImage(attachment.read())
            image.add_header("Content-ID", "<image1>")
            image.add_header('Content-Disposition', 'attachment', filename=filename)
            msg.attach(image)

        else:
            # 文件是其他类型
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", 'attachment', filename=filename)
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

        log.info("Email sent successfully")
    except smtplib.SMTPException as e:
        log.info(f"Failed to send the email: {e}")
    except Exception as e:
        log.info(f"An error occurred: {e}")

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


"""读取邮件列表"""


def read_mail_list(pers_id: int, email_account: str, page_size: int, page_number: int):
    # TODO 根据 pers id 和 email account 查询账户密码
    # Connect to the IMAP server
    mail = __login_mail(mail_server, email_account, "111111")

    # Search for all emails in the mailbox. use UNSEEN search unread mail
    status, email_ids = mail.search(None, "ALL")

    email_list = []
    if status == "OK":
        email_id_list = email_ids[0].split()
        # Sort the email IDs in descending order (newest first)
        email_id_list.reverse()

        # Calculate the range of email IDs for the current page
        start_email_id = 1 + (page_size * (page_number - 1))
        end_email_id = page_size * page_number
        log.info(f"email count: {len(email_id_list)}, page_size: {page_size}, page_number: {page_number} \n")

        # Limit the number of emails to retrieve to the latest 5
        email_id_list = email_id_list[start_email_id - 1:end_email_id]

        # Loop through the email IDs and fetch the email details
        for email_id in email_id_list:
            ret, err = __read_mail_by_mail_id(mail, email_id)
            if ret is not None:
                email_list.append(ret)

    # Close the mailbox and log out
    __close_mail(mail)

    return email_list


# 下载附件

def fetch_attachment(pers_id: int, email_account: str, email_id: str):
    # Connect to the IMAP server
    mail = __login_mail(mail_server, email_account, "111111")

    # Fetch the email based on the ID.  peek 防止修改邮件已读状态
    result, message_data = mail.fetch(email_id, '(BODY.PEEK[])')
    if result == "OK":
        # Parse the email message
        msg = email.message_from_bytes(message_data[0][1])
        # Extract email details
        subject, encoding = decode_header(msg.get("Subject"))[0]
        subject = subject.decode(encoding) if encoding else subject
        log.info("Subject              : {}".format(subject))

        for part in msg.walk():
            if part.get_content_maintype() == "multipart" or part.get("Content-Disposition") is None:
                continue
            filename = part.get_filename()
            data = part.get_payload(decode=True)
            yield filename, data

    # Close the mailbox and log out
    __close_mail(mail)


"""登陆邮件服务器"""


def __login_mail(mail_server: str, mail_account: str, mail_password: str):
    # Connect to the IMAP server
    mail = imaplib.IMAP4_SSL(mail_server)
    log.debug(f"Successed to connect to the IMAP server {imap_server} .")

    # Login to the email account
    status, _ = mail.login(mail_account, mail_password)
    if status != "OK":
        log.warning(f" {mail_account} Login failed. Please check your credentials.")
        mail.logout()
        return "Fail", f" {mail_account} Login failed. Please check your credentials."
    log.debug(f" {mail_account} Login successed. ")

    # list mailboxes
    status, data = mail.list()
    if status != "OK":
        log.warning("Failed to get mail list.")
        mail.logout()
        return "Fail", "Failed to get mail list."
    log.debug(f'mailboxes: {data}')

    # Select the mailbox you want to read, 使用 select() 方法选择要读取的邮件文件夹
    status, _ = mail.select(mail_mailbox)
    if status != "OK":
        log.warning("Failed to select the mailbox.")
        mail.logout()
        return "Fail", "Failed to select the mailbox."
    log.debug(f"select {mail_mailbox}")

    return "OK", mail


"""通过 email id 读取邮件"""


def __read_mail_by_mail_id(mail, email_id):
    # Fetch the email based on the ID.  peek 防止修改邮件已读状态
    result, message_data = mail.fetch(email_id, '(FLAGS BODY.PEEK[])')
    if result == "OK":
        # Extract email flags and Check if the email is marked as unread
        flags = message_data[0][0].decode("utf-8").split("FLAGS (")[1].split(")")[0]
        is_unread = "\\Seen" not in flags

        # Parse the email message
        msg = email.message_from_bytes(message_data[0][1])
        # Extract email details
        subject, encoding = decode_header(msg.get("Subject"))[0]
        subject = subject.decode(encoding) if encoding else subject

        # Print the email details
        log.debug(f"================== mail {email_id} ==================")
        log.debug("Unread               : {}".format('Yes' if is_unread else 'No'))
        log.debug("Email ID             : {}".format(email_id))
        log.debug("Subject              : {}".format(subject))
        log.debug("From                 : {}".format(msg.get("From")))
        log.debug("To                   : {}".format(msg.get("To")))
        log.debug("CC                   : {}".format(msg.get("CC")))
        log.debug("Bcc                  : {}".format(msg.get("Bcc")))
        log.debug("Priority             : {}".format(msg.get("Priority")))
        log.debug("ReplyToList          : {}".format(msg.get("ReplyToList")))
        log.debug("Date                 : {}".format(msg.get("Date")))
        log.debug("Contact Groups       : {}".format(msg.get("X-Contact-Groups")))

        # Extract attachments
        attachments = []
        for part in msg.walk():
            if part.get_content_maintype() == "multipart" or part.get("Content-Disposition") is None:
                continue
            filename = part.get_filename()
            if filename:
                attachments.append(filename)
        log.debug("Attachments count    : {}".format(len(attachments)))
        for attachment in attachments:
            print(attachment)

        # Get the email content
        body = None
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    log.debug("Message:")
                    # print(body)
        else:
            body = msg.get_payload(decode=True).decode()
            log.debug("Message:")
            # print(body)
        return {
            "id": email_id.decode("utf-8"),
            "Unread": True if is_unread else False,
            "Subject": subject,
            "From": msg.get("From"),
            "To": msg.get("To"),
            "CC": msg.get("CC"),
            "Bcc": msg.get("Bcc"),
            "ReplyToList": msg.get("ReplyToList"),
            "Date": msg.get("Date"),
            "ContactGroups": msg.get("X-Contact-Group"),
            "attachments": attachments,
            "body": body,
        }, None
    return None, f"read email {email_id} failed"


"""关闭邮箱相关连接"""


def __close_mail(mail):
    # Close the mailbox and log out
    log.debug("Close the mailbox and log out")
    mail.close()
    mail.logout()


# ===========================================================
# ===============     user manager    =======================
# ===========================================================

"""停用账户"""


def deactivate_account(deactivate_username: str):
    db = DbUtil(db_host, db_port, db_user, db_passwd, db_database)

    sql = f"update mailbox set active=0 where username='{deactivate_username}'"
    db.execute(sql, need_commit=True)

    del db


"""创建单个账户"""


def create_a_new_mail_user(mail_name: str, password: str):
    db = DbUtil(db_host, db_port, db_user, db_passwd, db_database)

    # 判断该username是否已经存在
    sql = f"select username from mailbox where username='{mail_name}'"
    user = db.query_one(sql)
    if user is not None:
        log.warning(f'邮箱 {mail_name} 已经存在, 不能重复创建')
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
            log.warning(f'邮箱 {mail_name} 已经存在, 不能重复创建')
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


"""修改密码"""


def update_mail_user_password(mail_name: str, new_password: str):
    db = DbUtil(db_host, db_port, db_user, db_passwd, db_database)

    # 判断该username是否已经存在
    sql = f"select username from mailbox where username='{mail_name}'"
    user = db.query_one(sql)
    if user is None:
        log.warning(f'邮箱 {mail_name} 不存在，不能执行更新密码操作')
        return

    encrypted_password = generate_encrypted_password(new_password)
    sql = f"UPDATE mailbox SET password='{encrypted_password}' WHERE username='{mail_name}';"
    db.execute(sql, need_commit=True)

    del db


DEFAULT_PASSWORD_SCHEME = 'SSHA512'
HASHES_WITHOUT_PREFIXED_PASSWORD_SCHEME = ['NTLM']

"""加密密码"""


def generate_encrypted_password(plain_password, scheme=None):
    # TODO scheme 可选值： SSHA512 BCRYPT， 默认使用 ssha512
    ssh = SshUtil(ssh_host, ssh_username, ssh_password)
    output = ssh.execute_shell_command(f"cd /home/yanliang; doveadm pw -s 'ssha512' -p '{plain_password}'")
    print(f"generate_encrypted_password plain_password: {plain_password}, encrypted_password: {output}")

    del ssh
    return output


# ===========================================================
# =============  contact group manager  =====================
# ===========================================================


"""创建分组"""


def create_contact_group(*args):
    # db config
    db_host = '127.0.0.1'
    db_user = 'root'
    db_passwd = 'gyl.2015'
    db_database = 'mail'
    db = DbUtil(db_host, db_port, db_user, db_passwd, db_database)

    sql = "INSERT INTO contactgroups (contactgroup_id, name, pers_id, changed, is_public) " \
          "VALUES (%d, %s, %d, %s, %d)"
    dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    val = (args[0], args[1], args[2], dt, args[3])
    db.execute(sql, val, need_commit=True)

    del db


"""更新分组"""


def update_contact_group(*args):
    # db config
    db_host = '127.0.0.1'
    db_user = 'root'
    db_passwd = 'gyl.2015'
    db_database = 'mail'
    db = DbUtil(db_host, db_port, db_user, db_passwd, db_database)

    sql = "UPDATE contactgroups SET name = %s, changed = %s, is_public = %d WHERE contactgroup_id = %d"
    dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    val = (args[0], dt, args[1], dt, args[2])
    db.execute(sql, val, need_commit=True)

    del db


"""根据用户ID查询分组"""


def get_contact_group_by_persid(pers_id):
    # db config
    db_host = '127.0.0.1'
    db_user = 'root'
    db_passwd = 'gyl.2015'
    db_database = 'mail'
    db = DbUtil(db_host, db_port, db_user, db_passwd, db_database)

    sql = f"select * from contactgroups where pers_id='{pers_id}'"
    contactgroups = db.query_all(sql)

    del db
    return contactgroups


"""删除分组"""


def delete_contact_group_by_id(contactgroup_id):
    # db config
    db_host = '127.0.0.1'
    db_user = 'root'
    db_passwd = 'gyl.2015'
    db_database = 'mail'
    db = DbUtil(db_host, db_port, db_user, db_passwd, db_database)

    # 删除分组记录 一条
    sql = f"DELETE FROM contactgroups WHERE contactgroup_id = '{contactgroup_id}'"
    db.execute(sql, need_commit=True)

    # 删除分组成员 多条
    sql = f"DELETE FROM contactgroupmembers WHERE contactgroup_id = '{contactgroup_id}'"
    db.execute(sql, need_commit=True)

    del db


"""向分组添加成员"""


def add_contact_group_member(*args):
    # db config
    db_host = '127.0.0.1'
    db_user = 'root'
    db_passwd = 'gyl.2015'
    db_database = 'mail'
    db = DbUtil(db_host, db_port, db_user, db_passwd, db_database)

    contactgroup_id = args[0]
    pers_id = args[1]
    dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sql = "INSERT INTO contactgroupmembers (contactgroup_id, pers_id, changed) VALUES (%d, %d, %s)"
    val = (contactgroup_id, pers_id, dt)
    db.execute(sql, val, need_commit=True)

    del db


"""从分组移除成员"""


def remove_contact_group_member(*args):
    # db config
    db_host = '127.0.0.1'
    db_user = 'root'
    db_passwd = 'gyl.2015'
    db_database = 'mail'
    db = DbUtil(db_host, db_port, db_user, db_passwd, db_database)

    contactgroup_id = args[0]
    pers_id = args[1]

    sql = f"DELETE FROM contactgroupmembers WHERE contactgroup_id = '{contactgroup_id}', pers_id = '{pers_id}'"
    db.execute(sql, need_commit=True)

    del db
