"""预约借阅：用户预约 / 取消 / 归还 / 我的记录（含到期自动提醒）。"""
from datetime import datetime

from flask import Blueprint, current_app, g, jsonify, request

from models import Book, Reservation, db, recalc_available
from utils.mail import send_due_remind
from utils.security import auth_required

bp = Blueprint("reservations", __name__, url_prefix="/api/reservations")


def check_and_remind():
    """对「1 天内到期或已逾期且尚未提醒」的借阅记录自动发送一封提醒邮件。"""
    rows = Reservation.query.filter_by(status="borrowed", reminded=False).all()
    for r in rows:
        if not r.due_date:
            continue
        remaining = (r.due_date - datetime.now()).total_seconds()
        if remaining <= 24 * 3600:  # 到期前 1 天内或已逾期
            try:
                send_due_remind(
                    r.user.email, r.user.username, r.book.title,
                    r.due_date.strftime("%Y-%m-%d %H:%M"), remaining < 0,
                )
                r.reminded = True
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                current_app.logger.warning("到期提醒邮件发送失败（reservation=%s）: %s", r.id, e)


@bp.post("")
@auth_required
def reserve():
    data = request.get_json(silent=True) or {}
    book = db.session.get(Book, data.get("book_id") or 0)
    if not book:
        return jsonify(message="图书不存在"), 404
    if book.is_online:
        return jsonify(message="在线图书无需借阅"), 400
    exists = (
        Reservation.query.filter_by(user_id=g.current_user.id, book_id=book.id)
        .filter(Reservation.status.in_(["pending", "borrowed"]))
        .first()
    )
    if exists:
        return jsonify(message="您已预约或正在借阅该书"), 400
    if book.available_copies <= 0:
        return jsonify(message="该书暂无可借数量"), 400
    db.session.add(Reservation(user_id=g.current_user.id, book_id=book.id, status="pending"))
    recalc_available(book)
    db.session.commit()
    return jsonify(message="预约成功，请等待管理员审核")


@bp.get("/mine")
@auth_required
def mine():
    check_and_remind()
    rows = (
        Reservation.query.filter_by(user_id=g.current_user.id)
        .order_by(Reservation.reserved_at.desc())
        .all()
    )
    return jsonify(reservations=[r.to_dict() for r in rows])


@bp.post("/<int:rid>/cancel")
@auth_required
def cancel(rid):
    r = db.session.get(Reservation, rid)
    if not r or r.user_id != g.current_user.id:
        return jsonify(message="记录不存在"), 404
    if r.status != "pending":
        return jsonify(message="当前状态不可取消"), 400
    r.status = "cancelled"
    recalc_available(r.book)
    db.session.commit()
    return jsonify(message="已取消预约")


@bp.post("/<int:rid>/return")
@auth_required
def give_back(rid):
    r = db.session.get(Reservation, rid)
    if not r or r.user_id != g.current_user.id:
        return jsonify(message="记录不存在"), 404
    if r.status != "borrowed":
        return jsonify(message="当前状态不可归还"), 400
    r.status = "returned"
    recalc_available(r.book)
    db.session.commit()
    return jsonify(message="归还成功，感谢阅读")
