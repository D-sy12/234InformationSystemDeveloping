"""图书管理系统后端入口。

启动：python app.py   （http://127.0.0.1:5000）
首次启动会自动建库、建表、创建管理员账号并写入样例图书。
"""
import pymysql
from flask import Flask
from flask_cors import CORS
from werkzeug.security import generate_password_hash

from config import Config
from models import Book, User, db

SEED_BOOKS = [
    # 在线图书（全文由 scripts/download_books.py 下载）
    dict(title="红楼梦", author="曹雪芹", category="古典文学", cover_url="/static/covers/hongloumeng.svg", description="中国古典四大名著之首，章回体长篇小说", is_online=True, online_url="/static/books/hongloumeng.txt"),
    dict(title="西游记", author="吴承恩", category="古典文学", cover_url="/static/covers/xiyouji.svg", description="神魔章回体长篇小说", is_online=True, online_url="/static/books/xiyouji.txt"),
    dict(title="三国演义", author="罗贯中", category="古典文学", cover_url="/static/covers/sanguoyanyi.svg", description="历史演义小说经典", is_online=True, online_url="/static/books/sanguoyanyi.txt"),
    dict(title="水浒传", author="施耐庵", category="古典文学", cover_url="/static/covers/shuihuzhuan.svg", description="英雄传奇章回体长篇小说", is_online=True, online_url="/static/books/shuihuzhuan.txt"),
    dict(title="Pride and Prejudice", author="Jane Austen", category="英文经典", cover_url="/static/covers/pride-and-prejudice.jpg", description="Classic romance novel", is_online=True, online_url="/static/books/pride-and-prejudice.txt"),
    dict(title="Alice's Adventures in Wonderland", author="Lewis Carroll", category="英文经典", cover_url="/static/covers/alice-in-wonderland.jpg", description="Children's fantasy novel", is_online=True, online_url="/static/books/alice-in-wonderland.txt"),
    dict(title="Frankenstein", author="Mary Shelley", category="英文经典", cover_url="/static/covers/frankenstein.jpg", description="Gothic science fiction", is_online=True, online_url="/static/books/frankenstein.txt"),
    dict(title="The Adventures of Sherlock Holmes", author="Arthur Conan Doyle", category="英文经典", cover_url="/static/covers/sherlock-holmes.jpg", description="Detective short stories", is_online=True, online_url="/static/books/sherlock-holmes.txt"),
    dict(title="Moby Dick", author="Herman Melville", category="英文经典", cover_url="/static/covers/moby-dick.jpg", description="Adventure of the whaling ship Pequod", is_online=True, online_url="/static/books/moby-dick.txt"),
    dict(title="A Tale of Two Cities", author="Charles Dickens", category="英文经典", cover_url="/static/covers/a-tale-of-two-cities.jpg", description="Historical novel of the French Revolution", is_online=True, online_url="/static/books/a-tale-of-two-cities.txt"),
    # 实体图书（供预约借阅）
    dict(title="数据库系统概论", author="王珊", category="教材", cover_url="/static/covers/db-system.svg", description="数据库经典教材", is_online=False, total_copies=5, available_copies=5),
    dict(title="算法导论", author="Thomas H. Cormen", category="计算机科学", cover_url="/static/covers/introduction-to-algorithms.svg", description="算法领域权威著作", is_online=False, total_copies=3, available_copies=3),
    dict(title="深入理解计算机系统", author="Randal E. Bryant", category="计算机科学", cover_url="/static/covers/csapp.svg", description="CSAPP，程序员必修", is_online=False, total_copies=4, available_copies=4),
    dict(title="计算机网络：自顶向下方法", author="James F. Kurose", category="计算机科学", cover_url="/static/covers/computer-networking.svg", description="计算机网络经典教材", is_online=False, total_copies=3, available_copies=3),
    dict(title="现代操作系统", author="Andrew S. Tanenbaum", category="计算机科学", cover_url="/static/covers/modern-operating-systems.svg", description="操作系统权威教材", is_online=False, total_copies=2, available_copies=2),
]


def ensure_database():
    """数据库不存在时自动创建（需要 .env 里的账号有建库权限）。"""
    try:
        conn = pymysql.connect(
            host=Config.DB_HOST, port=Config.DB_PORT,
            user=Config.DB_USER, password=Config.DB_PASSWORD, charset="utf8mb4",
        )
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{Config.DB_NAME}` "
                "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[警告] 自动创建数据库失败：{e}（请确认 MySQL 已启动且 .env 配置正确）")


def ensure_admin():
    """无管理员时自动创建（账号密码来自 .env，默认 admin/admin）。"""
    username, password = Config.ADMIN_USERNAME, Config.ADMIN_PASSWORD
    if User.query.filter_by(role="admin").first():
        return
    user = User.query.filter_by(username=username).first()
    if user:
        user.role = "admin"
        user.password_hash = generate_password_hash(password)
        print(f"[初始化] 已将已有用户 {username} 提升为管理员")
    else:
        db.session.add(
            User(
                username=username,
                email=f"{username}@library.local",
                password_hash=generate_password_hash(password),
                role="admin",
            )
        )
        print(f"[初始化] 已创建管理员账号：{username} / {password}")
    db.session.commit()


def seed_books():
    if Book.query.count() > 0:
        return
    for item in SEED_BOOKS:
        db.session.add(Book(**item))
    db.session.commit()
    print(f"[初始化] 已写入 {len(SEED_BOOKS)} 本样例图书")


def create_app():
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    app.config.from_object(Config)
    db.init_app(app)
    CORS(app)

    from routes.admin import bp as admin_bp
    from routes.auth import bp as auth_bp
    from routes.books import bp as books_bp
    from routes.reservations import bp as reservations_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(reservations_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        ensure_database()
        db.create_all()
        ensure_admin()
        seed_books()
    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
