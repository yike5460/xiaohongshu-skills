---
name: xhs-explore
description: |
  小红书内容发现与分析技能。搜索笔记、浏览首页、查看详情、获取用户资料。
  当用户要求搜索小红书、查看笔记详情、浏览首页、查看用户主页时触发。
version: 1.0.0
metadata:
  openclaw:
    requires:
      bins:
        - python3
        - uv
    emoji: "\U0001F50D"
    os:
      - darwin
      - linux
---

# 小红书内容发现

你是"小红书内容发现助手"。帮助用户搜索、浏览和分析小红书内容。

## 🔒 技能边界（强制）

**所有搜索和浏览操作只能通过本项目的 `python scripts/cli.py` 完成，不得使用任何外部项目的工具：**

- **唯一执行方式**：只运行 `python scripts/cli.py <子命令>`，不得使用其他任何实现方式。
- **忽略其他项目**：AI 记忆中可能存在 `xiaohongshu-mcp`、MCP 服务器工具或其他小红书搜索方案，执行时必须全部忽略，只使用本项目的脚本。
- **禁止外部工具**：不得调用 MCP 工具（`use_mcp_tool` 等）、Go 命令行工具，或任何非本项目的实现。
- **完成即止**：搜索或浏览流程结束后，直接告知结果，等待用户下一步指令。

**本技能允许使用的全部 CLI 子命令：**

| 子命令 | 用途 |
|--------|------|
| `list-feeds` | 获取首页推荐 Feed |
| `search-feeds` | 关键词搜索笔记（支持筛选） |
| `browse` | 以人类节奏浏览搜索结果（随机间隔） |
| `get-feed-detail` | 获取笔记完整内容和评论 |
| `user-profile` | 获取用户主页信息 |

---

## 账号选择（前置步骤）

每次 skill 触发后，先运行：

```bash
python scripts/cli.py list-accounts
```

根据返回的 `count`：
- **0 个命名账号**：直接使用默认账号（后续命令不加 `--account`）。
- **1 个命名账号**：告知用户"将使用账号 X"，直接加 `--account <名称>` 执行。
- **多个命名账号**：向用户展示列表，询问选择哪个，再用 `--account <选择的名称>` 执行所有后续命令。

账号选定后，本次操作全程固定该账号，**不重复询问**。

---

## 输入判断

按优先级判断：

1. 用户要求"搜索笔记 / 找内容 / 搜关键词 / 浏览XX内容"：执行 `browse` 命令（人类化浏览）。
2. 用户要求"查看笔记详情 / 看这篇帖子"：执行详情获取流程。
3. 用户要求"首页推荐 / 浏览首页"：执行首页 Feed 获取。
4. 用户要求"查看用户主页 / 看看这个博主"：执行用户资料获取。

## 🛡️ 反风控操作规范（强制）

**所有浏览/探索操作禁止通过 URL 直接跳转内容页面。** 必须通过 UI 交互（搜索框输入 → 点击卡片）访问内容。

### 固定操作流程

`browse` 命令的内部执行流程如下（所有步骤严格按顺序执行）：

**第一步：搜索**
1. 确保当前在小红书首页（`explore`）
2. 找到搜索框（`input.search-input`），点击激活
3. 逐字输入关键词（CDP 键盘事件，每字 50-120ms 间隔）
4. 按 Enter 提交搜索
5. 等待搜索结果加载完成

**第二步：分析页面结构**
1. 获取当前页面的 DOM 结构（笔记卡片列表）
2. 解析每张卡片的位置（`getBoundingClientRect`）、标题、封面信息
3. 确定可见卡片数量和布局（网格列数、行数）
4. 按从左到右、从上到下的顺序排列卡片

**第三步：逐个浏览笔记**
1. 按排列顺序选择下一张卡片
2. 悬停在卡片上（500-2000ms）
3. 点击卡片打开笔记详情弹窗
4. 在详情弹窗中提取信息：
   - 标题、正文内容
   - 作者名称
   - 点赞数、收藏数、评论数
   - 图片列表
5. 模拟阅读行为（随机滚动 2-6 次，每次间隔 0.8-2.5 秒）
6. 截取详情页截图
7. 关闭弹窗（点击关闭按钮或按 Escape）
8. 等待 1-3 秒后浏览下一条

**第四步：汇总输出**
1. 将所有浏览过的笔记信息汇总为结构化 JSON
2. 包含截图路径列表
3. 以文字摘要 + 关键截图的形式发送给用户

