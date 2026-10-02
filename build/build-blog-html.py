# -*- coding: utf-8 -*-
"""
把 ADB 博客 Markdown 构建成单文件、零依赖、可离线打开的交互式 HTML 文档站。

用法:
    python build/build-blog-html.py

输入: <仓库根>/ADB从入门到企业级实战与面试指南.md
输出: <仓库根>/ADB从入门到企业级实战与面试指南.html

构建期做这些事(全部为纯文本变换, 不依赖网络):
  1. Markdown -> HTML (markdown 库, 含 tables / fenced_code / toc)
  2. 抽出 H1 + 引言, 生成 Hero 区(标题 / 数据条 / 阅读路径卡片)
  3. ASCII 架构图 -> CSS 可视化架构图(原图保留在「查看 ASCII 原图」折叠块里)
  4. forward/reverse 说明 -> CSS 流向图
  5. 面试题 -> <details> 手风琴(可自测), 场景题同理
  6. 引用块 -> 分级 Callout(提示 / 注意 / 铁律 / 面试加分)
  7. 加减分回答 -> 双色对照卡
  8. 表格 -> 可横向滚动容器
  9. 面试章节标题 -> 难度徽章
 10. 注入侧边目录 / 滚动高亮 / 命令搜索 / 主题切换 / 字号 / 复制 等前端逻辑
"""

import html as htmllib
import os
import re
import sys

import markdown

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)  # 脚本位于 build/ 下, 产物与源文件放在仓库根目录
SRC = os.path.join(ROOT, "ADB从入门到企业级实战与面试指南.md")
OUT = os.path.join(ROOT, "ADB从入门到企业级实战与面试指南.html")

TITLE = "ADB 从入门到企业级实战与面试全解"
SUBTITLE = "从 adb devices 到千台设备农场 · 原理 / 实战 / 面试一体化手册"
DESC = "ADB 原理、命令、自动化测试、CI/CD、设备农场、安全合规与 27 道面试题的分层指南"


# --------------------------------------------------------------------------
# 0. 小工具
# --------------------------------------------------------------------------
def esc(s: str) -> str:
    return htmllib.escape(s, quote=False)


def slugify(value: str, separator: str) -> str:
    """保留中文的 heading id 生成器, 让锚点可读。"""
    value = value.strip().lower()
    value = re.sub(r"[^\w\u4e00-\u9fff\-. ]", "", value, flags=re.UNICODE)
    value = re.sub(r"[\s.]+", separator, value)
    value = re.sub(re.escape(separator) + r"{2,}", separator, value)
    return value.strip(separator) or "sec"


# --------------------------------------------------------------------------
# 1. 读取与预处理 Markdown
# --------------------------------------------------------------------------
with open(SRC, "r", encoding="utf-8") as f:
    raw = f.read()

# 1.1 抽出 H1
m = re.match(r"#\s+(.+?)\s*\n", raw)
if not m:
    sys.exit("找不到 H1 标题")
doc_title = m.group(1).strip()
raw = raw[m.end():]

# 1.2 抽出紧随其后的引言 blockquote
lede = ""
lm = re.match(r"\s*((?:>[^\n]*\n)+)", raw)
if lm:
    lede = " ".join(
        re.sub(r"^>\s?", "", line).strip()
        for line in lm.group(1).strip().splitlines()
    )
    raw = raw[lm.end():]

# 1.3 去掉紧随引言的分隔线与原 Markdown 自带目录(改由侧边栏承担)
raw = re.sub(r"^\s*---\s*\n", "", raw, count=1)
raw = re.sub(r"^##\s*目录\s*\n.*?\n---\s*\n", "", raw, count=1, flags=re.S | re.M)

# 1.4 段落内的软换行 -> 硬换行(保持列表项内的多行紧凑展示)
#     markdown 默认会把单换行合并成空格, 这里不动它, 由源码控制。

# 1.5 兼容 markdown 的 '---' 分隔与后续内容
raw = raw.lstrip("\n")


# --------------------------------------------------------------------------
# 2. 转换为 HTML
# --------------------------------------------------------------------------
md = markdown.Markdown(
    extensions=["tables", "fenced_code", "attr_list", "sane_lists", "toc", "md_in_html"],
    extension_configs={
        "toc": {"slugify": slugify, "permalink": False, "toc_depth": "2-3"},
        "fenced_code": {"lang_prefix": "language-"},
    },
    output_format="html5",
)
body = md.convert(raw)
tokens = md.toc_tokens


