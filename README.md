# 🎟️ 车牌库 Codes Index

> 一个由社区共同维护的「番号 → 值不值得看」推荐清单。
> **只沉淀元数据 + 一句话推荐理由。不存资源、不传种子、不放下载地址。**

[![投稿](https://img.shields.io/badge/%E6%8A%95%E7%A8%BF-%E7%82%B9%E8%BF%99%E9%87%8C-ffb020)](../../issues/new/choose)
[![数据校验](../../actions/workflows/validate.yml/badge.svg)](../../actions/workflows/validate.yml)

---

## 它解决什么问题

「这车值不值得上」在论坛里永远是碎片化的：有人发帖问，有人回一句「好看」，然后淹没在几百层楼里。
这个项目的思路是——**把口碑变成结构化数据**：一个番号一条记录，多人推荐就多人投票，理由是必填项。

于是它天然具备三个特性：

| 特性 | 怎么做到的 |
| --- | --- |
| 人人可编辑 | 投稿走 GitHub Issue 表单，不懂 git 也能提交 |
| 数据永不失真 | 自动化校验 + 机器入库，人不碰文件 |
| 可自由分发 | 数据是纯 JSON，谁都可以 fork 一份做自己的站 |

---

## 30 秒看懂工作原理

```
投稿人 → Issue 表单 → GitHub Actions 解析校验 → 写入 data/entries/*.json
                                                        ↓
                                      自动重建成 data/index.json
                                                        ↓
                                GitHub Pages 站点自动刷新，全站可搜
```

投稿人只需要：**打开 Issue → 填表单 → 提交 → 机器人自动合并并关帖**。
他从头到尾没碰过一行代码、一个 PR。

---

## 目录结构

```
.
├── data/
│   ├── entries/              # ⭐ 唯一数据源：一个番号一个文件
│   │   ├── ABC-101.json
│   │   └── XYZ-220.json
│   └── index.json            # 自动生成的聚合索引，不要手改
├── site/                     # GitHub Pages 站点（纯静态，零依赖）
│   ├── index.html
│   ├── style.css             # 亮色主题
│   ├── app.js
│   ├── config.js             # ⭐ 站点配置：仓库地址 + giscus 评论
│   └── data/index.js         # 自动生成，把索引包成 JS 变量
├── scripts/
│   ├── entrylib.py           # 共享逻辑：番号规范化 / 校验 / 合并
│   ├── validate.py           # 校验器（CI 用）
│   ├── build_index.py        # 聚合索引生成器
│   ├── issue_to_entry.py     # Issue 正文 → 数据文件
│   ├── check_frontend.py     # 前端自检：DOM 引用、脚本顺序、主题残留
│   └── seed_demo.py          # 生成示例数据
├── schema/entry.schema.json  # JSON Schema，编辑器/CI 都能用
└── .github/
    ├── ISSUE_TEMPLATE/submit.yml   # 投稿表单
    └── workflows/
        ├── issue-to-entry.yml      # Issue → 数据（自动入库）
        ├── validate.yml            # PR / push 数据校验
        └── deploy-pages.yml        # 构建并部署站点
```

### 为什么「一个番号一个文件」？

这是整个项目最关键的一个设计决定。

如果所有人往同一个 `entries.json` 里追加，两个人同时投稿，Git 会在**同一行**产生冲突，
PR 里出现 `<<<<<<< HEAD`，你必须手工解冲突 —— 投稿量一大，维护者会被折磨到弃坑。

拆成一人一文件后，A 改 `ABC-101.json`、B 改 `XYZ-220.json`，**两个改动在物理上不重叠**，
Git 可以自动三方合并，永远不会撞车。代价只是需要一个脚本把它们聚合起来 —— 而我们本来就要跑 CI。

> 这个模式叫 **"file-per-record + build step"**，是开源数据集项目（awesome-xxx 系列、
> shadcn 的 registry、Homebrew 的 formula）通用的做法。记住它，比记住任何语法都值钱。

---

## 数据格式

```jsonc
{
  "code": "ABC-101",              // 番号，必填，会被自动规范化
  "title": "作品标题",             // 选填
  "actors": ["演员甲", "演员乙"],   // 选填，多人推荐时取并集
  "tags": ["剧情", "悬疑"],        // 选填，全站标签云由它生成
  "studio": "厂牌",               // 选填
  "releaseDate": "2024-03-01",    // 选填，YYYY-MM-DD
  "sourceUrl": "https://...",     // 选填，仅限官方/正规页面
  "score": 8.6,                   // 所有推荐人评分的平均值，自动算
  "recommendations": [            // ⭐ 多人推荐就多条记录
    {
      "login": "github-用户名",
      "reason": "剧本完整，前四十分钟铺垫后反转，反派演技在线。",
      "score": 9,
      "at": "2026-09-19T04:00:00Z"
    }
  ],
  "createdAt": "2026-09-19T04:00:00Z",
  "updatedAt": "2026-09-20T09:12:00Z"
}
```

**规则**

- `code`：规范化后形如 `SSIS-123`、`FC2-PPV-1234567`，长度 3–24，必须含数字。
  > ⚠️ **前导零是有意义的**：`MIDE-001` 和 `MIDE-1` 会被当成两条不同的记录。
  > 投稿时请照抄作品上印的编号，别自己省零。
- `reason`：**必填**，4–200 字。写「好看」「推荐」这种废话会被 CI 拦下来。
- 同一个 GitHub 账号对同一个番号只保留最新一条推荐（改主意就重投，算改票不算刷票）。
- `sourceUrl` 命中以下关键词会被直接拒绝：磁力、种子、网盘、`.mkv` / `.mp4` / `.zip` 等。

---

## 部署：四步让它跑起来

### 1. 建仓库并推代码

```bash
# 在 GitHub 上新建一个空仓库，例如 codes-index（不要勾选 README）
git init
git add -A
git commit -m "chore: init codes index"
git branch -M main
git remote add origin git@github.com:<你的用户名>/codes-index.git
git push -u origin main
```

### 2. 打开两个开关

- **Actions 写权限**：`Settings → Actions → General → Workflow permissions`
  选 **Read and write permissions**。
  > 不打开这个，`issue-to-entry.yml` 里的 `git push` 会以 403 收场 —— 这是新手最常见的坑。
- **Pages 源**：`Settings → Pages → Source` 选 **GitHub Actions**（不是 "Deploy from a branch"）。

### 3. 打开 Discussions 并配置评论（可选但强烈建议）

**先开启 Discussions**：`Settings → General → Features → Discussions` 打勾。

然后去 `Discussions` 标签页新建一个分类：

- 名字：`条目讨论`（或你喜欢的）
- 类型：**Announcements** ← 关键，这个类型只有维护者和机器人能发新帖，从源头掐掉灌水

接着装 **giscus App**：打开 https://github.com/apps/giscus → Install → 只授权这一个仓库。

最后去 https://giscus.app 填你的仓库名和分类名，页面底部会生成两段 id，
粘进 `site/config.js`：

```js
giscus: {
  repo: 'yourname/codes-index',
  repoId: 'R_kgDOLxxxxxxx',
  category: '条目讨论',
  categoryId: 'DIC_kwDOLxxxxxxx'
}
```

> **不配也能用。** 四项缺任意一项，评论区会自动变成「去 GitHub 讨论」的链接，
> 不会留一片空白。你可以先把站点跑起来，之后再补。

### 4. 占位符

本项目里所有 `OWNER/REPO` 已经替换为 `derecat/codes-index`。
如果你 fork 到别的账号下，记得全局替换回来：

```bash
grep -rn "derecat/codes-index" site/ .github/ README.md
```

站点地址：**https://derecat.github.io/codes-index/**

想让仓库根本搜不到、只给熟人用？去 `Settings → General → Danger Zone → Change visibility`
切 Private。**注意**：私有仓库的 Actions 会消耗额度，Pages 也不再免费（需要 GitHub Pro / Team）。
稳妥做法是保持 Public，但把内容严格限制在「元数据 + 主观评价」范围内。

---

## 怎么投稿

打开 `Issues → New issue → 投稿一个车牌号`，填完提交。

- 机器人几秒内校验、入库、回帖并关闭 Issue。
- 失败了它会在 Issue 下面留言说明原因，**直接编辑 Issue 内容就会自动重试**（不用重开一个）。
- 想改口？重新提一个 Issue 或在原 Issue 上编辑，同账号算改票。

维护者想人工干预时，直接编辑 `data/entries/xxx.json` 提 PR 即可，CI 会自动跑校验。

---

## 评论区

推荐理由解决的是「值不值得看」，评论区解决的是「看完了想聊两句」。

用的是 **giscus** —— 把 GitHub Discussions 直接当评论后端。它的妙处在于：

| 你担心的 | giscus 的答案 |
| --- | --- |
| 要租服务器吗 | 不要，整个评论系统就是一个 iframe |
| 要数据库吗 | 不要，评论存在 Discussions 里 |
| 会被刷广告吗 | 要 GitHub 账号才能发言，机器人账号成本极高 |
| 有人发违法内容怎么办 | GitHub 社区规范替你兜着，一键删除即消失 |
| 免费吗 | 完全免费，公开仓库不消耗任何额度 |

**每个番号 = 一个 Discussion**，标题就是番号本身（`data-term` 传的是 code，
配 `data-strict="1"` 保证 `ABC-1` 不会误撞 `ABC-10`）。
第一次有人评论时 giscus 自动创建对应讨论串，你什么都不用管。

发帖权限靠 **Announcements 类型** 的分类来控制：这类分类只有维护者能开新帖，
但 **任何人可以回复** —— 正好是我们要的效果：话题由数据决定，讨论由大家进行。

> 站点是纯静态页面，用 `file://` 直接打开时评论不会显示（跨域限制）。
> 本地想看评论，用 `python3 -m http.server` 起个服务器。

---

## 本地开发

```bash
python3 scripts/seed_demo.py      # 生成示例数据（不想要就 rm data/entries/*.json）
python3 scripts/validate.py       # 全库校验
python3 scripts/build_index.py    # 生成 data/index.json + site/data/index.js
python3 scripts/check_frontend.py # 前端自检：DOM 引用 / 脚本顺序 / 主题残留

# 起个静态服务器看效果（评论功能必须有 http 才能加载）
cd site && python3 -m http.server 8080
```

---

## 运维与风险

**必读，这个项目最大的敌人不是技术。**

1. **只收元数据。** 不收录任何下载链接、截图、封面、视频。一旦涉及盗版资源分发，
   不只是仓库被 DMCA 掉的问题，是法律问题。
2. **`sourceUrl` 白名单思维**：只允许指向官方发行页、正规数据库条目页。
   校验脚本里那份黑名单（磁力/网盘/文件后缀）就是第一道闸门。
3. **防刷**：同账号一票制已经挡住了大部分。真被盯上可以再加
   `账号注册时间 > 30 天`（用 `gh api users/{login}` 查），或在 Action 里加人工审核标签。
4. **内容争议**：加 `CONTRIBUTING.md` 里的删除条款 —— 权利人提出异议，
   维护者 24 小时内删除对应条目，无需理由。这条能救你一命。
5. **不要用 GitHub Pages 直接放置可检索的敏感词标题**，标题字段留空是合法选择，
   站点照样能用番号搜索。

---

## 进阶玩法

- **Discussions 做投票**：`tag: 提名` 的帖子用 👍 reaction 决定要不要收录。
- **标签收敛**：`build_index.py` 已经在统计标签频次，可以加一个「同义词映射表」
  把「巨乳」和「欧派」合并，否则标签会碎成几百个。
- **Telegram / 微信机器人**：同样调 GitHub API 建 Issue，社群投稿零门槛。
- **每周精选**：一个 cron Action，按 `recommendations.length` 和平均分生成周报 Issue。
- **直接复用数据**：`data/index.json` 是干净 JSON，别人可以拿去自己搭站，
  这才是「大家都能推荐」的最终形态 —— 数据比站点活得久。

## License

MIT（代码）+ CC0（数据）。投稿即视为同意以上条款。
