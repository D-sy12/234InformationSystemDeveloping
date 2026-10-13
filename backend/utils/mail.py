"""QQ 邮箱 SMTP 发信（注册验证码 / 催还邮件）。"""
import random
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr

from flask import current_app


def gen_code():
    return f"{random.randint(0, 999999):06d}"


def _send(to, subject, body):
    cfg = current_app.config
    if not cfg.get("SMTP_USER") or not cfg.get("SMTP_PASSWORD"):
        raise RuntimeError("SMTP 未配置：请在 backend/.env 中填写 SMTP_USER 和 SMTP_PASSWORD（QQ 邮箱授权码）")
    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = formataddr(("图书管理系统", cfg["SMTP_USER"]))
    msg["To"] = formataddr(("读者", to))
    msg["Subject"] = subject
    with smtplib.SMTP_SSL(cfg["SMTP_HOST"], cfg["SMTP_PORT"], timeout=15) as server:
        server.login(cfg["SMTP_USER"], cfg["SMTP_PASSWORD"])
        server.sendmail(cfg["SMTP_USER"], [to], msg.as_string())


def send_register_code(email, code):
    minutes = current_app.config["MAIL_CODE_EXPIRE_MINUTES"]
    body = (
        "您好！\n\n"
        f"您正在注册图书管理系统，本次验证码为：{code}\n\n"
        f"验证码 {minutes} 分钟内有效，请勿泄露给他人。\n"
        "如非本人操作，请忽略本邮件。"
    )
    _send(email, "图书管理系统 - 注册验证码", body)


def send_due_remind(email, username, book_title, due_str, overdue):
    if overdue:
        subject = "图书管理系统 - 逾期催还提醒"
        body = (
            f"{username} 您好！\n\n"
            f"您借阅的《{book_title}》已于 {due_str} 到期，目前仍未归还。\n"
            "请尽快到馆归还，或联系管理员说明情况。感谢您的配合！"
        )
    else:
        subject = "图书管理系统 - 借阅到期提醒"
        body = (
            f"{username} 您好！\n\n"
            f"您借阅的《{book_title}》将于 {due_str} 到期。\n"
            "请在到期前及时归还，以免产生逾期记录。"
        )
    _send(email, subject, body)
