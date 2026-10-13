"""管理员接口：图书管理 / 借阅管理 / 催还邮件 / 统计。"""
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from models import BORROW_DAYS, Book, Reservation, db, recalc_available
from routes.reservations import check_and_remind
from utils.mail import send_due_remind
from utils.security import admin_required

bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@bp.get("/reservations")
@admin_required
def all_reservations():
    check_and_remind()  # 先执行到期自动提醒，再返回列表
    rows = Reservation.query.order_by(Reservation.reserved_at.desc()).all()
    return jsonify(reservations=[r.to_dict(with_user=True) for r in rows])


@bp.post("/reservations/<int:rid>/approve")
@admin_required
def approve(rid):
    r = db.session.get(Reservation, rid)
    if not r:
        return jsonify(message="记录不存在"), 404
    if r.status != "pending":
        return jsonify(message="仅待审核的预约可以出借"), 400
    if r.book.available_copies <= 0:
        return jsonify(message="该书暂无可借数量"), 400
    r.status = "borrowed"
    r.borrowed_at = datetime.now()
    r.due_date = r.borrowed_at + timedelta(days=BORROW_DAYS)
    r.reminded = False
    recalc_available(r.book)
    db.session.commit()
    return jsonify(message=f"已出借，应还时间 {r.due_date:%Y-%m-%d %H:%M}")


@bp.post("/reservations/<int:rid>/returned")
@admin_required
def mark_returned(rid):
    r = db.session.get(Reservation, rid)
    if not r:
        return jsonify(message="记录不存在"), 404
    if r.status != "borrowed":
        return jsonify(message="仅借阅中的记录可以标记归还"), 400
    r.status = "returned"
    recalc_available(r.book)
    db.session.commit()
    return jsonify(message="已标记归还")


@bp.post("/reservations/<int:rid>/remind")
@admin_required
def remind(rid):
    r = db.session.get(Reservation, rid)
    if not r or r.status != "borrowed":
        return jsonify(message="记录不存在或当前状态不可提醒"), 404
    remaining = (r.due_date - datetime.now()).total_seconds()
    try:
        send_due_remind(
            r.user.email, r.user.username, r.book.title,
            r.due_date.strftime("%Y-%m-%d %H:%M"), remaining < 0,
        )
    except Exception as e:
        return jsonify(message=f"邮件发送失败：{e}"), 500
    r.reminded = True
    db.session.commit()
    return jsonify(message=f"催还邮件已发送至 {r.user.email}")


@bp.post("/books")
@admin_required
def add_book():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify(message="书名不能为空"), 400
    is_online = bool(data.get("is_online"))
    try:
        total = int(data.get("total_copies") or 0)
    except (TypeError, ValueError):
        return jsonify(message="馆藏数量格式不正确"), 400
    if not is_online and total <= 0:
        return jsonify(message="实体图书需要设置馆藏数量"), 400
    book = Book(
        title=title,
        author=(data.get("author") or "").strip(),
        isbn=(data.get("isbn") or "").strip(),
        category=(data.get("category") or "未分类").strip(),
        cover_url=(data.get("cover_url") or "").strip(),
        description=(data.get("description") or "").strip(),
        is_online=is_online,
        online_url=(data.get("online_url") or "").strip(),
        total_copies=0 if is_online else total,
        available_copies=0 if is_online else total,
    )
    db.session.add(book)
    db.session.commit()
    return jsonify(message="图书添加成功", book={"id": book.id})


@bp.put("/books/<int:book_id>/copies")
@admin_required
def update_copies(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify(message="图书不存在"), 404
    if book.is_online:
        return jsonify(message="在线图书没有馆藏数量"), 400
    data = request.get_json(silent=True) or {}
    try:
        total = int(data.get("total_copies"))
    except (TypeError, ValueError):
        return jsonify(message="数量格式不正确"), 400
    if total < 0:
        return jsonify(message="数量不能为负数"), 400
    book.total_copies = total
    recalc_available(book)
    db.session.commit()
    return jsonify(
        message="馆藏数量已更新",
        total_copies=book.total_copies,
        available_copies=book.available_copies,
    )


@bp.get("/stats")
@admin_required
def stats():
    categories = (
        Book.query.with_entities(Book.category, func.count(Book.id))
        .group_by(Book.category)
        .all()
    )
    status_rows = (
        Reservation.query.with_entities(Reservation.status, func.count(Reservation.id))
        .group_by(Reservation.status)
        .all()
    )
    status_dist = {s: c for s, c in status_rows}
    overdue = (
        Reservation.query.filter(Reservation.status == "borrowed", Reservation.due_date < datetime.now())
        .count()
    )
    top_rows = (
        Reservation.query.join(Book, Reservation.book_id == Book.id)
        .with_entities(Book.title, func.count(Reservation.id))
        .group_by(Book.id, Book.title)
        .order_by(func.count(Reservation.id).desc())
        .limit(5)
        .all()
    )
    return jsonify(
        categories=[{"name": c or "未分类", "count": n} for c, n in categories],
        status_dist={**status_dist, "overdue": overdue},
        top_borrowed=[{"title": t, "count": n} for t, n in top_rows],
    )
