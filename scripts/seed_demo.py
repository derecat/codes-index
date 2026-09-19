#!/usr/bin/env python3
"""生成示例数据，让站点一上线就不是空白页。

不想要示例数据？删掉即可：
    rm -f data/entries/*.json
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from entrylib import dump_json, entry_path, validate_raw  # noqa: E402

DEMO = [
    {
        "code": "ABC-101", "title": "雨夜电车", "studio": "演示厂牌",
        "actors": ["示例演员甲"], "tags": ["剧情", "悬疑", "长镜头"],
        "releaseDate": "2023-06-12", "score": 8.7,
        "reason": "全片只有一个场景，靠对话推进了九十分钟，最后十分钟的镜头运动是教科书级别。",
        "submittedBy": "demo-bot",
        "sourceUrl": "https://example.com/works/abc-101",
        "recommendations": [
            {
                "login": "demo-bot",
                "reason": "全片只有一个场景，靠对话推进了九十分钟，最后十分钟的镜头运动是教科书级别。",
                "score": 9,
            },
            {
                "login": "another-fan",
                "reason": "台词密度极高，二刷才发现前半段每句闲聊都在埋伏笔。适合戴耳机看。",
                "score": 8.4,
            },
        ],
    },
    {
        "code": "XYZ-220", "title": "夏日回声", "studio": "演示厂牌",
        "actors": ["示例演员乙", "示例演员丙"], "tags": ["治愈", "校园", "复古"],
        "releaseDate": "2021-08-20", "score": 9.2,
        "reason": "明线是青春，暗线是一次告别。配乐用了大量环境音，安静得能听见呼吸。",
        "submittedBy": "demo-bot",
    },
    {
        "code": "MNO-338", "title": "第七次走廊", "tags": ["悬疑", "都市"],
        "releaseDate": "2022-11-03", "score": 7.8,
        "reason": "循环叙事但没玩概念，每一轮都在补细节。喜欢烧脑但讨厌故弄玄虚的可以看。",
        "submittedBy": "demo-bot",
    },
    {
        "code": "QRS-451", "title": "沉入水底的信", "tags": ["剧情"],
        "actors": ["示例演员丁"], "releaseDate": "2020-02-14", "score": 8.0,
        "reason": "前四十分钟节奏慢，撑过去之后情绪是层层叠上来的。反派演技明显高于主角。",
        "submittedBy": "demo-bot",
    },
    {
        "code": "TUV-562", "title": "深夜食堂的常客", "tags": ["治愈", "都市", "喜剧"],
        "releaseDate": "2024-01-09", "score": 7.5,
        "reason": "不需要动脑的下饭菜，胜在台词自然。适合当背景音，认真看会有点寡淡。",
        "submittedBy": "demo-bot",
    },
    {
        "code": "WXY-673", "title": "档案室第九格", "tags": ["悬疑", "制服"],
        "releaseDate": "2023-09-27", "score": 8.4,
        "reason": "美术和置景是最大加分项，每个道具都在剧情里回收。摄影偏冷调，很喜欢。",
        "submittedBy": "demo-bot",
    },
    {
        "code": "DEF-784", "title": "逆光而行", "tags": ["剧情", "高颜值"],
        "actors": ["示例演员戊"], "releaseDate": "2019-05-30", "score": 6.9,
        "reason": "剧本一般，但演员撑住了。只想看表演的话值得，冲剧情去的会失望。",
        "submittedBy": "demo-bot",
    },
    {
        "code": "GHI-895", "title": "午夜便利店", "tags": ["都市", "喜剧"],
        "releaseDate": "2025-03-11", "score": 8.1,
        "reason": "群像写得很扎实，七个夜班店员各有各的执念。配角比主线好看。",
        "submittedBy": "demo-bot",
    },
]


def main():
    ok = 0
    for raw in DEMO:
        clean, errors, warns = validate_raw(raw, origin=raw["code"])
        if errors:
            print(f"❌ {raw['code']}: {errors}")
            continue
        dump_json(clean, entry_path(clean["code"]))
        ok += 1
    print(f"✅ 写入 {ok} 条示例数据到 data/entries/（删掉即可清空）")


if __name__ == "__main__":
    main()