# --------------------------------------------------------------------------
# 3. 侧边目录
# --------------------------------------------------------------------------
def plain(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    return htmllib.unescape(text)


def build_toc(tks):
    out = []
    for t in tks:
        if t["level"] != 2:
            continue
        label = plain(t["name"])
        num = re.match(r"^(\d+)\.", label)
        chip = num.group(1) if num else "•"
        out.append('<div class="toc-group">')
        out.append(
            '<a class="toc-l2" href="#{i}" data-target="{i}">'
            '<i class="chip">{c}</i><span>{n}</span></a>'.format(
                i=t["id"], c=esc(chip), n=esc(label)
            )
        )
        kids = [c for c in t.get("children", []) if c["level"] == 3]
        if kids:
            out.append('<div class="toc-sub">')
            for c in kids:
                out.append(
                    '<a class="toc-l3" href="#{i}" data-target="{i}">{n}</a>'.format(
                        i=c["id"], n=esc(plain(c["name"]))
                    )
                )
            out.append("</div>")
        out.append("</div>")
    return "\n".join(out)


TOC_HTML = build_toc(tokens)


# --------------------------------------------------------------------------
# 4. 可视化替换: 架构图 与 流向图
# --------------------------------------------------------------------------
ARCH_FIGURE = """
<figure class="figure arch">
  <figcaption>图 1 · ADB 三端架构与一次命令的完整链路</figcaption>
  <div class="arch-grid">
    <div class="arch-side host">
      <div class="arch-side-title"><span class="dot"></span>开发机 / CI Runner</div>
      <div class="arch-node n1">
        <span class="nid">①</span>
        <div><b>adb client</b><em>你敲的每条命令 = 一个独立进程，用完即退</em></div>
      </div>
      <div class="arch-link"><span>本地 socket</span><code>127.0.0.1:5037</code></div>
      <div class="arch-node n2">
        <span class="nid">②</span>
        <div><b>adb server</b><em>后台常驻 · 全机唯一 · 负责设备扫描与请求路由</em></div>
      </div>
    </div>
    <div class="arch-mid">
      <div class="wire-top">transport</div>
      <div class="wire"></div>
      <div class="wire-label">USB bulk endpoints<br><i>或</i><br>TCP 5555+（无线调试）</div>
    </div>
    <div class="arch-side device">
      <div class="arch-side-title"><span class="dot"></span>Android 设备</div>
      <div class="arch-node n3">
        <span class="nid">③</span>
        <div><b>adbd</b><em>以 shell 用户身份运行的 native 守护进程</em></div>
      </div>
      <div class="arch-link"><span>fork / exec</span></div>
      <div class="arch-node n4">
        <span class="nid">④</span>
        <div><b>shell / app_process</b><em>你真正操作的系统服务与进程</em></div>
      </div>
    </div>
  </div>
  <div class="arch-note">
    <b>为什么重要：</b><code>adb kill-server</code> 杀掉的是 ② 这个「中间人」，
    所以它既不改变设备状态也不影响 ① 的参数 —— 这解释了它为什么能一次修好一大批「玄学问题」。
  </div>
</figure>
"""

FLOW_FIGURE = """
<figure class="figure flow">
  <figcaption>图 2 · forward 与 reverse 的方向差异</figcaption>
  <div class="flow-row fwd">
    <span class="tag">forward</span>
    <span class="box">主机浏览器<br><i>localhost:6100</i></span>
    <span class="arrow">→</span>
    <span class="box mid">adb server</span>
    <span class="arrow">→</span>
    <span class="box">设备上的服务<br><i>设备:7100</i></span>
    <span class="use">用途：scrcpy、WebView 调试、访问设备内服务</span>
  </div>
  <div class="flow-row rev">
    <span class="tag">reverse</span>
    <span class="box">设备上的 App<br><i>localhost:8081</i></span>
    <span class="arrow">→</span>
    <span class="box mid">adb server</span>
    <span class="arrow">→</span>
    <span class="box">你电脑上的服务<br><i>主机:8081</i></span>
    <span class="use">用途：RN/Metro、Mock Server、抓包代理</span>
  </div>
</figure>
"""


def swap_figure(html_text, matcher, figure):
    """把匹配到的 <pre><code> 块换成可视化图, 原 ASCII 收进折叠块。

    注意: 源码里存在无语言标记的围栏(markdown 会渲染成裸 <pre><code>),
    所以 class 必须可选; 且必须用 count=0 全量扫描 —— 否则前一个不匹配的
    候选块会白白吃掉 count 配额(上一版架构图替换失败的根因)。
    """

    pattern = re.compile(
        r'<pre><code(?: class="language-[^"]*")?>(.*?)</code></pre>', re.S
    )

    def repl(mo):
        content = mo.group(1)
        if not matcher(content):
            return mo.group(0)
        return (
            figure
            + '\n<details class="raw"><summary>查看 ASCII 原图（便于复制到笔记）</summary>'
            + '<pre><code class="language-text">'
            + content
            + "</code></pre></details>"
        )

    return pattern.sub(repl, html_text)


body = swap_figure(
    body, lambda c: "adb client" in c and "adb server" in c and "adbd" in c, ARCH_FIGURE
)
body = swap_figure(
    body, lambda c: "forward:" in c and "reverse:" in c and "浏览器" in c, FLOW_FIGURE
)


# --------------------------------------------------------------------------
# 5. 面试题 -> 手风琴
# --------------------------------------------------------------------------
# 注意: 题干里常含 <code> 行内标签, 所以不能用 [^<]* 限定
QA_RE = re.compile(
    r"<p><strong>(Q(\d+)\..*?)</strong></p>\s*<blockquote>(.*?)</blockquote>", re.S
)


def qa_repl(mo):
    qtext = mo.group(1).strip()
    num = mo.group(2)
    answer = mo.group(3).strip()
    qtext = re.sub(r"^Q\d+\.\s*", "", qtext)
    return (
        '<details class="qa">'
        '<summary><span class="qbadge">Q{num}</span>'
        '<span class="qtext">{q}</span></summary>'
        '<div class="answer">{a}</div>'
        "</details>"
    ).format(num=num, q=qtext, a=answer)


qa_count = len(QA_RE.findall(body))
body = QA_RE.sub(qa_repl, body)

# 场景题（含紧随其后的说明段落 + 有序列表）
SCENE_RE = re.compile(
    r"<p><strong>(场景[一二三四五六]：[^<]*?)</strong></p>\s*(.*?</ol>)", re.S
)


def scene_repl(mo):
    name = mo.group(1).strip()
    rest = mo.group(2).strip()
    return (
        '<details class="qa scene">'
        '<summary><span class="qbadge scene-badge">场景</span>'
        '<span class="qtext">{n}</span></summary>'
        '<div class="answer">{r}</div>'
        "</details>"
    ).format(n=name, r=rest)


scene_count = len(SCENE_RE.findall(body))
body = SCENE_RE.sub(scene_repl, body)


# --------------------------------------------------------------------------
# 6. 加减分对照卡
# --------------------------------------------------------------------------
def verdict(html_text, strong_text, cls, icon, label):
    pat = re.compile(
        r"<p><strong>" + strong_text + r"</strong>：</p>\s*<ul>(.*?)</ul>", re.S
    )
    return pat.sub(
        lambda mo: '<div class="verdict {c}"><h4>{i} {l}</h4><ul>{u}</ul></div>'.format(
            c=cls, i=icon, l=label, u=mo.group(1).strip()
        ),
        html_text,
        count=1,
    )


body = verdict(body, "会减分的回答", "bad", "✕", "会减分的回答")
body = verdict(body, "明显加分的回答", "good", "✓", "明显加分的回答")


# --------------------------------------------------------------------------
# 7. 引用块 -> 分级 Callout
# --------------------------------------------------------------------------
CALLOUT_RULES = [
    (("铁律", "必须用同一个", "❌"), "danger", "铁律", "🚨"),
    (("⚠️", "陷阱", "坑", "注意", "副作用"), "warn", "注意", "⚠️"),
    (("面试加分", "面试题", "加分", "💡"), "tip", "面试视角", "💡"),
]


def callout_repl(mo):
    inner = mo.group(1)
    text = plain(inner)
    cls, label, icon = "info", "说明", "📌"
    for keys, c, lab, ico in CALLOUT_RULES:
        if any(k in text for k in keys):
            cls, label, icon = c, lab, ico
            break
    # 去掉内容里已经带的表情, 避免与 CSS 图标重复
    inner_clean = re.sub(r"^\s*<p>\s*(?:⚠️|🚨|💡|📌|❌)\s*", "<p>", inner, count=1)
    return (
        '<div class="callout {c}"><div class="callout-h">{i} {l}</div>'
        '<div class="callout-b">{b}</div></div>'
    ).format(c=cls, i=icon, l=label, b=inner_clean.strip())


body = re.sub(r"<blockquote>(.*?)</blockquote>", callout_repl, body, flags=re.S)


# --------------------------------------------------------------------------
# 8. 表格容器 + 面试难度徽章
# --------------------------------------------------------------------------
body = body.replace("<table>", '<div class="tw"><table>').replace(
    "</table>", "</table></div>"
)

LV = {
    "6.1": ("初级", "lv1", "1-3 年"),
    "6.2": ("中级", "lv2", "3-5 年"),
    "6.3": ("高级", "lv3", "架构 / 资深"),
    "6.4": ("场景题", "lv4", "重点"),
    "6.5": ("面试官视角", "lv5", "加分项"),
}


def badge_repl(mo):
    attrs, text = mo.group(1), mo.group(2)
    key = text.split()[0].rstrip(".")
    if key in LV:
        name, cls, note = LV[key]
        return (
            '<h3{attrs}>{text}<span class="badge {cls}">{name} · {note}</span></h3>'
        ).format(attrs=attrs, text=text, cls=cls, name=name, note=note)
    return mo.group(0)


body = re.sub(r"<h3([^>]*)>(6\.\d[^<]*)</h3>", badge_repl, body)


# --------------------------------------------------------------------------
# 9. 组装页面
# --------------------------------------------------------------------------
TOC_JSON_HINT = ""

SVG_OPEN = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" '
            'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">')
ICO_BULB = SVG_OPEN + ('<path d="M9.5 18h5M10.5 21h3M12 3a6 6 0 0 0-3.6 10.8c.4.3.6.8.6 1.3v.9h6v-.9'
                       'c0-.5.2-1 .6-1.3A6 6 0 0 0 12 3z"/></svg>')
ICO_TERM = SVG_OPEN + ('<rect x="3" y="4.5" width="18" height="15" rx="2.2"/>'
                       '<path d="M7.2 9.4 9.8 12l-2.6 2.6M13 14.6h4"/></svg>')
ICO_BUILD = SVG_OPEN + ('<path d="M3.5 20.5V6.2a1 1 0 0 1 1-1h6.4a1 1 0 0 1 1 1v14.3"/>'
                        '<path d="M11.9 20.5V10.4h7.6a1 1 0 0 1 1 1v9.1M2.5 20.5h19"/>'
                        '<path d="M6.4 9.2h1.4M6.4 13h1.4M6.4 16.6h1.4M15 13.6h1.4M15 17h1.4"/></svg>')
