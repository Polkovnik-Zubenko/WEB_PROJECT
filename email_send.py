import smtplib
import random
from email.mime.text import MIMEText


def send_email(user_email):
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
        server.login(sender, password)
        msg = MIMEText(template, "html")
        msg["From"] = sender
        msg["To"] = user_email
        msg["Subject"] = "Восстановление пароля"
        server.sendmail(sender, user_email, msg.as_string())
        return "success"
    except Exception as f:
        return f