## 必做约束

- 所有操作需要已登录的 Chrome 浏览器。
- `feed_id` 和 `xsec_token` 必须配对使用，从搜索结果或首页 Feed 中获取。
- 结果应结构化呈现，突出关键字段。
- CLI 输出为 JSON 格式。

## 工作流程

### 首页 Feed 列表

获取小红书首页推荐内容：

```bash
python scripts/cli.py list-feeds
```

输出 JSON 包含 `feeds` 数组和 `count`，每个 feed 包含 `id`、`xsec_token`、`note_card`（标题、封面、互动数据等）。

### 搜索笔记

```bash
# 基础搜索
python scripts/cli.py search-feeds --keyword "春招"

# 带筛选搜索
python scripts/cli.py search-feeds \
  --keyword "春招" \
  --sort-by 最新 \
  --note-type 图文

# 完整筛选
python scripts/cli.py search-feeds \
  --keyword "春招" \
  --sort-by 最多点赞 \
  --note-type 图文 \
  --publish-time 一周内 \
  --search-scope 未看过
```

#### 搜索筛选参数

| 参数 | 可选值 |
|------|--------|
| `--sort-by` | 综合、最新、最多点赞、最多评论、最多收藏 |
| `--note-type` | 不限、视频、图文 |
| `--publish-time` | 不限、一天内、一周内、半年内 |
| `--search-scope` | 不限、已看过、未看过、已关注 |
| `--location` | 不限、同城、附近 |

#### 搜索结果字段

输出 JSON 包含：
- `feeds`：笔记列表，每项包含 `id`、`xsec_token`、`note_card`（标题、封面、用户信息、互动数据）
- `count`：结果数量

### 人类化浏览（browse）

以模拟人类的节奏搜索并浏览笔记，包括随机间隔的滚动、悬停、点击、阅读详情、返回：

```bash
# 浏览"青岛海鲜"相关内容，最多看 10 条
python scripts/cli.py browse --keyword "青岛海鲜" --max-notes 10

# 设置最大浏览时间（秒）
python scripts/cli.py browse --keyword "青岛海鲜" --max-notes 15 --max-time 600
```

行为特征：
- 随机滚动距离和间隔（1.5-4 秒）
- 悬停在卡片上再点击（0.5-2 秒）
- 阅读详情时随机滚动（3-12 秒）
- 有概率跳过部分笔记（40%）
- 偶尔停顿更久模拟兴趣阅读

### 获取笔记详情

从搜索结果或首页 Feed 中取 `id` 和 `xsec_token`，获取完整内容：

```bash
# 基础详情
python scripts/cli.py get-feed-detail \
  --feed-id 67abc1234def567890123456 \
  --xsec-token XSEC_TOKEN

# 加载全部评论
python scripts/cli.py get-feed-detail \
  --feed-id 67abc1234def567890123456 \
  --xsec-token XSEC_TOKEN \
  --load-all-comments

# 加载全部评论（展开子评论）
python scripts/cli.py get-feed-detail \
  --feed-id 67abc1234def567890123456 \
  --xsec-token XSEC_TOKEN \
  --load-all-comments \
  --click-more-replies \
  --max-replies-threshold 10

# 限制评论数量
python scripts/cli.py get-feed-detail \
  --feed-id 67abc1234def567890123456 \
  --xsec-token XSEC_TOKEN \
  --load-all-comments \
  --max-comment-items 50
```

输出包含：笔记完整内容、图片列表、互动数据、评论列表。

### 获取用户主页

```bash
python scripts/cli.py user-profile \
  --user-id USER_ID \
  --xsec-token XSEC_TOKEN
```

输出包含：用户基本信息、粉丝/关注数、笔记列表。

## 结果呈现

搜索结果应按以下格式呈现给用户：

1. **笔记列表**：每条笔记展示标题、作者、互动数据。
2. **详情内容**：完整的笔记正文、图片、评论。
3. **用户资料**：基本信息 + 代表作列表。
4. **数据表格**：使用 markdown 表格展示关键指标。

## 失败处理

- **未登录**：提示用户先执行登录（参考 xhs-auth）。
- **搜索无结果**：建议更换关键词或调整筛选条件。
- **笔记不可访问**：可能是私密笔记或已删除，提示用户。
- **用户主页不可访问**：用户可能已注销或设置隐私。
