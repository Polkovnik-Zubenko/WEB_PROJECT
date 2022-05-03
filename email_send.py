import smtplib
import random
from email.mime.text import MIMEText


def create_secret_key():
    itog_secret_key = random.randint(1000000, 9999999)
    return str(itog_secret_key)


def send_email(user_email, itog_secret_key):
    sender = "association.olymp.programmers@gmail.com"
    password = 'qwe9032gn'

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    try:
        with open("./templates/email.html") as file:
            template = file.read()

    except IOError:
        return "file dos not found"
    try:
        print(type(template))

        replaced_template = template.replace('secret_key', itog_secret_key)
        server.login(sender, password)
        msg = MIMEText(replaced_template, "html")
        msg["From"] = sender
        msg["To"] = user_email
        msg["Subject"] = "Восстановление пароля"
        server.sendmail(sender, user_email, msg.as_string())
        return "success"
    except Exception as f:
        print(f)
