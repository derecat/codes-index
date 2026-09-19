#!/usr/bin/env python3
"""前端自检：确保 app.js 里引用的 DOM id 都在 index.html 里存在。

这类「id 写错一个字 → 页面白屏」的 bug 编译期不报错，
但用户一打开就是空白。用脚本卡住它，比上线后靠肉眼发现便宜得多。

用法：python3 scripts/check_frontend.py
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "site", "index.html")
JS = os.path.join(ROOT, "site", "app.js")
CSS = os.path.join(ROOT, "site", "style.css")

# 动态注入的 id（不来自 index.html，来自 app.js 里拼的字符串）
DYNAMIC = {
    "closeBtn", "copyCode", "resetAll",     # 弹窗内动态生成
    "comments",                              # 弹窗内动态生成
}


def main():
    html = open(HTML, encoding="utf-8").read()
    js = open(JS, encoding="utf-8").read()
    css = open(CSS, encoding="utf-8").read()

    html_ids = set(re.findall(r'\bid="([^"]+)"', html))
    html_ids |= set(re.findall(r'\bid="([^"]+)"', js))       # JS 拼进去的模板
    html_ids |= DYNAMIC

    js_ids = set(re.findall(r"""\$\(['"]#([A-Za-z0-9_-]+)['"]\)""", js))
    js_ids |= set(re.findall(r"""getElementById\(['"]([A-Za-z0-9_-]+)['"]\)""", js))

    errors, warnings = [], []

    missing = sorted(js_ids - html_ids)
    for m in missing:
        errors.append(f"app.js 引用了 #{m}，但 index.html 里找不到这个元素")

    # JS 里动态插入的 class 必须在 CSS 里有定义，否则就是没上色的裸元素
    js_classes = set(re.findall(r'class="([a-zA-Z][a-zA-Z0-9_-]*)', js))
    css_classes = set(re.findall(r'\.([a-zA-Z][a-zA-Z0-9_-]*)', css))
    for c in sorted(js_classes - css_classes):
        warnings.append(f"app.js 用了 .{c}，但 style.css 里没有对应样式")

    # 必须按顺序加载：config.js 提供全局配置，data/index.js 提供数据
    order = re.findall(r'<script src="([^"]+)"', html)
    expect = ["config.js", "data/index.js", "app.js"]
    if order != expect:
        errors.append(f"脚本加载顺序应为 {expect}，实际为 {order}")

    # 亮色主题自检：不应该残留深色底
    if "--bg: #0b0b0e" in css or "--tx: #e9e9ef" in css:
        errors.append("style.css 仍是暗色主题，亮色改造没生效")

    for w in warnings:
        print(f"⚠️  {w}")
    for e in errors:
        print(f"❌ {e}")

    print(f"\n检查 {len(js_ids)} 个 DOM 引用 · {len(js_classes)} 个动态 class · "
          f"{len(errors)} 个错误 · {len(warnings)} 个警告")
    if errors:
        return 1
    print("✅ 前端自检通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
