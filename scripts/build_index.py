#!/usr/bin/env python3
"""聚合索引生成器。

把 data/entries/*.json 合成两个产物：
  1. data/index.json     —— 给机器读（API、外部复用）
  2. site/data/index.js  —— 给浏览器读（包成 JS 变量，绕开 fetch 的跨域/file 限制）

产物由 CI 自动提交，**不要手改**。
"""

import os
import sys
from collections import Counter
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from entrylib import INDEX_PATH, SITE_INDEX_JS, load_entries  # noqa: E402

SORTERS = {
    "new": lambda e: e.get("updatedAt") or "",
    "score": lambda e: e.get("score") or 0,
    "code": lambda e: e.get("code") or "",
}


def build():
    entries = load_entries()
    for e in entries:
        e.setdefault("tags", [])
        e.setdefault("actors", [])
        e.setdefault("recommendations", [])

    entries.sort(key=SORTERS["new"], reverse=True)

    tag_counter = Counter(t for e in entries for t in e["tags"])
    actor_counter = Counter(a for e in entries for a in e["actors"])
    logins = {r.get("login") for e in entries for r in e["recommendations"] if r.get("login")}

    payload = {
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": len(entries),
        "recommenderCount": len(logins),
        "tags": [[t, c] for t, c in tag_counter.most_common(60)],
        "actors": [[a, c] for a, c in actor_counter.most_common(40)],
        "entries": entries,
    }
    return payload


def write(payload):
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    import json
    with open(INDEX_PATH, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    os.makedirs(os.path.dirname(SITE_INDEX_JS), exist_ok=True)
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    # 防止数据里出现 </script> 把标签提前闭合
    body = body.replace("</", "<\\/")
    with open(SITE_INDEX_JS, "w", encoding="utf-8") as fh:
        fh.write("/* 自动生成，请勿手改。源文件：data/entries/*.json */\n")
        fh.write(f"window.__CODES__ = {body};\n")


if __name__ == "__main__":
    p = build()
    write(p)
    print(f"✅ 已聚合 {p['count']} 条 · {p['recommenderCount']} 位推荐人 · {len(p['tags'])} 个标签")
    print(f"   → {INDEX_PATH}")
    print(f"   → {SITE_INDEX_JS}")
