#!/usr/bin/env python3
"""Issue 投稿 → 数据文件。

GitHub Issue Forms 提交后，正文是一段固定格式的 Markdown：

    ### 车牌号

    SSIS-123

    ### 作品标题

    xxx

本脚本把它还原成字段对象，校验后写入 data/entries/<番号>.json。
番号已存在则执行合并（多人推荐累积，同账号改票）。

环境变量（由 workflow 注入，避免把用户输入直接拼进命令里造成注入）：
    ISSUE_BODY     Issue 正文
    ISSUE_AUTHOR   提交者 GitHub 用户名
    ISSUE_NUMBER   Issue 编号
    GITHUB_OUTPUT  Actions 输出文件（自动存在）
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from entrylib import (  # noqa: E402
    EMPTY_TOKENS, clean_text, dump_json, entry_path, load_entries, merge_entry,
    validate_raw,
)

# 表单里的 label → 内部字段名。去掉括注后精确匹配，改表单时这里也要同步改。
LABEL_MAP = {
    "车牌号": "code",
    "作品标题": "title",
    "演员": "actors",
    "标签": "tags",
    "厂牌": "studio",
    "发行日期": "releaseDate",
    "评分": "score",
    "推荐理由": "reason",
    "来源链接": "sourceUrl",
    "提交前确认": "ack",
}


def strip_parens(s: str) -> str:
    return re.sub(r"[（(].*?[)）]", "", s).strip()


def parse_issue_body(body: str) -> dict:
    """把 Issue 正文解析成 {字段: 原值}。"""
    out, key = {}, None
    for line in (body or "").splitlines():
        m = re.match(r"^#{2,3}\s+(.+?)\s*$", line)
        if m:
            key = LABEL_MAP.get(strip_parens(m.group(1)))
            if key:
                out[key] = []
            continue
        if key is not None:
            out[key].append(line)

    fields = {}
    for k, lines in out.items():
        if k == "ack":
            fields[k] = "\n".join(lines)
        else:
            fields[k] = clean_text("\n".join(lines), 1000)
    return fields


def main() -> int:
    body = os.environ.get("ISSUE_BODY", "")
    author = os.environ.get("ISSUE_AUTHOR", "anonymous")
    number = os.environ.get("ISSUE_NUMBER", "0")

    fields = parse_issue_body(body)

    # 1. 确认勾选框
    ack = (fields.get("ack") or "").lower()
    if "[x]" not in ack:
        print("❌ 没有勾选「不含任何资源链接」的确认框", file=sys.stderr)
        return 1

    # 2. 组装原始数据
    raw = {
        "code": fields.get("code", ""),
        "title": fields.get("title", ""),
        "actors": fields.get("actors", ""),
        "tags": fields.get("tags", ""),
        "studio": fields.get("studio", ""),
        "releaseDate": fields.get("releaseDate", ""),
        "score": fields.get("score", ""),
        "reason": fields.get("reason", ""),
        "sourceUrl": fields.get("sourceUrl", ""),
        "submittedBy": author,
    }

    if not raw["code"] or raw["code"].lower() in EMPTY_TOKENS:
        print("❌ 车牌号不能为空 —— 是不是表单没填完？", file=sys.stderr)
        return 1

    clean, errors, warnings = validate_raw(raw, origin=f"Issue #{number}")
    for w in warnings:
        print(f"⚠️  {w}")
    if errors:
        for e in errors:
            print(f"❌ {e}", file=sys.stderr)
        print("\n提示：直接编辑 Issue 内容即可自动重试。", file=sys.stderr)
        return 1

    # 3. 写入或合并
    path = entry_path(clean["code"])
    if os.path.exists(path):
        import json
        with open(path, encoding="utf-8") as fh:
            old = json.load(fh)
        if any(r["login"] == author for r in old.get("recommendations") or []):
            print(f"ℹ️  {author} 之前推荐过 {clean['code']}，本次视为改票")
        merged = merge_entry(old, clean)
        dump_json(merged, path)
        verb = "更新"
        total = len(merged["recommendations"])
    else:
        dump_json(clean, path)
        verb = "新增"
        total = len(clean["recommendations"])

    print(f"✅ {verb} {clean['code']} → {path}（累计 {total} 人推荐）")

    # 4. 把结果透给 workflow，用于回执评论
    out_file = os.environ.get("GITHUB_OUTPUT")
    if out_file:
        with open(out_file, "a", encoding="utf-8") as fh:
            fh.write(f"code={clean['code']}\n")
            fh.write(f"verb={verb}\n")
            fh.write(f"total={total}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
