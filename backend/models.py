"""数据模型与通用序列化工具。"""
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

BORROW_DAYS = 7  # 借阅上限（天）
DUE_SOON_SECONDS = 24 * 3600  # 到期前 1 天开始提醒


def fmt(dt):
    """datetime -> 前端友好的 ISO 字符串（本地时区，T 分隔）。"""
    return dt.strftime("%Y-%m-%dT%H:%M:%S") if dt else None


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("user", "admin"), nullable=False, default="user")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "created_at": fmt(self.created_at),
        }


class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), default="")
    isbn = db.Column(db.String(20), default="")
    category = db.Column(db.String(50), default="")
    cover_url = db.Column(db.String(500), default="")
    description = db.Column(db.Text)
    is_online = db.Column(db.Boolean, nullable=False, default=False)
    online_url = db.Column(db.String(500), default="")
    total_copies = db.Column(db.Integer, default=0)
    available_copies = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "isbn": self.isbn,
            "category": self.category,
            "cover_url": self.cover_url,
            "description": self.description,
            "is_online": bool(self.is_online),
            "online_url": self.online_url,
            "total_copies": self.total_copies,
            "available_copies": self.available_copies,
            "created_at": fmt(self.created_at),
        }


class Reservation(db.Model):
    __tablename__ = "reservations"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False)
    book_id = db.Column(db.BigInteger, db.ForeignKey("books.id"), nullable=False)
    status = db.Column(
        db.Enum("pending", "borrowed", "returned", "cancelled", name="reservation_status"),
        nullable=False, default="pending",
    )
    reserved_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    borrowed_at = db.Column(db.DateTime)
    due_date = db.Column(db.DateTime)
    reminded = db.Column(db.Boolean, nullable=False, default=False)

    user = db.relationship("User", lazy="joined")
    book = db.relationship("Book", lazy="joined")

    def display_status(self):
        """borrowed 细分为：borrowed（正常）/ due_soon（1 天内到期）/ overdue（逾期）。"""
        if self.status != "borrowed" or not self.due_date:
            return self.status
        remaining = (self.due_date - datetime.now()).total_seconds()
        if remaining < 0:
            return "overdue"
        if remaining <= DUE_SOON_SECONDS:
            return "due_soon"
        return "borrowed"

    def to_dict(self, with_user=False):
        d = {
            "id": self.id,
            "status": self.status,
            "display_status": self.display_status(),
            "reserved_at": fmt(self.reserved_at),
            "borrowed_at": fmt(self.borrowed_at),
            "due_date": fmt(self.due_date),
            "reminded": bool(self.reminded),
            "book": {
                "id": self.book.id,
                "title": self.book.title,
                "author": self.book.author,
                "category": self.book.category,
                "cover_url": self.book.cover_url,
                "is_online": bool(self.book.is_online),
            },
        }
        if with_user:
            d["user"] = {
                "id": self.user.id,
                "username": self.user.username,
                "email": self.user.email,
            }
        return d


class EmailCode(db.Model):
    __tablename__ = "email_codes"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    email = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(6), nullable=False)
    purpose = db.Column(db.Enum("register", "reset"), default="register")
    used = db.Column(db.Boolean, nullable=False, default=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)


def recalc_available(book):
    """根据待审核 + 借阅中的记录数，重算实体书可借数量。"""
    active = Reservation.query.filter(
        Reservation.book_id == book.id,
        Reservation.status.in_(["pending", "borrowed"]),
    ).count()
    book.available_copies = max(0, book.total_copies - active)
