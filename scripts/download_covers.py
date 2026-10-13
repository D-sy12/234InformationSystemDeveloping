"""从 Gutenberg 镜像下载 10 本在线书的真实封面，保存为 covers/{slug}.jpg。"""
import os
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COVER_DIR = os.path.join(ROOT, "backend", "static", "covers")

BOOKS = [
    ("hongloumeng", 24264), ("xiyouji", 23962), ("sanguoyanyi", 23950),
    ("shuihuzhuan", 23863), ("pride-and-prejudice", 1342), ("alice-in-wonderland", 11),
    ("frankenstein", 84), ("sherlock-holmes", 1661), ("moby-dick", 2701),
    ("a-tale-of-two-cities", 98),
]

def fetch(url, timeout=120):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

ok = []
for slug, gid in BOOKS:
    url = f"https://gutenberg.pglaf.org/cache/epub/{gid}/pg{gid}.cover.medium.jpg"
    try:
        data = fetch(url)
        if not data.startswith(b"\xff\xd8"):  # JPEG 魔数校验
            raise ValueError("not a jpeg")
        path = os.path.join(COVER_DIR, f"{slug}.jpg")
        with open(path, "wb") as f:
            f.write(data)
        ok.append(slug)
        print(f"[OK]   {slug} ({len(data)//1024} KB)")
    except Exception as e:
        print(f"[FAIL] {slug}: {e}")

print(f"\n成功 {len(ok)}/10：" + ", ".join(ok))
