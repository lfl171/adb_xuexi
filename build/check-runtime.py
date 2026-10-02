# -*- coding: utf-8 -*-
"""用 --dump-dom 检查前端脚本是否完整执行(靠注入产物判断, 越靠后越能证明没抛异常)。"""
import os
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
SRC = os.path.join(ROOT, "ADB从入门到企业级实战与面试指南.html")
PROFILE = os.path.join(tempfile.gettempdir(), "dsh-adb-blog-edgeshot")

p = subprocess.run([
    EDGE, "--headless=new", "--disable-gpu", "--no-sandbox", "--no-first-run",
    "--user-data-dir=" + PROFILE,
    "--virtual-time-budget=8000", "--dump-dom",
    "file:///" + SRC.replace("\\", "/"),
], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
dom = p.stdout.decode("utf-8", "replace")

checks = [
    ("代码块头部注入(pre-head)", dom.count('class="pre-head"'), 49),
    ("复制按钮注入(copy)", dom.count('class="copy"'), 49),
    ("语法着色(token span)", dom.count('class="tok-') > 200, True),
    ("标题锚点注入(anchor)", dom.count('class="anchor"'), 54),
    ("未解析的路径卡片 href=\"#\"", dom.count('href="#"'), 0),
    ("已解析的路径卡片(真实锚点)", len([x for x in
        ["#1-原理篇", "#3-基础篇", "#5-企业级篇", "#6-面试篇"] if x in dom]), 4),
]
ok = True
for name, got, want in checks:
    flag = "OK  " if got == want else "!!! "
    if got != want:
        ok = False
    print("%s%-26s got=%-6s want=%s" % (flag, name, got, want))

print("\nRESULT:", "all injected" if ok else "SOMETHING FAILED")
