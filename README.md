# 英语口语跟读素材（Instagram Reels → 照片 → iPhone 快捷指令）

198 条 Instagram 口语短视频，按「话题」和「人物」两套分类整理好，导入 Mac 的「照片」，
iCloud 同步到 iPhone，用一个快捷指令每次随机抽 10 条，左右滑着跟读。

素材是别人说的话：演讲、播客片段、访谈、电影台词。有原文转写，标注了难度（L1 句子 → L5 长难段）和时长。

## 做完之后长这样

```
照片
├── 英语素材｜由浅入深｜001–198           ← 198 条，相簿里按 001→198 排
├── 英语素材｜按话题
│   ├── 1 与自己相处
│   │   ├── 1.1 内在系统
│   │   │   ├── 1.1.1 面对恐惧（9）
│   │   │   ├── 1.1.2 自信（13）
│   │   │   ├── 1.1.3 情绪与压力（5）
│   │   │   └── 1.1.4 身体（12）
│   │   ├── 1.2 行动系统
│   │   │   ├── 1.2.1 启动与执行（14）
│   │   │   ├── 1.2.2 坚持与韧性（7）
│   │   │   └── 1.2.3 习惯与自律（10）
│   │   └── 1.3 认知系统
│   │       ├── 1.3.1 目标与方向（6）
│   │       ├── 1.3.2 思维与心态（36）
│   │       ├── 1.3.3 学习方法（16）
│   │       └── 1.3.4 失败与复盘（3）
│   ├── 2 与他人相处
│   │   ├── 2.1 人际关系
│   │   │   ├── 2.1.1 沟通与连接（6）
│   │   │   └── 2.1.2 边界与选择（8）
│   │   └── 2.2 爱情
│   │       ├── 2.2.1 恋爱与吸引（17）
│   │       └── 2.2.2 伴侣与婚姻（4）
│   ├── 3 与世界交手（21）
│   └── 4 附属（11）
└── 英语素材｜按人物
    ├── Chris Williamson（7）
    ├── Brandon Clark（6）
    ├── Alex Hormozi（5）
    ├── ...
    └── 其他人物·各1条（125）            ← 26 个相簿，合计 198
```

相簿里的顺序就是难度顺序：每条视频的拍摄时间被写成 `2026-01-01 08:00:00 + 序号秒`，
照片按日期排，所以「1.1.1 面对恐惧」里第一条就是全库最容易的一条。这是整套排序的关键，
脚本会核对每条的日期，不对就重设。

## 开始（交给 agent）

把 [`PROMPT.md`](PROMPT.md) 里的那段话粘进 Codex / Claude Code / Hermes 之类的 agent，它会读仓库里的
[`AGENTS.md`](AGENTS.md) 自己跑完。跑之前它会问你磁盘和时长，下载中途断了重跑同一条命令就行。

## 手动安装

需要：macOS、iPhone、Chrome 里登录过 Instagram、`brew install yt-dlp ffmpeg`。

```bash
git clone https://github.com/Snoop2023/english-speaking-shadowing.git
cd english-speaking-shadowing
bash scripts/install.sh
```

中间会有一次系统弹窗「终端想控制照片」，点允许。

只下前 3 条试试：

```bash
python3 scripts/download.py --limit 3
```

已经有本地视频（比如自己以前下过），跳过下载只转码：

```bash
python3 scripts/download.py --from-local /path/to/01_videos_compatible
```

## 快捷指令

`shortcut/英语随机刷.shortcut`：从「英语素材｜由浅入深｜001–198」里随机抽 10 条视频，快速查看，左右滑。

- iCloud 链接：https://www.icloud.com/shortcuts/02186a00c50946179e40b7def847a2ff
- 链接失效时，自己在 Mac 上生成、签名、导入：

  ```bash
  python3 shortcut/build_shortcut.py
  shortcuts sign --mode people-who-know-me --input shortcut/英语随机刷.shortcut --output shortcut/英语随机刷.signed.shortcut
  open shortcut/英语随机刷.signed.shortcut
  ```

  未签名的 `.shortcut` 新版 macOS 直接拒绝导入，必须先签名。签名要连 Apple 的服务器，
  经常 5xx；重试几次，或者过一会儿再跑。
- 想重新签名分享给别人：`shortcuts sign --mode anyone --input shortcut/英语随机刷.shortcut --output out.shortcut`。
  Apple 的签名服务器经常 5xx，重试几次；一直不行就退回 `--mode people-who-know-me`。

## 仓库里有什么

| 路径 | 内容 |
|---|---|
| `data/index.json` | 198 条的主索引：序号、IG 链接、标题、人物、话题路径、难度、时长、原文 |
| `data/albums.json` | 相簿结构（文件夹 / 相簿 / 每条属于哪个），`photos.py` 按它建 |
| `notes/` | 四份 Markdown 笔记：按话题、按人物、高档（L3–L5）、低档（L1–L2） |
| `scripts/download.py` | 从 Instagram 下载 + 转码 + 写日期 |
| `scripts/photos.py` | 导入照片 + 建两套相簿 + 核对日期和数量 |
| `scripts/install.sh` | 上面两步串起来 |
| `shortcut/` | 快捷指令生成脚本和 `.shortcut` 文件 |
| `AGENTS.md` / `PROMPT.md` / `CLAUDE.md` / `skill/SKILL.md` | 给 agent 的入口 |

笔记里每条长这样，点 IG 链接能回到原视频：

```
- [ ] 1. **Stoicism | Philosophy | Mindset**
   原文：You know, sometimes all you need is 20 seconds of insane courage...
   标题：20 seconds of insane courage
   [IG链接](https://www.instagram.com/reel/DVW52YfDD0-/) | 难度：L1 sentence | 时长：26.3s
```

（笔记里的勾选框是练习进度，仓库版本全部留空。）

## 限制

- 只有 macOS + iPhone。导入「照片」用的是 AppleScript，别的系统没有这套东西。
- 需要 Chrome 登录 Instagram：脚本靠 Chrome 的 cookie 下载。
- 原视频被 Instagram 删了或设成私密的，下不到。`failed.csv` 里会写是哪几条。
- Instagram 会限流，所以串行下载、每条停 3–5 秒，198 条要跑 30–60 分钟。
- 媒体类型是视频，占空间不小；脚本只下转码后的版本，`raw/` 用完就删。

## 版权

视频版权全部属于原作者和 Instagram 上的发布者。这个仓库不含任何视频文件，只有：

- 指向原帖的 IG 链接（公开信息）
- 每条的原文转写（用于语言学习，属于合理使用的范围，但如果你要商用请自行取得授权）

脚本只是把公开视频下到你自己的电脑上供个人学习。请勿二次分发视频、勿用于商业用途。
如果原作者要求下架某条，删掉对应的 IG 链接和索引条目即可。
