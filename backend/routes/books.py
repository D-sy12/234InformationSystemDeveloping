"""图书浏览：游客仅可见在线图书，登录后可见全部。"""
from flask import Blueprint, jsonify, request

from models import Book, db
from utils.security import current_user

bp = Blueprint("books", __name__, url_prefix="/api/books")


def book_dict(b):
    return b.to_dict()


@bp.get("")
def list_books():
    user = current_user()
    query = Book.query
    if not user:  # 游客只能浏览在线图书
        query = query.filter(Book.is_online.is_(True))
    type_ = request.args.get("type")
    if type_ == "online":
        query = query.filter(Book.is_online.is_(True))
    elif type_ == "physical":
        query = query.filter(Book.is_online.is_(False))
    category = request.args.get("category")
    if category:
        query = query.filter(Book.category == category)
    keyword = (request.args.get("q") or "").strip()
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(Book.title.like(like) | Book.author.like(like))
    books = query.order_by(Book.id.desc()).all()
    categories = [c for (c,) in Book.query.with_entities(Book.category).distinct() if c]
    return jsonify(books=[book_dict(b) for b in books], categories=categories)


@bp.get("/<int:book_id>")
def book_detail(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify(message="图书不存在"), 404
    if not book.is_online and not current_user():
        return jsonify(message="实体图书需要登录后查看"), 401
    return jsonify(book=book_dict(book))