ICO_CHECK = SVG_OPEN + ('<circle cx="12" cy="12" r="8.2"/><path d="M8.4 12.4l2.5 2.5 4.7-5.2"/></svg>')

# 阅读路径卡片
PATHS_HTML = """
    <div class="paths">
      <a class="path" data-h="1. 原理篇" href="#">
        <span class="pico">{ico1}</span><b>入门 · 先懂原理</b>
        <em>三端架构 / 5037 与 5555 / PTY 与二进制安全 —— 面试真正拉开差距的地方</em>
      </a>
      <a class="path" data-h="3. 基础篇" href="#">
        <span class="pico">{ico2}</span><b>日常 · 命令与坑</b>
        <em>安装参数、日志缓冲、输入模拟、截图录屏，以及失败对照表</em>
      </a>
      <a class="path" data-h="5. 企业级篇" href="#">
        <span class="pico">{ico3}</span><b>企业级 · 落地</b>
        <em>CI/CD 集成、设备自愈、并发隔离、安全合规、12 条踩坑清单</em>
      </a>
      <a class="path" data-h="6. 面试篇" href="#">
        <span class="pico">{ico4}</span><b>面试 · 自测</b>
        <em>分层题库 + 场景设计题，点击展开核对答案</em>
      </a>
    </div>
""".format(ico1=ICO_BULB, ico2=ICO_TERM, ico3=ICO_BUILD, ico4=ICO_CHECK)

html_lang = "zh-CN"

