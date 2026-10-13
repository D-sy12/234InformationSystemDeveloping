"""为中文古典名著生成线装书风格封面 SVG：藏青布面 + 米色竖排书签框 + 书名竖排。"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COVER_DIR = os.path.join(ROOT, "backend", "static", "covers")

BOOKS = [
    ("hongloumeng", "红楼梦", "曹雪芹 著"),
    ("xiyouji", "西游记", "吴承恩 著"),
    ("sanguoyanyi", "三国演义", "罗贯中 著"),
    ("shuihuzhuan", "水浒传", "施耐庵 著"),
]

TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" width="300" height="420" viewBox="0 0 300 420">
  <rect width="300" height="420" fill="{bg}"/>
  <rect x="12" y="12" width="276" height="396" fill="none" stroke="#c9a96a" stroke-width="2"/>
  <rect x="192" y="36" width="68" height="{label_h}" fill="#f5ecd7"/>
  {chars}
  <text x="40" y="372" font-size="15" fill="#c9a96a" font-family="KaiTi,STKaiti,serif">{author}</text>
</svg>
"""

BGS = ["#22365d", "#2d4a3e", "#5d2a2a", "#3a3a5d"]

for i, (slug, title, author) in enumerate(BOOKS):
    chars = []
    for j, ch in enumerate(title):
        chars.append(
            f'  <text x="226" y="{86 + j * 46}" font-size="36" fill="#2b2b2b" '
            f'text-anchor="middle" font-family="KaiTi,STKaiti,serif">{ch}</text>'
        )
    label_h = 50 + len(title) * 46
    svg = TEMPLATE.format(bg=BGS[i % len(BGS)], label_h=label_h, chars="\n".join(chars), author=author)
    path = os.path.join(COVER_DIR, f"{slug}.svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"[OK] {slug}.svg")
