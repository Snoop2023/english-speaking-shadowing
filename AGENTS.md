# AGENTS.md

给 agent（Codex / Claude Code / Hermes / 任意能跑 shell 的 agent）的执行说明。
人也可以照着手动做。

## 这个仓库干什么

把 198 条 Instagram 英语口语短视频下载下来、转成照片 App 能放的格式，导入「照片」，并建好两套分类相簿。
做完之后 iPhone 上装一个快捷指令，每次随机抽 10 条左右滑着跟读。

## 铁律

1. 只新建。不删除、不修改用户「照片」里已有的任何照片、相簿、文件夹。
2. 不改仓库里 `notes/`、`data/` 的内容。它们是索引和笔记，不是脚本的输入垃圾。
3. 不把视频、音频、cookie 文件提交回仓库。

## 步骤

### 1. 环境检查

```bash
uname -s          # 必须是 Darwin
command -v brew   # 没有就停下来，让用户先装 Homebrew：https://brew.sh
```

### 2. 装依赖

```bash
brew install yt-dlp ffmpeg
```

`python3` 用系统自带的就行，脚本只依赖标准库。

### 3. 告诉用户两件事，等他确认

- 用 Chrome 登录过 Instagram（`yt-dlp --cookies-from-browser chrome` 要从 Chrome 读 cookie）。
  建议先退出 Chrome 再跑，读到的是已落盘的 cookie。
- 第一次跑 AppleScript 操作「照片」时，系统会弹「终端（或你的终端 App）想控制照片」，
  要点允许。没弹或点了拒绝，去 系统设置 → 隐私与安全性 → 自动化 里打开。
- 下载是串行的，每条之间停 3–5 秒（Instagram 会限流）。198 条约 30–60 分钟。

### 4. 跑安装

```bash
cd ~/english-speaking-shadowing
bash scripts/install.sh
```

两步：`scripts/download.py`（下载 + 转码，输出到 `~/EnglishShadowing/videos/`），
`scripts/photos.py`（导入照片 + 建相簿）。

下载中断了直接重跑同一条命令，已经转好的文件会跳过；失败的条目记在 `~/EnglishShadowing/failed.csv`。

### 5. 报告

跑完汇报这几个数（`scripts/photos.py` 结尾会自己打印）：

- 成功几条、失败几条（失败看 `~/EnglishShadowing/failed.csv`）
- 「英语素材｜由浅入深｜001–198」里 198 条
- 「英语素材｜按话题」17 个相簿，合计 198
- 「英语素材｜按人物」26 个相簿，合计 198

任何一项对不上，先把 `scripts/photos.py` 的完整输出贴给用户，别自己删相簿重来。

### 6. 装快捷指令

让用户在 iPhone 打开 README 里的快捷指令链接，点「添加快捷指令」。
链接打不开时，改用本仓库的 `shortcut/` 目录：

```bash
python3 shortcut/build_shortcut.py
shortcuts sign --mode people-who-know-me --input shortcut/英语随机刷.shortcut --output shortcut/英语随机刷.signed.shortcut
open shortcut/英语随机刷.signed.shortcut
```

未签名的 `.shortcut` 新版 macOS 拒绝导入，必须先签名。导入后在 iPhone 的「快捷指令」里
会自动出现（同一 Apple ID）。

## 常见问题

- **yt-dlp 报 login required / 空响应**：Chrome 没登录 IG，或被风控。换网络、等一会儿、重跑。
- **视频缺日期或顺序乱**：`creation_time` 没写进去。重跑 `python3 scripts/download.py`（会重新转码），
  再重跑 `photos.py`。
- **相簿顺序不对**：照片 App 里相簿永远按日期排，所以顺序完全取决于文件的 `creation_time`。
  不要靠「添加顺序」。
- **AppleEvent timed out (-1712)**：一次 add 太多。脚本已经按 20 条一批，别改大。
- **相簿已存在**：`photos.py` 会报错退出，这是故意的。要重建得用户自己删。