page = r"""<!DOCTYPE html>
<html lang="zh-CN" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<meta name="description" content="__DESC__">
<meta name="author" content="ADB 实战手册">
<style>
/* ===================== 设计令牌 ===================== */
:root{
  --base: 16px;
  --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
          "Hiragino Sans GB", "Microsoft YaHei", "Source Han Sans SC", sans-serif;
  --mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas,
          "Cascadia Mono", "Liberation Mono", monospace;
  --accent:#2563eb; --accent-soft:rgba(37,99,235,.10);
  --green:#16a34a; --green-soft:rgba(22,163,74,.10);
  --amber:#d97706; --amber-soft:rgba(217,119,6,.10);
  --red:#dc2626;  --red-soft:rgba(220,38,38,.09);
  --violet:#7c3aed; --violet-soft:rgba(124,58,237,.10);
  --bg:#ffffff; --bg-soft:#f7f8fa; --surface:#ffffff; --surface-2:#f2f4f7;
  --text:#151922; --text-2:#4b5563; --muted:#7b8698;
  --border:#e5e8ee; --border-2:#d3d9e3;
  --code-bg:#0e1526; --code-head:#16203a; --code-text:#e3e9f5;
  --shadow:0 1px 2px rgba(16,24,40,.04), 0 8px 24px -12px rgba(16,24,40,.18);
  --radius:14px;
  --sidebar:320px;
}
html[data-theme="dark"]{
  --accent:#60a5fa; --accent-soft:rgba(96,165,250,.14);
  --green:#4ade80; --green-soft:rgba(74,222,128,.12);
  --amber:#fbbf24; --amber-soft:rgba(251,191,36,.12);
  --red:#f87171;  --red-soft:rgba(248,113,113,.12);
  --violet:#a78bfa; --violet-soft:rgba(167,139,250,.14);
  --bg:#080b12; --bg-soft:#0c1018; --surface:#0f141f; --surface-2:#161c29;
  --text:#e7ebf3; --text-2:#adb7c7; --muted:#7d8798;
  --border:#212938; --border-2:#2b3547;
  --code-bg:#0a0f1c; --code-head:#121a2b; --code-text:#dde5f4;
  --shadow:0 1px 2px rgba(0,0,0,.3), 0 12px 28px -16px rgba(0,0,0,.7);
}
*{box-sizing:border-box}
html{font-size:var(--base);scroll-behavior:smooth;scroll-padding-top:24px}
body{
  margin:0;background:var(--bg);color:var(--text);font-family:var(--sans);
  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;
  line-height:1.75;
}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
::selection{background:var(--accent-soft)}

/* ===================== 顶部进度条 ===================== */
.progress{position:fixed;top:0;left:0;right:0;height:3px;z-index:80;background:transparent}
.progress i{display:block;height:100%;width:0;
  background:linear-gradient(90deg,var(--accent),var(--green));transition:width .1s linear}

/* ===================== 侧边栏 ===================== */
.sidebar{
  position:fixed;top:0;left:0;bottom:0;width:var(--sidebar);z-index:60;
  background:var(--surface);border-right:1px solid var(--border);
  display:flex;flex-direction:column;
}
.brand{display:flex;gap:11px;align-items:center;padding:20px 20px 14px}
.brand svg{width:30px;height:30px;flex:0 0 auto;color:var(--green)}
.brand b{display:block;font-size:15px;letter-spacing:.2px;line-height:1.3}
.brand em{display:block;font-style:normal;font-size:11.5px;color:var(--muted);margin-top:2px}
.side-tools{padding:0 16px 12px;display:flex;gap:8px}
.searchbtn{
  flex:1;display:flex;align-items:center;gap:8px;cursor:pointer;
  background:var(--surface-2);border:1px solid var(--border);color:var(--muted);
  border-radius:10px;padding:8px 11px;font-size:12.5px;font-family:inherit;text-align:left;
}
.searchbtn:hover{border-color:var(--border-2);color:var(--text-2)}
.searchbtn kbd{
  margin-left:auto;font-family:var(--mono);font-size:10.5px;background:var(--bg);
  border:1px solid var(--border);border-radius:5px;padding:1px 5px;color:var(--muted);
}
.toc{overflow-y:auto;padding:6px 12px 20px;flex:1;scrollbar-width:thin}
.toc::-webkit-scrollbar{width:8px}
.toc::-webkit-scrollbar-thumb{background:var(--border-2);border-radius:8px}
.toc-group{margin-bottom:2px}
.toc-l2{
  display:flex;gap:9px;align-items:baseline;padding:7px 9px;border-radius:9px;
  color:var(--text-2);font-size:13px;font-weight:600;line-height:1.45;
  border-left:2px solid transparent;
}
.toc-l2 .chip{
  flex:0 0 auto;font-style:normal;font-family:var(--mono);font-size:10.5px;font-weight:700;
  min-width:20px;height:20px;line-height:20px;text-align:center;border-radius:6px;
  background:var(--surface-2);color:var(--muted);
}
.toc-l2:hover{background:var(--surface-2);text-decoration:none;color:var(--text)}
.toc-l2.active{background:var(--accent-soft);color:var(--accent);border-left-color:var(--accent)}
.toc-l2.active .chip{background:var(--accent);color:#fff}
.toc-sub{display:none;margin:2px 0 8px 22px;border-left:1px dashed var(--border-2);padding-left:9px}
.toc-group.open .toc-sub{display:block}
.toc-l3{
  display:block;padding:5px 9px;border-radius:8px;font-size:12.3px;color:var(--muted);
  line-height:1.5;
}
.toc-l3:hover{background:var(--surface-2);color:var(--text);text-decoration:none}
.toc-l3.active{color:var(--accent);background:var(--accent-soft);font-weight:600}
.side-foot{
  border-top:1px solid var(--border);padding:11px 16px;display:flex;
  align-items:center;gap:8px;flex-wrap:wrap;
}
.mini{
  background:var(--surface-2);border:1px solid var(--border);color:var(--text-2);
  border-radius:8px;padding:5px 9px;font-size:11.5px;cursor:pointer;font-family:inherit;
  transition:.15s;
}
.mini:hover{border-color:var(--accent);color:var(--accent)}
.mini.icon{width:30px;padding:5px 0;text-align:center}
.spacer{flex:1}

/* ===================== 主内容 ===================== */
.wrap{margin-left:var(--sidebar);display:block}
.doc{max-width:900px;margin:0 auto;padding:0 44px 140px}

/* Hero */
.hero{padding:64px 0 12px}
.hero h1{
  font-size:2.6rem;line-height:1.2;margin:0 0 14px;letter-spacing:-.02em;
  background:linear-gradient(100deg,var(--text) 30%,var(--accent));
  -webkit-background-clip:text;background-clip:text;color:transparent;
}
html[data-theme="dark"] .hero h1{background:linear-gradient(100deg,#fff 25%,var(--accent));-webkit-background-clip:text;background-clip:text}
.hero .lede{font-size:1.06rem;color:var(--text-2);margin:0 0 22px;max-width:70ch}
.stats{display:flex;flex-wrap:wrap;gap:9px;margin-bottom:26px}
.stat{
  display:flex;align-items:baseline;gap:6px;background:var(--surface-2);
  border:1px solid var(--border);border-radius:999px;padding:5px 13px;font-size:12.5px;color:var(--text-2);
}
.stat b{color:var(--text);font-size:14px}
.paths{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin-bottom:8px}
.path{
  display:block;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);
  padding:15px 16px;box-shadow:var(--shadow);transition:.18s;color:inherit;
}
.path:hover{transform:translateY(-2px);border-color:var(--accent);text-decoration:none}
.path .pico{
  width:36px;height:36px;border-radius:11px;display:flex;align-items:center;
  justify-content:center;margin-bottom:10px;border:1px solid transparent;
}
.path .pico svg{width:19px;height:19px;display:block}
.path:nth-child(1) .pico{background:var(--accent-soft);color:var(--accent);border-color:var(--accent)}
.path:nth-child(2) .pico{background:var(--green-soft);color:var(--green);border-color:var(--green)}
.path:nth-child(3) .pico{background:var(--violet-soft);color:var(--violet);border-color:var(--violet)}
.path:nth-child(4) .pico{background:var(--amber-soft);color:var(--amber);border-color:var(--amber)}
.path b{display:block;font-size:13.5px;margin-bottom:4px}
.path em{display:block;font-style:normal;font-size:11.8px;color:var(--muted);line-height:1.55}

/* 正文排版 */
.doc h2{
  font-size:1.62rem;margin:3.4rem 0 1.1rem;padding-bottom:.55rem;letter-spacing:-.01em;
  border-bottom:1px solid var(--border);scroll-margin-top:20px;
}
.doc h2:first-of-type{margin-top:1.6rem}
.doc h3{font-size:1.2rem;margin:2.4rem 0 .85rem;padding-left:12px;position:relative;scroll-margin-top:20px}
.doc h3::before{content:"";position:absolute;left:0;top:.34em;bottom:.3em;width:3px;
  border-radius:3px;background:linear-gradient(var(--accent),var(--green))}
.doc h2 .anchor,.doc h3 .anchor{
  margin-left:9px;font-size:.72em;font-weight:400;color:var(--muted);opacity:0;
  text-decoration:none;transition:.16s;
}
.doc h2:hover .anchor,.doc h3:hover .anchor{opacity:1}
.doc h2 .anchor:hover,.doc h3 .anchor:hover{color:var(--accent);text-decoration:none}
.doc h2 .anchor.done,.doc h3 .anchor.done{opacity:1;color:var(--green)}
.doc h4{font-size:1.02rem;margin:1.6rem 0 .6rem}
.doc p{margin:.85rem 0;color:var(--text)}
.doc ul,.doc ol{margin:.8rem 0;padding-left:1.5rem}
.doc li{margin:.36rem 0}
.doc li>ul,.doc li>ol{margin:.3rem 0}
.doc strong{font-weight:700;color:var(--text)}
.doc hr{border:0;border-top:1px dashed var(--border-2);margin:2.6rem 0}
.doc img{max-width:100%;border-radius:10px}

code{
  font-family:var(--mono);font-size:.875em;background:var(--surface-2);
  border:1px solid var(--border);border-radius:6px;padding:.1em .38em;
  color:var(--violet);word-break:break-word;
}
html[data-theme="dark"] code{color:#c4b5fd}

/* 代码块 */
.doc pre{
  position:relative;background:var(--code-bg);border:1px solid var(--border);
  border-radius:var(--radius);margin:1.1rem 0;overflow:hidden;box-shadow:var(--shadow);
}
.pre-head{
  display:flex;align-items:center;gap:10px;padding:7px 12px;background:var(--code-head);
  border-bottom:1px solid rgba(255,255,255,.06);
}
.pre-head .lang{
  font-family:var(--mono);font-size:10.5px;letter-spacing:.09em;text-transform:uppercase;
  color:#8fa2c4;
}
.pre-head .dots{display:flex;gap:5px}
.pre-head .dots i{width:9px;height:9px;border-radius:50%;background:#2c3a55;display:block}
.pre-head .dots i:first-child{background:#ff5f57}
.pre-head .dots i:nth-child(2){background:#febc2e}
.pre-head .dots i:nth-child(3){background:#28c840}
.copy{
  margin-left:auto;font-family:inherit;font-size:11px;color:#9fb0cf;cursor:pointer;
  background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);
  border-radius:7px;padding:3px 10px;transition:.15s;
}
.copy:hover{background:rgba(255,255,255,.14);color:#fff}
.copy.done{color:#4ade80;border-color:rgba(74,222,128,.5)}
.doc pre code{
  display:block;padding:14px 16px;overflow-x:auto;background:transparent;border:0;
  color:var(--code-text);font-size:12.9px;line-height:1.72;white-space:pre;
  -webkit-overflow-scrolling:touch;
}
.doc pre code::-webkit-scrollbar{height:9px}
.doc pre code::-webkit-scrollbar-thumb{background:#27334d;border-radius:9px}
.tok-c{color:#7dd3fc;font-weight:600}
.tok-f{color:#fbbf24}
.tok-s{color:#86efac}
.tok-v{color:#c4b5fd}
.tok-n{color:#f0abfc}
.tok-m{color:#64748b;font-style:italic}

/* 表格 */
.tw{overflow-x:auto;margin:1.2rem 0;border:1px solid var(--border);
  border-radius:var(--radius);box-shadow:var(--shadow);background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:13.4px;min-width:520px}
th,td{padding:10px 14px;text-align:left;border-bottom:1px solid var(--border);vertical-align:top}
th{background:var(--surface-2);font-weight:700;font-size:12.5px;color:var(--text-2);
  white-space:nowrap;letter-spacing:.02em}
tbody tr:last-child td{border-bottom:0}
tbody tr:hover{background:var(--bg-soft)}
td code{font-size:12px;white-space:nowrap}

/* Callout */
.callout{
  margin:1.2rem 0;border-radius:var(--radius);border:1px solid var(--border);
  border-left:4px solid var(--muted);background:var(--surface-2);overflow:hidden;
}
.callout-h{
  font-size:12.5px;font-weight:700;letter-spacing:.04em;padding:9px 16px 0;
  display:flex;align-items:center;gap:7px;
}
.callout-b{padding:2px 16px 10px}
.callout-b>p:first-child{margin-top:.35rem}
.callout-b>p:last-child{margin-bottom:.35rem}
.callout.info{border-left-color:var(--accent);background:var(--accent-soft)}
.callout.info .callout-h{color:var(--accent)}
.callout.tip{border-left-color:var(--violet);background:var(--violet-soft)}
.callout.tip .callout-h{color:var(--violet)}
.callout.warn{border-left-color:var(--amber);background:var(--amber-soft)}
.callout.warn .callout-h{color:var(--amber)}
.callout.danger{border-left-color:var(--red);background:var(--red-soft)}
.callout.danger .callout-h{color:var(--red)}

/* 面试题手风琴 */
.qa{
  border:1px solid var(--border);border-radius:var(--radius);background:var(--surface);
  margin:.7rem 0;box-shadow:var(--shadow);overflow:hidden;transition:.15s;
}
.qa[open]{border-color:var(--accent);box-shadow:0 0 0 1px var(--accent-soft),var(--shadow)}
.qa>summary{
  list-style:none;cursor:pointer;display:flex;gap:11px;align-items:flex-start;
  padding:13px 16px;font-weight:600;font-size:14.4px;line-height:1.6;
}
.qa>summary::-webkit-details-marker{display:none}
.qa>summary:hover{background:var(--surface-2)}
.qa>summary::after{
  content:"+";margin-left:auto;color:var(--muted);font-family:var(--mono);
  font-weight:400;font-size:17px;line-height:1.2;transition:.2s;
}
.qa[open]>summary::after{content:"−";color:var(--accent)}
.qbadge{
  flex:0 0 auto;font-family:var(--mono);font-size:11px;font-weight:700;color:#fff;
  background:var(--accent);border-radius:7px;padding:2px 8px;margin-top:2px;
}
.scene-badge{background:var(--violet)}
.qa.scene[open]{border-color:var(--violet);box-shadow:0 0 0 1px var(--violet-soft),var(--shadow)}
.answer{padding:2px 18px 16px;border-top:1px dashed var(--border);font-size:14.4px;color:var(--text)}
.answer strong{color:var(--text)}
.answer>.callout{margin-top:.8rem}

/* 难度徽章 */
.badge{
  display:inline-block;margin-left:10px;font-size:11px;font-weight:700;vertical-align:middle;
  border-radius:999px;padding:2px 10px;letter-spacing:.03em;border:1px solid transparent;
}
.lv1{background:var(--green-soft);color:var(--green);border-color:var(--green)}
.lv2{background:var(--accent-soft);color:var(--accent);border-color:var(--accent)}
.lv3{background:var(--violet-soft);color:var(--violet);border-color:var(--violet)}
.lv4{background:var(--amber-soft);color:var(--amber);border-color:var(--amber)}
.lv5{background:var(--surface-2);color:var(--text-2);border-color:var(--border-2)}

/* 加减分对照卡 */
.verdict{border-radius:var(--radius);padding:6px 18px 12px;margin:1rem 0;border:1px solid var(--border)}
.verdict h4{margin:.9rem 0 .4rem;font-size:13.5px}
.verdict ul{margin:.3rem 0;padding-left:1.3rem}
.verdict li{margin:.42rem 0;font-size:14px}
.verdict.bad{background:var(--red-soft);border-color:var(--red)}
.verdict.bad h4{color:var(--red)}
.verdict.good{background:var(--green-soft);border-color:var(--green)}
.verdict.good h4{color:var(--green)}

/* 可视化图 */
.figure{margin:1.6rem 0;border:1px solid var(--border);border-radius:var(--radius);
  background:var(--bg-soft);padding:16px;box-shadow:var(--shadow);overflow:hidden}
.figure figcaption{font-size:12px;color:var(--muted);text-align:center;margin-bottom:14px;
  letter-spacing:.02em}
.arch-grid{display:grid;grid-template-columns:1fr 134px 1fr;gap:0;align-items:stretch}
.arch-side{border:1px solid var(--border);border-radius:12px;padding:12px;background:var(--surface);
  display:flex;flex-direction:column;justify-content:center}
.arch-side.device{border-color:var(--green)}
.arch-side.host{border-color:var(--accent)}
.arch-side-title{font-size:11.5px;font-weight:700;color:var(--text-2);display:flex;
  align-items:center;gap:7px;margin-bottom:10px;letter-spacing:.03em}
.arch-side-title .dot{width:8px;height:8px;border-radius:50%;background:var(--accent)}
.arch-side.device .arch-side-title .dot{background:var(--green)}
.arch-node{display:flex;gap:10px;align-items:flex-start;border:1px solid var(--border);
  border-radius:10px;padding:10px 12px;background:var(--bg)}
.arch-node .nid{flex:0 0 auto;width:20px;height:20px;border-radius:6px;background:var(--accent);
  color:#fff;font-size:11px;font-weight:700;text-align:center;line-height:20px;font-family:var(--mono)}
.arch-side.device .arch-node .nid{background:var(--green)}
.arch-node b{display:block;font-size:13.2px;font-family:var(--mono)}
.arch-node em{display:block;font-style:normal;font-size:11.4px;color:var(--muted);
  line-height:1.5;margin-top:2px}
.arch-link{display:flex;flex-direction:column;align-items:center;gap:4px;padding:9px 0;
  font-size:10.5px;color:var(--muted)}
.arch-link::before,.arch-link::after{content:"";width:2px;height:12px;
  background:repeating-linear-gradient(var(--border-2) 0 4px,transparent 4px 8px)}
.arch-link code{font-size:10.5px;padding:1px 6px}
.arch-mid{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;padding:0 8px}
.arch-mid .wire-top{font-size:10px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;
  color:var(--text-2)}
.arch-mid .wire{width:100%;height:2px;background:linear-gradient(90deg,var(--accent),var(--green));position:relative}
.arch-mid .wire::before,.arch-mid .wire::after{content:"";position:absolute;top:-3px;
  width:8px;height:8px;border-radius:50%;background:var(--accent)}
.arch-mid .wire::before{left:-2px}
.arch-mid .wire::after{right:-2px;background:var(--green)}
.arch-mid .wire-label{font-size:10px;color:var(--muted);text-align:center;line-height:1.55;
  word-break:keep-all}
.arch-mid .wire-label i{font-style:normal;opacity:.7}
.arch-note{margin-top:14px;font-size:12.6px;color:var(--text-2);background:var(--surface);
  border:1px dashed var(--border-2);border-radius:10px;padding:9px 12px;line-height:1.65}
.arch-note code{font-size:11.5px}

.flow-row{display:flex;flex-wrap:wrap;align-items:center;gap:9px;padding:10px 12px;
  border-radius:12px;background:var(--surface);border:1px solid var(--border);margin-bottom:10px}
.flow-row .tag{font-family:var(--mono);font-size:11px;font-weight:700;border-radius:7px;
  padding:2px 9px;color:#fff}
.flow-row.fwd .tag{background:var(--accent)}
.flow-row.rev .tag{background:var(--violet)}
.flow-row .box{border:1px solid var(--border-2);border-radius:9px;padding:6px 11px;
  font-size:12.2px;text-align:center;line-height:1.45;background:var(--bg)}
.flow-row .box i{font-style:normal;font-family:var(--mono);font-size:10.8px;color:var(--muted)}
.flow-row .box.mid{background:var(--surface-2);color:var(--muted);font-size:11.5px}
.flow-row .arrow{color:var(--accent);font-weight:700}
.flow-row.rev .arrow{color:var(--violet)}
.flow-row .use{flex:1 1 100%;font-size:11.6px;color:var(--muted);margin-top:2px}

details.raw{margin:.6rem 0 1.4rem;font-size:12.6px}
details.raw>summary{cursor:pointer;color:var(--muted);padding:5px 0}
details.raw>summary:hover{color:var(--accent)}
details.raw pre{margin-top:.5rem}

/* 页脚 */
.doc-foot{margin-top:4rem;padding-top:1.6rem;border-top:1px solid var(--border);
  color:var(--muted);font-size:12.5px;display:flex;justify-content:space-between;
  flex-wrap:wrap;gap:10px}

/* 回到顶部 */
.totop{
  position:fixed;right:22px;bottom:22px;width:42px;height:42px;border-radius:50%;
  border:1px solid var(--border);background:var(--surface);color:var(--text-2);
  cursor:pointer;font-size:16px;box-shadow:var(--shadow);opacity:0;pointer-events:none;
  transition:.2s;z-index:55;
}
.totop.show{opacity:1;pointer-events:auto}
.totop:hover{border-color:var(--accent);color:var(--accent)}

/* 搜索面板 */
.overlay{
  position:fixed;inset:0;background:rgba(9,13,22,.45);backdrop-filter:blur(3px);
  z-index:90;display:none;padding-top:9vh;justify-content:center;align-items:flex-start;
}
.overlay.show{display:flex}
.palette{
  width:min(760px,92vw);background:var(--surface);border:1px solid var(--border-2);
  border-radius:16px;box-shadow:0 24px 60px -20px rgba(0,0,0,.5);overflow:hidden;
  display:flex;flex-direction:column;max-height:76vh;
}
.palette .pin{padding:13px 16px;border-bottom:1px solid var(--border);display:flex;
  align-items:center;gap:10px}
.palette input{
  flex:1;border:0;outline:0;background:transparent;color:var(--text);
  font-size:15px;font-family:inherit;
}
.palette .pin .esc{font-size:10.5px;color:var(--muted);font-family:var(--mono);
  border:1px solid var(--border);border-radius:5px;padding:1px 6px}
.presults{overflow-y:auto;padding:8px}
.pgroup{font-size:10.5px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;
  color:var(--muted);padding:9px 10px 5px}
.phit{
  display:flex;gap:11px;align-items:center;padding:8px 11px;border-radius:10px;
  cursor:pointer;font-size:13.4px;color:var(--text-2);
}
.phit:hover,.phit.sel{background:var(--accent-soft);color:var(--text)}
.phit .kind{flex:0 0 auto;font-size:10.5px;font-family:var(--mono);border-radius:6px;
  padding:1px 7px;background:var(--surface-2);color:var(--muted);border:1px solid var(--border)}
.phit code{background:transparent;border:0;padding:0;color:var(--text);
  font-size:12.6px;white-space:pre-wrap;word-break:break-all}
.phit .where{margin-left:auto;flex:0 0 auto;font-size:11px;color:var(--muted);
  max-width:34%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.pempty{padding:26px 16px;text-align:center;color:var(--muted);font-size:13px}

/* 移动端 */
.hamburger{display:none;position:fixed;top:12px;left:12px;z-index:70;width:40px;height:40px;
  border-radius:11px;border:1px solid var(--border);background:var(--surface);
  color:var(--text-2);font-size:17px;cursor:pointer;box-shadow:var(--shadow)}
.scrim{display:none;position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:59}
@media (max-width:1100px){
  :root{--sidebar:290px}
  .doc{padding:0 26px 120px}
}
@media (max-width:900px){
  .sidebar{transform:translateX(-102%);transition:transform .22s ease}
  body.nav-open .sidebar{transform:none}
  body.nav-open .scrim{display:block}
  .wrap{margin-left:0}
  .hamburger{display:block}
  .hero{padding-top:72px}
  .hero h1{font-size:1.95rem}
  .doc{padding:0 18px 110px}
  .arch-grid{grid-template-columns:1fr}
  .arch-mid{padding:12px 0}
  .arch-mid .wire{width:2px;height:34px;background:linear-gradient(var(--accent),var(--green))}
  .arch-mid .wire::before{top:-2px;left:-3px}
  .arch-mid .wire::after{top:auto;bottom:-2px;left:-3px}
}
@media print{
  .sidebar,.hamburger,.totop,.overlay,.progress,.copy,.anchor{display:none!important}
  .wrap{margin:0}
  .doc{padding:0;max-width:none}
  .qa>.answer{display:block!important}
  .qa{border:0;box-shadow:none;page-break-inside:avoid}
  pre,.tw,.figure{box-shadow:none}
  body{font-size:11pt}
}
</style>
</head>
<body>

<div class="progress"><i id="bar"></i></div>
<button class="hamburger" id="hamburger" aria-label="打开目录">☰</button>
<div class="scrim" id="scrim"></div>

<aside class="sidebar" id="sidebar">
  <div class="brand">
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path fill="currentColor" d="M6.2 10.1a5.8 5.8 0 0 1 11.6 0v6.3a2 2 0 0 1-2 2H8.2a2 2 0 0 1-2-2z"/>
      <circle cx="9.4" cy="12.6" r="1.05" fill="#fff"/>
      <circle cx="14.6" cy="12.6" r="1.05" fill="#fff"/>
      <path d="M7.6 4.6 9.2 7.2M16.4 4.6 14.8 7.2" stroke="currentColor"
            stroke-width="1.6" stroke-linecap="round" fill="none"/>
    </svg>
    <div>
      <b>ADB 实战手册</b>
      <em>原理 · 企业级 · 面试</em>
    </div>
  </div>

  <div class="side-tools">
    <button class="searchbtn" id="openSearch">
      <span>🔍</span><span>搜索章节 / 命令</span>
      <kbd id="kbdHint">Ctrl K</kbd>
    </button>
  </div>

  <nav class="toc" id="toc">
<!--TOC-->
  </nav>

  <div class="side-foot">
    <button class="mini" id="expandAll" title="展开全部面试题">展开</button>
    <button class="mini" id="collapseAll" title="收起全部面试题">收起</button>
    <span class="spacer"></span>
    <button class="mini icon" id="fsDown" title="减小字号">A−</button>
    <button class="mini icon" id="fsUp" title="增大字号">A+</button>
    <button class="mini icon" id="themeBtn" title="切换主题">🌙</button>
  </div>
</aside>

<div class="wrap">
<main class="doc" id="doc">

  <header class="hero">
    <h1>__TITLE__</h1>
    <p class="lede">__LEDE__</p>
    <div class="stats">
      <span class="stat"><b>9</b> 个章节</span>
      <span class="stat"><b>200+</b> 条命令</span>
      <span class="stat"><b>__QACOUNT__</b> 道面试题</span>
      <span class="stat"><b>__SCENECOUNT__</b> 道场景设计题</span>
      <span class="stat"><b>5</b> 级自愈模型</span>
    </div>

    <div class="paths">
<!--PATHS-->
    </div>
  </header>

<!--CONTENT-->

  <footer class="doc-foot">
    <span>共 __QACOUNT__ 道面试题 · __SCENECOUNT__ 道场景设计题 · 单文件离线可用</span>
    <span>按 <kbd>Ctrl</kbd>+<kbd>K</kbd> 搜索 · 按 <kbd>Esc</kbd> 关闭</span>
  </footer>

</main>
</div>

<button class="totop" id="totop" aria-label="回到顶部">↑</button>

<div class="overlay" id="overlay">
  <div class="palette" role="dialog" aria-modal="true">
    <div class="pin">
      <span>🔍</span>
      <input id="pq" type="text" placeholder="输入命令片段或章节名，例如 reverse / bugreport / 设备农场" autocomplete="off" spellcheck="false">
      <span class="esc">Esc</span>
    </div>
    <div class="presults" id="presults"></div>
  </div>
</div>

<script>
(function () {
  "use strict";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  /* 标题上挂了锚点链接, 取纯文本时必须先摘掉, 否则搜索结果会多出一个 # */
  function hTitle(h) {
    var c = h.cloneNode(true);
    $$(".anchor", c).forEach(function (a) { if (a.parentNode) a.parentNode.removeChild(a); });
    return c.textContent.replace(/\s+/g, " ").trim();
  }

  /* ---------------- 主题 ---------------- */
  var root = document.documentElement;
  var saved = null;
  try { saved = localStorage.getItem("adb-blog-theme"); } catch (e) {}
  var prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  setTheme(saved || (prefersDark ? "dark" : "light"));

  function setTheme(t) {
    root.setAttribute("data-theme", t);
    var btn = $("#themeBtn");
    if (btn) btn.textContent = t === "dark" ? "☀️" : "🌙";
    try { localStorage.setItem("adb-blog-theme", t); } catch (e) {}
  }
  $("#themeBtn").addEventListener("click", function () {
    setTheme(root.getAttribute("data-theme") === "dark" ? "light" : "dark");
  });

  /* ---------------- 字号 ---------------- */
  var base = parseInt(localStorage.getItem("adb-blog-fs") || "16", 10);
  applyFs();
  function applyFs() {
    base = Math.min(21, Math.max(13, base));
    root.style.setProperty("--base", base + "px");
    try { localStorage.setItem("adb-blog-fs", String(base)); } catch (e) {}
  }
  $("#fsUp").addEventListener("click", function () { base += 1; applyFs(); });
  $("#fsDown").addEventListener("click", function () { base -= 1; applyFs(); });

  /* ---------------- 代码高亮 + 复制 ---------------- */
  var CMDRE = /^[A-Za-z_][A-Za-z0-9_.\-]*$/;

  function escHtml(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function tokenize(src) {
    var re = /(#[^\n]*)|("(?:[^"\\\n]|\\.)*"|'(?:[^'\\\n]|\\.)*')|(\$\{[A-Za-z_]\w*\}|\$[A-Za-z_]\w*|\$[0-9?!#@*])|(\s-{1,2}[A-Za-z][\w-]*)|(\b\d+(?:\.\d+)?\b)/g;
    var out = [], last = 0, m;
    while ((m = re.exec(src)) !== null) {
      if (m.index > last) out.push({ t: "p", v: src.slice(last, m.index) });
      var type = m[1] ? "m" : m[2] ? "s" : m[3] ? "v" : m[4] ? "f" : "n";
      out.push({ t: type, v: m[0] });
      last = m.index + m[0].length;
      if (m[0].length === 0) re.lastIndex++;
    }
    if (last < src.length) out.push({ t: "p", v: src.slice(last) });
    return out;
  }

  function markCommands(tokens) {
    var out = [], atStart = true, i, tk, s, buf, ch, mm, j;
    for (i = 0; i < tokens.length; i++) {
      tk = tokens[i];
      if (tk.t !== "p") {
        out.push(tk);
        atStart = false;
        continue;
      }
      s = tk.v; buf = ""; j = 0;
      while (j < s.length) {
        ch = s.charAt(j);
        if (atStart) {
          mm = CMDRE.exec(s.slice(j));
          if (mm) {
            if (buf) { out.push({ t: "p", v: buf }); buf = ""; }
            out.push({ t: "c", v: mm[0] });
            j += mm[0].length; atStart = false; continue;
          }
          if (ch === " " || ch === "\t" || ch === "\n") { buf += ch; j++; continue; }
          atStart = false;
        }
        if (ch === "\n") { atStart = true; buf += ch; j++; continue; }
        if (ch === "|" || ch === ";" || ch === "&") {
          while (j < s.length && (s.charAt(j) === "|" || s.charAt(j) === ";" || s.charAt(j) === "&")) {
            buf += s.charAt(j); j++;
          }
          atStart = true; continue;
        }
        buf += ch; j++;
      }
      if (buf) out.push({ t: "p", v: buf });
    }
    return out;
  }

  function render(code) {
    var src = code.textContent;
    var cls = code.className || "";
    /* text / console 是「原文输出」，不做 shell 语法着色，避免把 List、adb: 之类误判成命令 */
    if (/language-(text|console)/.test(cls)) return;
    if (!/language-(bash|sh|shell|zsh|powershell|ps1)/.test(cls)) return;
    var toks = markCommands(tokenize(src));
    var buf = "";
    for (var i = 0; i < toks.length; i++) {
      var v = escHtml(toks[i].v);
      buf += toks[i].t === "p" ? v : '<span class="tok-' + toks[i].t + '">' + v + "</span>";
    }
    code.innerHTML = buf;
  }

  $$("pre").forEach(function (pre) {
    var code = pre.querySelector("code");
    if (!code) return;
    render(code);
    var m = /language-([\w-]+)/.exec(code.className || "");
    var head = document.createElement("div");
    head.className = "pre-head";
    head.innerHTML = '<span class="dots"><i></i><i></i><i></i></span><span class="lang">'
      + (m ? m[1] : "text") + "</span>";
    var btn = document.createElement("button");
    btn.className = "copy";
    btn.type = "button";
    btn.textContent = "复制";
    btn.addEventListener("click", function () {
      var txt = code.textContent;
      var done = function () {
        btn.textContent = "已复制"; btn.classList.add("done");
        setTimeout(function () { btn.textContent = "复制"; btn.classList.remove("done"); }, 1500);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(txt).then(done, fallback);
      } else { fallback(); }
      function fallback() {
        var ta = document.createElement("textarea");
        ta.value = txt; ta.style.position = "fixed"; ta.style.opacity = "0";
        document.body.appendChild(ta); ta.select();
        try { document.execCommand("copy"); done(); } catch (e) { btn.textContent = "复制失败"; }
        document.body.removeChild(ta);
      }
    });
    head.appendChild(btn);
    pre.insertBefore(head, code);
  });

  /* ---------------- 路径卡片定位 ---------------- */
  $$("[data-h]").forEach(function (el) {
    var key = el.getAttribute("data-h");
    var hit = $$("h2,h3").filter(function (h) {
      return h.textContent.replace(/\s+/g, " ").trim().indexOf(key) === 0;
    })[0];
    if (hit) el.setAttribute("href", "#" + hit.id);
  });

  /* ---------------- 滚动高亮 + 进度 + 回到顶部 ---------------- */
  var heads = $$(".doc h2, .doc h3");
  var links = $$(".toc a");
  var linkMap = {};
  links.forEach(function (a) { linkMap[a.getAttribute("data-target")] = a; });

  var bar = $("#bar"), totop = $("#totop"), ticking = false;

  function onScroll() {
    var y = window.scrollY || document.documentElement.scrollTop;
    var h = document.documentElement.scrollHeight - window.innerHeight;
    bar.style.width = (h > 0 ? Math.min(100, (y / h) * 100) : 0) + "%";
    totop.classList.toggle("show", y > 600);

    var cur = null;
    for (var i = 0; i < heads.length; i++) {
      if (heads[i].getBoundingClientRect().top <= 120) cur = heads[i]; else break;
    }
    if (!cur) cur = heads[0];
    if (cur) {
      links.forEach(function (a) { a.classList.remove("active"); });
      var a2 = linkMap[cur.id];
      if (a2) {
        a2.classList.add("active");
        var grp = a2.closest(".toc-group");
        if (grp) {
          $$(".toc-group.open").forEach(function (g) { if (g !== grp) g.classList.remove("open"); });
          grp.classList.add("open");
          /* 仅当激活项跑出侧栏可视区时才滚动它, 且用 rect 计算(offsetTop 相对的是文档而非滚动容器) */
          var box = $("#toc");
          var ar = a2.getBoundingClientRect(), br = box.getBoundingClientRect();
          if (ar.top < br.top + 12 || ar.bottom > br.bottom - 12) {
            box.scrollTo({
              top: box.scrollTop + (ar.top - br.top) - box.clientHeight / 2 + ar.height / 2,
              behavior: "smooth"
            });
          }
        }
      }
    }
    ticking = false;
  }
  window.addEventListener("scroll", function () {
    if (!ticking) { ticking = true; window.requestAnimationFrame(onScroll); }
  }, { passive: true });
  onScroll();

  totop.addEventListener("click", function () { window.scrollTo({ top: 0, behavior: "smooth" }); });

  // 默认展开当前章节
  var firstActive = $(".toc a.active");
  if (firstActive && firstActive.closest(".toc-group")) firstActive.closest(".toc-group").classList.add("open");

  /* ---------------- 面试题展开 / 收起 ---------------- */
  $$("#expandAll").forEach(function (b) {
    b.addEventListener("click", function () { $$("details.qa").forEach(function (d) { d.open = true; }); });
  });
  $$("#collapseAll").forEach(function (b) {
    b.addEventListener("click", function () { $$("details.qa").forEach(function (d) { d.open = false; }); });
  });
  /* 不做「打开一个自动关掉其他」的手风琴: 那会让「展开全部」立刻被自己撤销,
     也会关掉读者主动打开的题, 阅读体验反而更差。折叠态交给用户。 */

  /* ---------------- 标题锚点(悬停出现, 点击复制深链) ---------------- */
  $$(".doc h2, .doc h3").forEach(function (h) {
    var a = document.createElement("a");
    a.className = "anchor";
    a.href = "#" + h.id;
    a.textContent = "#";
    a.title = "复制本段链接";
    a.addEventListener("click", function (e) {
      e.preventDefault();
      var url = location.href.split("#")[0] + "#" + h.id;
      history.replaceState(null, "", "#" + h.id);
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(function () {
          a.classList.add("done");
          setTimeout(function () { a.classList.remove("done"); }, 1200);
        }, function () {});
      }
      h.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    h.appendChild(a);
  });

  /* ---------------- 搜索面板 ---------------- */
  var index = [];
  $$(".doc pre").forEach(function (pre) {
    var code = pre.querySelector("code");
    if (!code) return;
    var secTitle = "", secId = "";
    var node = pre;
    while (node && node !== document.body) {
      node = node.previousElementSibling;
      while (node) {
        if (/^H[23]$/.test(node.tagName)) { secTitle = hTitle(node); secId = node.id; break; }
        node = node.previousElementSibling;
      }
      if (secTitle) break;
      node = pre.parentElement;
      break;
    }
    if (!secTitle) {
      var anc = pre.closest("details, section, div");
      while (anc && !secTitle) {
        var p = anc.previousElementSibling;
        while (p) {
          if (/^H[23]$/.test(p.tagName)) { secTitle = hTitle(p); secId = p.id; break; }
          p = p.previousElementSibling;
        }
        anc = anc.parentElement;
      }
    }
    code.textContent.split("\n").forEach(function (line) {
      var t = line.trim();
      if (t.length < 3) return;
      index.push({ line: t, title: secTitle || "正文", id: secId || "", el: pre, hay: t.toLowerCase() });
    });
  });

  var headings = $$(".doc h2, .doc h3").map(function (h) {
    return { title: hTitle(h), id: h.id, level: h.tagName === "H2" ? 2 : 3 };
  });

  var overlay = $("#overlay"), input = $("#pq"), results = $("#presults");
  var sel = -1;

  function openPalette() {
    overlay.classList.add("show");
    input.value = "";
    renderResults("");
    setTimeout(function () { input.focus(); }, 20);
  }
  function closePalette() {
    overlay.classList.remove("show");
    sel = -1;
  }
  $("#openSearch").addEventListener("click", openPalette);
  overlay.addEventListener("click", function (e) { if (e.target === overlay) closePalette(); });

  var isMac = /Mac|iPhone|iPad/.test(navigator.platform || "");
  $("#kbdHint").textContent = isMac ? "⌘ K" : "Ctrl K";

  document.addEventListener("keydown", function (e) {
    var k = e.key.toLowerCase();
    if ((e.ctrlKey || e.metaKey) && k === "k") { e.preventDefault(); openPalette(); return; }
    if (e.key === "/" && !/input|textarea/i.test((e.target.tagName || ""))) { e.preventDefault(); openPalette(); return; }
    if (!overlay.classList.contains("show")) return;
    if (e.key === "Escape") { closePalette(); }
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      var hits = $$(".phit", results);
      if (!hits.length) return;
      sel = (sel + (e.key === "ArrowDown" ? 1 : -1) + hits.length) % hits.length;
      hits.forEach(function (h, i) { h.classList.toggle("sel", i === sel); });
      hits[sel].scrollIntoView({ block: "nearest" });
    }
    if (e.key === "Enter") {
      var cur = $(".phit.sel", results) || $(".phit", results);
      if (cur) cur.click();
    }
  });

  function score(item, q) {
    var i = item.hay.indexOf(q);
    if (i < 0) return -1;
    return i === 0 ? 0 : i;
  }

  function renderResults(q) {
    q = q.trim().toLowerCase();
    var hHits = [], cHits = [];
    if (q) {
      hHits = headings.filter(function (h) { return h.title.toLowerCase().indexOf(q) >= 0; }).slice(0, 6);
      var seen = {};
      cHits = index
        .map(function (it) { return { it: it, s: score(it, q) }; })
        .filter(function (o) { return o.s >= 0; })
        .sort(function (a, b) { return a.s - b.s || a.it.line.length - b.it.line.length; })
        .filter(function (o) {
          if (seen[o.it.line]) return false;
          seen[o.it.line] = 1; return true;
        })
        .slice(0, 40)
        .map(function (o) { return o.it; });
    } else {
      hHits = headings.filter(function (h) { return h.level === 2; }).slice(0, 9);
    }

    var html = "";
    if (hHits.length) {
      html += '<div class="pgroup">章节</div>';
      hHits.forEach(function (h) {
        html += '<div class="phit" data-jump="#' + h.id + '">'
          + '<span class="kind">§</span><code>' + escHtml(h.title) + "</code></div>";
      });
    }
    if (cHits.length) {
      html += '<div class="pgroup">命令 ' + (q ? "（" + cHits.length + " 条）" : "") + "</div>";
      cHits.forEach(function (it) {
        html += '<div class="phit" data-line="' + escHtml(it.line) + '">'
          + '<span class="kind">$</span><code>' + escHtml(it.line) + "</code>"
          + '<span class="where">' + escHtml(it.title) + "</span></div>";
      });
    }
    results.innerHTML = html || '<div class="pempty">没有匹配结果，试试 <code>reverse</code> / <code>logcat</code> / <code>设备农场</code></div>';
    sel = -1;

    $$(".phit", results).forEach(function (hit) {
      hit.addEventListener("click", function () {
        var jump = hit.getAttribute("data-jump");
        closePalette();
        if (jump) { location.hash = jump; return; }
        var line = hit.getAttribute("data-line");
        var target = null;
        for (var i = 0; i < index.length; i++) {
          if (index[i].line === line) { target = index[i]; break; }
        }
        if (target) {
          var d = target.el.closest("details");
          if (d) d.open = true;
          target.el.scrollIntoView({ behavior: "smooth", block: "center" });
          target.el.style.transition = "box-shadow .3s";
          target.el.style.boxShadow = "0 0 0 3px var(--accent)";
          setTimeout(function () { target.el.style.boxShadow = ""; }, 1600);
        }
      });
    });
  }

  input.addEventListener("input", function () { renderResults(input.value); });

  /* ---------------- 移动端抽屉 ---------------- */
  $("#hamburger").addEventListener("click", function () { document.body.classList.toggle("nav-open"); });
  $("#scrim").addEventListener("click", function () { document.body.classList.remove("nav-open"); });
  $$(".toc a").forEach(function (a) {
    a.addEventListener("click", function () { document.body.classList.remove("nav-open"); });
  });
})();
</script>
</body>
</html>
"""

page = (
    page.replace("__TITLE__", esc(doc_title or TITLE))
    .replace("__DESC__", esc(DESC))
    .replace("__LEDE__", esc(lede or SUBTITLE))
    .replace("__QACOUNT__", str(qa_count))
    .replace("__SCENECOUNT__", str(scene_count))
    .replace("<!--TOC-->", TOC_HTML)
    .replace("<!--PATHS-->", PATHS_HTML)
    .replace("<!--CONTENT-->", body)
)

with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write(page)

print("QA:", qa_count, "SCENE:", scene_count)
print("TOC entries:", len(TOC_HTML.split("<a ")) - 1)
print("HTML chars:", len(page))
print("OUT:", OUT)
