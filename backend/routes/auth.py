"""注册 / 登录 / 邮箱验证码。"""
import re
from datetime import datetime, timedelta

from flask import Blueprint, current_app, g, jsonify, request
from sqlalchemy import or_
from werkzeug.security import check_password_hash, generate_password_hash

from models import EmailCode, User, db
from utils.mail import gen_code, send_register_code
from utils.security import auth_required, create_token

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")


@bp.post("/send-code")
def send_code():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    if not EMAIL_RE.match(email):
        return jsonify(message="邮箱格式不正确"), 400
    if User.query.filter_by(email=email).first():
        return jsonify(message="该邮箱已被注册"), 400
    latest = (
        EmailCode.query.filter_by(email=email, purpose="register")
        .order_by(EmailCode.created_at.desc())
        .first()
    )
    if latest and (datetime.now() - latest.created_at).total_seconds() < 60:
        return jsonify(message="验证码发送过于频繁，请 1 分钟后再试"), 429
    code = gen_code()
    db.session.add(
        EmailCode(
            email=email,
            code=code,
            purpose="register",
            expires_at=datetime.now() + timedelta(minutes=current_app.config["MAIL_CODE_EXPIRE_MINUTES"]),
        )
    )
    db.session.commit()
    try:
        send_register_code(email, code)
    except Exception as e:
        current_app.logger.error("发送邮件失败: %s", e)
        return jsonify(message=f"验证码邮件发送失败：{e}"), 500
    return jsonify(message="验证码已发送，请查收邮箱")


@bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    code = (data.get("code") or "").strip()

    if not (2 <= len(username) <= 20):
        return jsonify(message="用户名长度需为 2-20 个字符"), 400
    if not EMAIL_RE.match(email):
        return jsonify(message="邮箱格式不正确"), 400
    if len(password) < 6:
        return jsonify(message="密码至少 6 位"), 400
    if User.query.filter_by(username=username).first():
        return jsonify(message="用户名已存在"), 400
    if User.query.filter_by(email=email).first():
        return jsonify(message="该邮箱已被注册"), 400

    record = (
        EmailCode.query.filter_by(email=email, purpose="register", used=False)
        .order_by(EmailCode.created_at.desc())
        .first()
    )
    if not record or record.code != code:
        return jsonify(message="邮箱验证码错误"), 400
    if record.expires_at < datetime.now():
        return jsonify(message="验证码已过期，请重新获取"), 400

    record.used = True
    db.session.add(User(username=username, email=email, password_hash=generate_password_hash(password)))
    db.session.commit()
    return jsonify(message="注册成功，请登录")


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    account = (data.get("account") or "").strip()
    password = data.get("password") or ""
    user = User.query.filter(or_(User.username == account, User.email == account)).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify(message="用户名或密码错误"), 400
    return jsonify(message="登录成功", token=create_token(user), user=user.to_dict())


@bp.get("/me")
@auth_required
def me():
    return jsonify(user=g.current_user.to_dict())
