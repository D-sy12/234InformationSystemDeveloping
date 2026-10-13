"""下载公版图书全文与封面（纯标准库实现，无需安装依赖）。

- 图书全文：Project Gutenberg（公版书，无版权问题）
- 封面：优先 Open Library 真实封面（有 ISBN 的书），失败则生成渐变色 SVG 占位封面

运行：python scripts/download_books.py
输出：backend/static/books/*.txt、backend/static/covers/*、backend/static/book_manifest.json
"""
import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "backend" / "static"
BOOKS_DIR = STATIC / "books"
COVERS_DIR = STATIC / "covers"
UA = {"User-Agent": "Mozilla/5.0 (library-system-seed)"}

BOOKS = [
    {"slug": "hongloumeng", "title": "红楼梦", "author": "曹雪芹", "category": "古典文学", "gutenberg_id": 24264},
    {"slug": "xiyouji", "title": "西游记", "author": "吴承恩", "category": "古典文学", "gutenberg_id": 23962},
    {"slug": "sanguoyanyi", "title": "三国演义", "author": "罗贯中", "category": "古典文学", "gutenberg_id": 23950},
    {"slug": "shuihuzhuan", "title": "水浒传", "author": "施耐庵", "category": "古典文学", "gutenberg_id": 23863},
    {"slug": "pride-and-prejudice", "title": "Pride and Prejudice", "author": "Jane Austen", "category": "英文经典", "gutenberg_id": 1342, "isbn": "9780141439518"},
    {"slug": "alice-in-wonderland", "title": "Alice's Adventures in Wonderland", "author": "Lewis Carroll", "category": "英文经典", "gutenberg_id": 11, "isbn": "9780141439761"},
    {"slug": "frankenstein", "title": "Frankenstein", "author": "Mary Shelley", "category": "英文经典", "gutenberg_id": 84, "isbn": "9780140433623"},
    {"slug": "sherlock-holmes", "title": "The Adventures of Sherlock Holmes", "author": "Arthur Conan Doyle", "category": "英文经典", "gutenberg_id": 1661, "isbn": "9780141039339"},
    {"slug": "moby-dick", "title": "Moby Dick", "author": "Herman Melville", "category": "英文经典", "gutenberg_id": 2701, "isbn": "9780142437247"},
    {"slug": "a-tale-of-two-cities", "title": "A Tale of Two Cities", "author": "Charles Dickens", "category": "英文经典", "gutenberg_id": 98, "isbn": "9780141439600"},
]

PALETTE = [
    ("#667eea", "#764ba2"), ("#f093fb", "#f5576c"), ("#4facfe", "#00f2fe"),
    ("#43e97b", "#38f9d7"), ("#fa709a", "#fee140"), ("#30cfd0", "#330867"),
    ("#ff9a9e", "#a18cd1"), ("#5ee7df", "#b490ca"), ("#c471f5", "#fa71cd"),
    ("#f6d365", "#fda085"),
]


def fetch(url, timeout=120):
    req = Request(url, headers=UA)
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


_probe_cache = {}


def host_ok(url, timeout=6):
    """探测主机可达性；HTTPError（如 404）也算可达，只有连接失败/超时才算不可达。"""
    host = urlsplit(url).netloc
    if host not in _probe_cache:
        try:
            urlopen(Request(f"https://{host}/", headers=UA), timeout=timeout)
            _probe_cache[host] = True
        except HTTPError:
            _probe_cache[host] = True
        except (URLError, TimeoutError, OSError):
            _probe_cache[host] = False
    return _probe_cache[host]


