# -*- coding: utf-8 -*-
"""视觉走查 / 预览图生成: 用 Edge 无头模式渲染产物的关键区域。

用法:
    python build/shoot.py            # 生成 preview/ 下的预览图
    python build/shoot.py arch       # 只生成某一项

两个技巧:
  * 无头 --screenshot 总是从文档顶部截起, 所以这里注入脚本把目标章节之前的
    兄弟节点隐藏, 让目标落到视口顶部;
  * 主题由 CSS 变量驱动, 注入 data-theme 就能分别走查浅色/深色两套配色。
"""

import os
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREVIEW = os.path.join(ROOT, "preview")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
SRC = os.path.join(ROOT, "ADB从入门到企业级实战与面试指南.html")
# Edge 的临时用户目录必须放在系统临时区, 否则会在工作目录里留下几百个文件的 .edgeshot
PROFILE = os.path.join(tempfile.gettempdir(), "dsh-adb-blog-edgeshot")

VIEW = """
<script>
window.addEventListener("load", function () {
  var theme = "%(theme)s";
  if (theme) { document.documentElement.setAttribute("data-theme", theme); }
  if (%(open_all)s) {
    document.querySelectorAll("details").forEach(function (d) { d.open = true; });
  }
  %(extra)s
  var el = document.getElementById("%(anchor)s");
  if (!el) return;
  var doc = document.getElementById("doc");
  var kids = Array.prototype.slice.call(doc.children);
  var sec = el;
  while (sec && sec.parentElement !== doc) sec = sec.parentElement;
  var idx = kids.indexOf(sec);
  if (idx > 0) { kids.slice(0, idx).forEach(function (k) { k.style.display = "none"; }); }
  window.scrollTo(0, 0);
});
</script>
</body>"""

SEARCH_JS = """
  document.getElementById("openSearch").click();
  var q = document.getElementById("pq");
  q.value = "reverse";
  q.dispatchEvent(new Event("input"));
"""

# key, 输出文件, 宽, 高, 主题, 锚点, 展开全部折叠块, 额外注入 JS
SHOTS = [
    ("overview", "01-overview-light.png", 1500, 1450, "light", "", False, ""),
    ("arch", "02-arch-light.png", 1500, 900, "light", "1-1-三端架构", False, ""),
    ("interview", "03-interview-light.png", 1500, 1500, "light",
     "6-4-场景设计题重点", True, ""),
    ("search", "04-search-dark.png", 1500, 950, "dark", "", True, SEARCH_JS),
    ("mobile", "05-mobile-drawer.png", 430, 950, "dark", "", False,
     'document.body.classList.add("nav-open");'),
]


def shot(key, out, w, h, theme, anchor, open_all, extra):
    with open(SRC, encoding="utf-8") as f:
        doc = f.read()
    view = os.path.join(ROOT, "_view.html")
    with open(view, "w", encoding="utf-8") as f:
        f.write(doc.replace("</body>", VIEW % {
            "theme": theme, "anchor": anchor,
            "open_all": "true" if open_all else "false", "extra": extra,
        }))
    os.makedirs(PREVIEW, exist_ok=True)
    target = os.path.join(PREVIEW, out)
    subprocess.run([
        EDGE, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
        "--no-first-run", "--force-color-profile=srgb",
        "--user-data-dir=" + PROFILE,
        "--window-size=%d,%d" % (w, h), "--virtual-time-budget=8000",
        "--screenshot=" + target, "file:///" + view.replace("\\", "/"),
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(view)
    print(("OK   %-24s %8d bytes" % (out, os.path.getsize(target)))
          if os.path.exists(target) else "FAIL " + out)


if __name__ == "__main__":
    want = sys.argv[1] if len(sys.argv) > 1 else None
    for s in SHOTS:
        if want and s[0] != want:
            continue
        shot(*s)
