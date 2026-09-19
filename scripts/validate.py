#!/usr/bin/env python3
"""数据校验器。

用法：
    python3 scripts/validate.py                     # 校验整个库里所有条目
    python3 scripts/validate.py a.json b.json       # 只校验指定文件
    python3 scripts/validate.py --strict            # 把 warning 也当成错误

退出码 0 = 通过，1 = 有问题（CI 会因此标红）。
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from entrylib import ENTRIES_DIR, ROOT, normalize_code, validate_raw  # noqa: E402


def rel(p):
    return os.path.relpath(p, ROOT)


def main(argv):
    strict = "--strict" in argv
    targets = [a for a in argv if not a.startswith("--")]

    if targets:
        files = []
        for t in targets:
            if os.path.isdir(t):
                files += [os.path.join(t, f) for f in sorted(os.listdir(t)) if f.endswith(".json")]
            elif t.strip():
                files.append(t)
    else:
        files = [os.path.join(ENTRIES_DIR, f)
                 for f in sorted(os.listdir(ENTRIES_DIR))] if os.path.isdir(ENTRIES_DIR) else []

    if not files:
        print("· 没有需要校验的文件")
        return 0

    errors, warnings, codes = [], [], {}
    for path in files:
        if not os.path.exists(path):
            errors.append(f"{rel(path)}: 文件不存在")
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                raw = json.load(fh)
        except json.JSONDecodeError as e:
            errors.append(f"{rel(path)}: JSON 语法错误 → {e}")
            continue

        clean, errs, warns = validate_raw(raw, origin=rel(path))
        errors += errs
        warnings += warns
        if not clean:
            continue

        # 文件名必须等于番号，否则站点链接会错位
        expected = normalize_code(clean["code"]) + ".json"
        if os.path.basename(path) != expected:
            errors.append(f"{rel(path)}: 文件名与番号不一致，应为 {expected}")

        if clean["code"] in codes:
            errors.append(f"{rel(path)}: 番号 {clean['code']} 与 {codes[clean['code']]} 重复")
        codes[clean["code"]] = rel(path)

    for w in warnings:
        print(f"⚠️  {w}")
    for e in errors:
        print(f"❌ {e}")

    print(f"\n检查 {len(files)} 个文件 · {len(codes)} 个番号 · {len(errors)} 个错误 · {len(warnings)} 个警告")
    if errors or (strict and warnings):
        return 1
    print("✅ 全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
