# -*- coding: utf-8 -*-
"""构建产物结构自检: 标签平衡 / 占位符残留 / 锚点一致性 / 关键组件是否就位。"""
import os
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")  # 产物含 emoji, 否则 GBK 控制台会抛 UnicodeEncodeError

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "ADB从入门到企业级实战与面试指南.html")

with open(OUT, "r", encoding="utf-8") as f:
    h = f.read()

print("size:", len(h), "chars")

# 1. 占位符残留
left = re.findall(r"__[A-Z]+__", h)
print("placeholders left:", left or "none")

# 2. 标签平衡
for tag in ["div", "details", "figure", "table", "pre", "blockquote", "main", "aside", "article"]:
    o = len(re.findall(r"<%s[\s>]" % tag, h))
    c = len(re.findall(r"</%s>" % tag, h))
    flag = "OK " if o == c else "!!!"
    print("%s <%s> open=%d close=%d" % (flag, tag, o, c))

# 3. 组件计数
print("details.qa   :", len(re.findall(r'<details class="qa"', h)))
print("details.scene:", len(re.findall(r'details class="qa scene"', h)))
print("callouts     :", {k: len(re.findall(r'class="callout %s"' % k, h))
                         for k in ["info", "tip", "warn", "danger"]})
print("verdict cards:", len(re.findall(r'class="verdict', h)))
print("figures      :", len(re.findall(r'<figure class="figure', h)))
print("raw ascii    :", len(re.findall(r'details class="raw"', h)))
print("table wrap   :", len(re.findall(r'class="tw"', h)))
print("badges       :", len(re.findall(r'class="badge lv', h)))

# 4. 锚点一致性: 侧栏 href 是否都能在正文找到对应 id
toc_ids = re.findall(r'class="toc-l[23]" href="#([^"]+)"', h)
head_ids = set(re.findall(r'<h[23] id="([^"]+)"', h))
missing = [i for i in toc_ids if i not in head_ids]
print("toc links:", len(toc_ids), "headings:", len(head_ids), "dangling:", missing or "none")
dup = [k for k, v in Counter(re.findall(r'<h[23] id="([^"]+)"', h)).items() if v > 1]
print("duplicate heading ids:", dup or "none")

# 5. 悬空的 data-h 路径卡片
print("path cards:", len(re.findall(r'data-h="', h)))

# 6. 是否残留未转换的 markdown 记号
for pat, name in [(r"^#{1,6} ", "md heading"), (r"\*\*[^<\n]{2,40}\*\*", "md bold"),
                  (r"^\|.*\|$", "md table row")]:
    n = len(re.findall(pat, h, re.M))
    print("residual %-14s: %d %s" % (name, n, "".join(re.findall(pat + "\n", h, re.M)[:2])))

# 7. 代码块总数与语言分布
langs = Counter(re.findall(r'<code class="language-([\w-]+)"', h))
print("code blocks:", sum(langs.values()), dict(langs))

# 8. 抽查片段
def show(label, pat, span=260):
    m = re.search(pat, h, re.S)
    print("\n--- %s ---\n%s" % (label, (m.group(0)[:span] if m else "NOT FOUND")))

show("hero lede", r'<p class="lede">.*?</p>')
show("first QA", r'<details class="qa">.*?</summary>')
show("first callout", r'<div class="callout \w+">.*?</div>\s*</div>')
show("arch figure head", r'<figure class="figure arch">.{0,200}')
