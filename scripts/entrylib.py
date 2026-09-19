"""共享逻辑：番号规范化、条目校验、合并、读写。

被 validate.py / build_index.py / issue_to_entry.py 共同引用，
保证「校验规则」只有一份，不会出现 CI 放行但站点渲染失败的情况。
"""

import json
import os
import re
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTRIES_DIR = os.path.join(ROOT, "data", "entries")
INDEX_PATH = os.path.join(ROOT, "data", "index.json")
SITE_INDEX_JS = os.path.join(ROOT, "site", "data", "index.js")

# ---------------------------------------------------------------- 黑名单
# 命中任意关键词的 sourceUrl 会被直接拒绝，这是仓库的「保命闸门」。
BLOCKED_PATTERNS = (
    "magnet:", "ed2k:", "thunder://", "xunlei", "torrent",
    "pan.baidu.com", "pan.quark.cn", "aliyundrive", "alipan.com",
    "115.com", "weiyun.com", "mega.nz", "pikpak", "t.me/",
    "drive.google.com", "onedrive", "lanzou", "123pan",
    ".mkv", ".mp4", ".avi", ".wmv", ".rmvb", ".iso",
    ".zip", ".rar", ".7z", ".torrent", ".m3u8",
)

EMPTY_TOKENS = {"", "无", "没有", "none", "null", "n/a", "_no response_", "选填"}

CODE_RE = re.compile(r"^[A-Z0-9]+(?:-[A-Z0-9]+)*$")