def download_book(book):
    """下载图书全文，返回文件大小（字节）；失败返回 0。"""
    gid = book["gutenberg_id"]
    candidates = [
        f"https://www.gutenberg.org/ebooks/{gid}.txt.utf-8",
        f"https://www.gutenberg.org/files/{gid}/{gid}-0.txt",
        f"https://www.gutenberg.org/cache/epub/{gid}/pg{gid}.txt",
        # 国内可达的官方镜像（速度较慢但稳定）
        f"https://gutenberg.pglaf.org/cache/epub/{gid}/pg{gid}.txt",
    ]
    for url in candidates:
        if not host_ok(url):
            continue
        try:
            text = fetch(url).decode("utf-8", errors="ignore")
            # 去掉 Gutenberg 头尾声明
            start = text.find("*** START OF THE PROJECT GUTENBERG EBOOK")
            end = text.find("*** END OF THE PROJECT GUTENBERG EBOOK")
            if start != -1:
                text = text[text.find("\n", start) + 1:]
            if end != -1:
                text = text[:end]
            path = BOOKS_DIR / f"{book['slug']}.txt"
            path.write_text(text.strip() + "\n", encoding="utf-8")
            return path.stat().st_size
        except (HTTPError, URLError, TimeoutError, OSError):
            continue
    return 0


def make_cover_svg(title, author, idx):
    c1, c2 = PALETTE[idx % len(PALETTE)]
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="300" height="420">'
        '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0%" stop-color="{c1}"/><stop offset="100%" stop-color="{c2}"/>'
        '</linearGradient></defs>'
        '<rect width="300" height="420" fill="url(#g)"/>'
        '<rect x="18" y="18" width="264" height="384" fill="none" stroke="rgba(255,255,255,0.55)" stroke-width="2"/>'
        f'<text x="150" y="190" font-size="26" font-family="serif" fill="#ffffff" text-anchor="middle" dominant-baseline="middle">{escape(title)}</text>'
        f'<text x="150" y="250" font-size="16" font-family="sans-serif" fill="rgba(255,255,255,0.85)" text-anchor="middle">{escape(author)}</text>'
        '<text x="150" y="380" font-size="12" font-family="sans-serif" fill="rgba(255,255,255,0.6)" text-anchor="middle">LIBRARY</text>'
        '</svg>'
    )


def download_real_cover(book, slug):
    """按 ISBN 从 Open Library 拉取真实封面，成功返回文件名。"""
    isbn = book.get("isbn")
    if not isbn:
        return None
    cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg?default=false"
    if not host_ok(cover_url):
        return None
    try:
        data = fetch(cover_url, timeout=8)
        if len(data) < 1000:  # 太小说明是默认占位图
            return None
        (COVERS_DIR / f"{slug}.jpg").write_bytes(data)
        return f"{slug}.jpg"
    except (HTTPError, URLError, TimeoutError, OSError):
        return None


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    BOOKS_DIR.mkdir(parents=True, exist_ok=True)
    COVERS_DIR.mkdir(parents=True, exist_ok=True)
    manifest = []
    updates = []
    for idx, book in enumerate(BOOKS):
        slug = book["slug"]
        size = download_book(book)
        cover_file = f"{slug}.svg"
        (COVERS_DIR / cover_file).write_text(make_cover_svg(book["title"], book["author"], idx), encoding="utf-8")
        real = download_real_cover(book, slug)
        if real:
            updates.append("UPDATE books SET cover_url = '/static/covers/%s' WHERE title = '%s';" % (real, book["title"]))
        if size:
            print(f"[OK]   {book['title']} ({size // 1024} KB) 封面={real or cover_file}")
        else:
            print(f"[FAIL] {book['title']} 下载失败，请检查网络或 gutenberg_id={book['gutenberg_id']}")
        manifest.append({**book, "file": f"/static/books/{slug}.txt", "cover": f"/static/covers/{real or cover_file}", "size": size})
    (STATIC / "book_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    if updates:
        sql_path = Path(__file__).parent / "update_covers.sql"
        sql_path.write_text("USE library_system;\n" + "\n".join(updates) + "\n", encoding="utf-8")
        print(f"已生成 {sql_path}，请在 MySQL 中执行一次以启用真实封面")
    print(f"完成，共 {len(BOOKS)} 本，输出目录：{STATIC}")


if __name__ == "__main__":
    main()
