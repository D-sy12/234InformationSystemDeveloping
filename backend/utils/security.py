"""JWT 生成/校验与登录鉴权装饰器。"""
from datetime import datetime, timedelta
from functools import wraps

import jwt
from flask import current_app, g, jsonify, request

from models import User, db


def create_token(user):
    payload = {
        "uid": user.id,
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(hours=current_app.config["JWT_EXPIRE_HOURS"]),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")


def decode_token(token):
    try:
        return jwt.decode(token, current_app.config["JWT_SECRET"], algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise ValueError("登录已过期，请重新登录")
    except Exception:
        raise ValueError("无效的登录凭证")


def _bearer():
    header = request.headers.get("Authorization", "")
    return header[7:] if header.startswith("Bearer ") else None


def current_user():
    """可选鉴权：返回登录用户或 None（不抛错）。"""
    token = _bearer()
    if not token:
        return None
    try:
        payload = decode_token(token)
    except ValueError:
        return None
    return db.session.get(User, payload.get("uid"))


def auth_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = _bearer()
        if not token:
            return jsonify(message="请先登录"), 401
        try:
            payload = decode_token(token)
        except ValueError as e:
            return jsonify(message=str(e)), 401
        user = db.session.get(User, payload.get("uid"))
        if not user:
            return jsonify(message="用户不存在"), 401
        g.current_user = user
        return fn(*args, **kwargs)

    return wrapper


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = _bearer()
        if not token:
            return jsonify(message="请先登录"), 401
        try:
            payload = decode_token(token)
        except ValueError as e:
            return jsonify(message=str(e)), 401
        user = db.session.get(User, payload.get("uid"))
        if not user:
            return jsonify(message="用户不存在"), 401
        if user.role != "admin":
            return jsonify(message="需要管理员权限"), 403
        g.current_user = user
        return fn(*args, **kwargs)

    return wrapper