LIMITS = {
    "title": 120,
    "studio": 40,
    "reason": (4, 200),
    "sourceUrl": 300,
    "tags": 8,
    "actors": 10,
}


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ------------------------------------------------------------ 规范化
def normalize_code(raw: str) -> str:
    """把用户五花八门的写法统一。

    ssis-123 / SSIS_123 / ssis123 / SSIS 123  →  SSIS-123
    """
    s = (raw or "").strip().upper()
    s = s.replace("　", "").replace(" ", "").replace("_", "-")
    s = s.replace("－", "-").replace("—", "-").replace("–", "-")
    s = re.sub(r"[^A-Z0-9\-]", "", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    # 纯字母+数字且没有连字符时，补一个连字符：SSIS123 → SSIS-123
    m = re.fullmatch(r"([A-Z]{1,8})(\d{2,8})", s)
    if m:
        s = f"{m.group(1)}-{m.group(2)}"
    return s


def clean_text(v, limit=None) -> str:
    t = "" if v is None else str(v).strip()
    if t.lower() in EMPTY_TOKENS:
        return ""
    t = re.sub(r"\s+", " ", t)
    return t[:limit] if limit else t


def split_list(v, limit) -> list:
    """把 "甲, 乙、丙 丁" 这类输入切成列表并去重。"""
    if v is None:
        return []
    if isinstance(v, list):
        parts = [str(x) for x in v]
    else:
        parts = re.split(r"[,，、;；/|\n]+", str(v))
    out = []
    for p in parts:
        p = clean_text(p, 40)
        if p and p not in out:
            out.append(p)
    return out[:limit]


def parse_score(v):
    """返回 (score or None, error or None)。"""
    if v is None or str(v).strip().lower() in EMPTY_TOKENS:
        return None, None
    try:
        f = float(str(v).strip().rstrip("分"))
    except ValueError:
        return None, f"评分「{v}」不是数字"
    if not 0 <= f <= 10:
        return None, f"评分 {f} 超出 0–10 范围"
    return round(f, 1), None


def parse_date(v):
    t = clean_text(v)
    if not t:
        return "", None
    m = re.fullmatch(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", t)
    if not m:
        return "", f"日期「{v}」格式不对，应为 2024-03-01"
    y, mo, d = (int(x) for x in m.groups())
    try:
        return f"{y:04d}-{mo:02d}-{d:02d}", None
    except Exception:  # pragma: no cover
        return "", f"日期「{v}」无效"


def check_url(url: str):
    u = clean_text(url, LIMITS["sourceUrl"])
    if not u:
        return "", None
    low = u.lower()
    for bad in BLOCKED_PATTERNS:
        if bad in low:
            return "", f"来源链接命中禁止关键词「{bad}」，本项目不收任何资源链接"
    if not low.startswith(("http://", "https://")):
        return "", "来源链接必须以 http:// 或 https:// 开头"
    return u, None


# ------------------------------------------------------------ 校验
def validate_raw(raw: dict, origin: str = "") -> tuple:
    """把任意来源的原始数据变成合法条目。

    返回 (clean_entry, errors, warnings)。
    clean_entry 为 None 表示硬失败。
    """
    errors, warnings = [], []
    label = origin or "条目"

    if not isinstance(raw, dict):
        return None, [f"{label}: 内容不是合法的 JSON 对象"], []

    code = normalize_code(raw.get("code", ""))
    if not code:
        errors.append(f"{label}: 缺少番号 code")
    elif not CODE_RE.match(code) or not (3 <= len(code) <= 24):
        errors.append(f"{label}: 番号「{raw.get('code')}」格式不合法（规范化后为 {code}）")
    elif not any(c.isdigit() for c in code):
        errors.append(f"{label}: 番号「{code}」必须包含数字")

    reason = clean_text(raw.get("reason"), LIMITS["reason"][1])
    if not reason:
        # 也可能是从 recommendations 里来的
        recs = raw.get("recommendations") or []
        if not recs:
            errors.append(f"{label}: 缺少推荐理由 reason")
    elif len(reason) < LIMITS["reason"][0]:
        errors.append(f"{label}: 推荐理由太短（{len(reason)} 字），至少要 {LIMITS['reason'][0]} 字")
    if reason and re.fullmatch(r"[好棒顶赞推经典牛逼6强]+", reason):
        warnings.append(f"{label}: 推荐理由「{reason}」信息量为零，建议补充具体看点")

    title = clean_text(raw.get("title"), LIMITS["title"])
    studio = clean_text(raw.get("studio"), LIMITS["studio"])
    tags = split_list(raw.get("tags"), LIMITS["tags"])
    actors = split_list(raw.get("actors"), LIMITS["actors"])

    release_date, derr = parse_date(raw.get("releaseDate"))
    if derr:
        warnings.append(f"{label}: {derr}（已忽略该字段）")

    url, uerr = check_url(raw.get("sourceUrl"))
    if uerr:
        errors.append(f"{label}: {uerr}")

    score, serr = parse_score(raw.get("score"))
    if serr:
        warnings.append(f"{label}: {serr}（已忽略该字段）")

    # ---- recommendations：新投稿优先，老条目保留历史
    recs_in = raw.get("recommendations")
    if not recs_in:
        login = clean_text(raw.get("submittedBy") or raw.get("login") or "anonymous", 40)
        recs_in = [{"login": login, "reason": reason, "score": score, "at": now_iso()}]

    recs, seen = [], {}
    for r in recs_in if isinstance(recs_in, list) else []:
        if not isinstance(r, dict):
            continue
        login = clean_text(r.get("login") or r.get("submittedBy") or "anonymous", 40)
        r_reason = clean_text(r.get("reason"), LIMITS["reason"][1])
        if not r_reason:
            continue
        r_score, _ = parse_score(r.get("score"))
        # 同账号只保留最后一条 —— 改主意算改票，不算刷票
        item = {
            "login": login,
            "reason": r_reason,
            "score": r_score,
            "at": clean_text(r.get("at")) or now_iso(),
        }
        if login in seen:
            warnings.append(f"{label}: 用户 {login} 有重复推荐，保留最新一条")
            recs[seen[login]] = item
        else:
            seen[login] = len(recs)
            recs.append(item)

    if not recs:
        errors.append(f"{label}: 没有任何有效的推荐记录")

    if errors:
        return None, errors, warnings

    scores = [r["score"] for r in recs if r["score"] is not None]
    avg = round(sum(scores) / len(scores), 1) if scores else None

    clean = {
        "code": code,
        "title": title,
        "actors": actors,
        "tags": tags,
        "studio": studio,
        "releaseDate": release_date,
        "sourceUrl": url,
        "score": avg,
        "recommendations": recs,
        "createdAt": clean_text(raw.get("createdAt")) or now_iso(),
        "updatedAt": clean_text(raw.get("updatedAt")) or now_iso(),
    }
    return clean, [], warnings


# ------------------------------------------------------------ 合并
def merge_entry(old: dict, new: dict) -> dict:
    """把新投稿合并进已有条目：元数据取并集，推荐人各自保留。"""
    out = dict(old)
    for field in ("title", "studio", "releaseDate", "sourceUrl"):
        if new.get(field):
            out[field] = new[field]
    for field in ("actors", "tags"):
        merged = list(old.get(field) or [])
        for x in new.get(field) or []:
            if x not in merged:
                merged.append(x)
        out[field] = merged[: LIMITS[field]]

    recs = [dict(r) for r in old.get("recommendations") or []]
    index = {r["login"]: i for i, r in enumerate(recs)}
    for r in new.get("recommendations") or []:
        if r["login"] in index:
            recs[index[r["login"]]] = r
        else:
            recs.append(r)
    out["recommendations"] = recs

    scores = [r["score"] for r in recs if r.get("score") is not None]
    out["score"] = round(sum(scores) / len(scores), 1) if scores else None
    out["updatedAt"] = now_iso()
    out["createdAt"] = old.get("createdAt") or now_iso()
    return out


# ------------------------------------------------------------ IO
def entry_path(code: str, base: str = ENTRIES_DIR) -> str:
    return os.path.join(base, f"{code.replace('/', '_')}.json")


def load_entries(base: str = ENTRIES_DIR) -> list:
    if not os.path.isdir(base):
        return []
    out = []
    for name in sorted(os.listdir(base)):
        if not name.endswith(".json") or name.startswith("_"):
            continue
        with open(os.path.join(base, name), encoding="utf-8") as fh:
            out.append(json.load(fh))
    return out


def dump_json(obj, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
