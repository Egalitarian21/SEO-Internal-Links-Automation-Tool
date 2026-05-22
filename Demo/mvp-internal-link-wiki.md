# Internal-Link-Wiki-MVP 实施方案

> 版本：v1.1（新增 Step 4 Excel 输出）  
> 日期：2026-05-22  
> 目标读者：软件开发工程师  
> MVP 上线目标：跑通「URL 入库 → 生成 Wiki 卡片 → 博客匹配推荐 → Excel 报告」四步链路

\---

## 1\. 项目目标与范围

### 1.1 一句话定位

接收客户的博客 URL 列表和单篇博客 Markdown 正文，由 LLM 生成结构化 Wiki 卡片库，再由 LLM 基于 Wiki 卡片库为博客推荐内链锚文本和目标 URL，最终汇总成 Excel 报告交付给 SEO 团队执行。

### 1.2 MVP 范围

|能力|MVP 内|MVP 外|
|-|-|-|
|客户隔离的文件夹存储|✅||
|URL 列表追加去重|✅||
|网页爬取（Title / Description / H 层级）|✅||
|LLM 生成 Wiki 卡片|✅||
|批量分批处理（带阈值）|✅||
|博客 Markdown 输入 → 推荐输出|✅||
|两段式匹配（先文件名筛选，再内容评分）|✅||
|**推荐结果汇总 Excel**|✅||

### 1.3 设计原则

1. **文件系统就是数据库**：不引入 SQLite / PostgreSQL，所有状态落到 `.md / .json / .xlsx` 文件
2. **客户级隔离**：所有数据按客户名分文件夹（Raw / Wiki card / Reference 三处同步）
3. **LLM 只在三个明确节点调用**：Wiki 卡片生成、卡片名筛选、博客内容匹配
4. **可重入**：同一 URL 重复输入不重复创建卡片，重复匹配可幂等
5. **可观测**：每次 LLM 调用记录 prompt + response 到日志文件
6. **可交付**：最终输出标准 Excel，SEO 团队可直接用来执行内链插入

\---

## 2\. 项目文件夹结构

### 2.1 顶层结构

```
Internal-Link-Wiki-MVP/
├── Code/                              # 所有源代码
│   ├── app/
│   │   ├── \_\_init\_\_.py
│   │   ├── main.py                    # FastAPI / CLI 入口
│   │   ├── config.py
│   │   ├── services/
│   │   │   ├── url\_intake.py          # Step 1
│   │   │   ├── wiki\_generator.py      # Step 2
│   │   │   ├── recommender.py         # Step 3
│   │   │   ├── excel\_reporter.py      # Step 4
│   │   │   ├── crawler.py
│   │   │   └── storage.py
│   │   ├── llm/
│   │   │   ├── client.py
│   │   │   └── prompts/
│   │   │       ├── wiki\_generation.md
│   │   │       ├── card\_filter.md
│   │   │       └── content\_match.md
│   │   ├── routers/
│   │   │   ├── intake.py
│   │   │   ├── generate.py
│   │   │   ├── recommend.py
│   │   │   └── report.py
│   │   ├── cli.py
│   │   └── utils/
│   │       ├── slug.py
│   │       └── url\_utils.py
│   ├── tests/
│   ├── logs/
│   │   └── llm\_calls/{yyyy-mm-dd}.jsonl
│   ├── .env.example
│   ├── pyproject.toml
│   └── README.md
└── Data/
    ├── Raw/
    │   └── {Customer-Name}/
    │       └── Internal-URL.md
    ├── Wiki card/
    │   └── {Customer-Name}/
    │       ├── Wiki-{Title-Slug}.json
    │       └── ...
    └── Reference/
        └── {Customer-Name}/
            ├── Recommendations-{blog-slug}-{yyyymmdd-HHMMSS}.xlsx
            └── ...
```

### 2.2 文件命名约定

|实体|命名规则|示例|
|-|-|-|
|客户文件夹|客户名替换路径非法字符（`/ \\ : \* ? " < > \|`）为 `-`|`BrandX-Inc`|
|URL 列表|固定 `Internal-URL.md`|`Data/Raw/BrandX-Inc/Internal-URL.md`|
|Wiki 卡片|`Wiki-{Title-Slug}.json`，Title-Slug = lowercase + 替换特殊字符为 `-` + 截断 80 字符|`Wiki-how-to-optimize-shopify-product-pages.json`|
|Excel 报告|`Recommendations-{blog-slug}-{yyyymmdd-HHMMSS}.xlsx`|`Recommendations-how-to-find-suppliers-20260522-113045.xlsx`|

### 2.3 路径解析模块

`app/services/storage.py` 提供以下方法（所有路径基于 `DATA\_ROOT` 配置）：

```python
def get\_customer\_raw\_dir(customer: str) -> Path
def get\_customer\_wiki\_dir(customer: str) -> Path
def get\_customer\_reference\_dir(customer: str) -> Path
def get\_internal\_url\_md\_path(customer: str) -> Path
def get\_wiki\_card\_path(customer: str, title: str) -> Path
def get\_excel\_report\_path(customer: str, blog\_slug: str) -> Path
def ensure\_customer\_dirs(customer: str) -> None        # 同时确保三个文件夹存在
def list\_wiki\_cards(customer: str) -> list\[Path]
def list\_wiki\_card\_titles(customer: str) -> list\[str]
```

\---

## 3\. 数据格式规范

### 3.1 Internal-URL.md 格式

纯 Markdown 列表，**追加写入**，不删除历史，幂等去重。

```markdown
# {Customer-Name} — Internal URLs

> Last updated: 2026-05-22T11:30:00+08:00

- https://brandx.com/blogs/seo/optimize-product-pages
- https://brandx.com/blogs/dropshipping/find-suppliers
- https://brandx.com/blogs/marketing/email-campaigns
```

**写入逻辑**：

* 文件不存在 → 创建并写入 header
* 文件存在 → 读取已有 URL 集合，仅追加新 URL
* 每次写入更新 `Last updated` 时间戳

### 3.2 Wiki 卡片 JSON Schema

```json
{
  "customer": "BrandX-Inc",
  "url": "https://brandx.com/blogs/seo/optimize-product-pages",
  "Title": "How to Optimize Shopify Product Pages for SEO",
  "Description": "A comprehensive guide covering title tags, meta descriptions, image alt text...",
  "H\_Hierarchy": \[
    { "level": 1, "text": "How to Optimize Shopify Product Pages for SEO" },
    { "level": 2, "text": "Why Product Page SEO Matters" },
    { "level": 2, "text": "Title Tag Best Practices" },
    { "level": 3, "text": "Keyword Placement" },
    { "level": 3, "text": "Length Limits" },
    { "level": 2, "text": "Meta Description Optimization" }
  ],
  "Web\_Abstract\_AI\_Generated": "This article guides Shopify merchants through optimizing product pages for organic search. It covers four core areas: writing keyword-rich title tags, crafting compelling meta descriptions, structuring H tags for content hierarchy, and adding descriptive image alt text. The guide is targeted at small-to-mid sized Shopify stores looking to improve product visibility in Google."
}
```

**字段约束：**

|字段|来源|长度限制|必需|
|-|-|-|-|
|`Title`|网页 `<title>` 或 `<h1>`|≤ 200 字符|✅|
|`Description`|`<meta name="description">`|≤ 500 字符|⚠️ 缺失时为空字符串|
|`H\_Hierarchy`|解析 H1-H6|数组保留出现顺序|✅|
|`Web\_Abstract\_AI\_Generated`|LLM 生成|200-500 字符|✅|

### 3.3 Excel 报告 Schema（Step 4 输出）

文件类型：`.xlsx`，由 `openpyxl` 生成。

**Sheet 1：Recommendations**（主表，SEO 团队执行用）

|列名|类型|说明|
|-|-|-|
|#|int|序号（从 1 开始）|
|Source Blog URL|str|当前博客 URL|
|Source Blog Title|str|当前博客标题（若提供）|
|Anchor Text|str|推荐锚文本（博客原文中的连续片段）|
|Target URL|str|推荐内链目标 URL（来自 Wiki Card）|
|Target Title|str|目标页面标题（来自 Wiki Card）|
|Insert Paragraph|str|锚文本所在段落原文（用于精确定位）|

**Sheet 2：Metadata**（元信息）

|Key|Value|
|-|-|
|Customer|BrandX-Inc|
|Source Blog URL|https://...|
|Total Recommendations|6|
|Score Threshold|0.6|
|Wiki Cards Library Size|142|
|Cards Filtered (Stage 1)|18|

**格式约定**：

* Sheet 1 首行加粗 + 灰色底色
* 列宽自适应（关键列：Anchor Text / Insert Paragraph 宽度上限 60）
* Anchor Text 列字体加粗（便于 SEO 团队识别）
* Relevance Score 列条件格式：≥ 0.8 绿色、0.6-0.8 黄色、< 0.6 不显示（已过滤）

\---

## 4\. 工作流详细设计

### 4.1 Step 1：URL 入库（url\_intake）

**输入**：

```python
class IntakeRequest(BaseModel):
    customer: str
    urls: list\[str] | None = None
    blog\_url: str | None = None
    blog\_markdown: str | None = None
```

**处理逻辑**：

```
1. customer 名称合法性校验 + slug 化
2. ensure\_customer\_dirs(customer)
   - 确保 Data/Raw/{customer}/ 存在
   - 确保 Data/Wiki card/{customer}/ 存在
   - 确保 Data/Reference/{customer}/ 存在
3. 收集 URL 候选集合：urls + blog\_url（去重，去空）
4. 读取已有 Internal-URL.md（若存在），解析出已有 URL 集合
5. 计算 new\_urls = candidates - existing
6. 追加 new\_urls 到 Internal-URL.md，更新 Last updated 时间戳
7. 若提供 blog\_url + blog\_markdown：
   - 暂存到 Data/Raw/{customer}/blogs/{blog-slug}.md
8. 返回入库统计
```

**输出**：

```python
class IntakeResult(BaseModel):
    customer: str
    new\_urls\_added: int
    duplicate\_urls\_skipped: int
    total\_urls\_in\_db: int
    blog\_md\_saved: bool
    dirs\_ready: list\[str]   # 三个文件夹路径
```

\---

### 4.2 Step 2：Wiki 卡片生成（wiki\_generator）

**输入**：

```python
class GenerateRequest(BaseModel):
    customer: str
    batch\_size: int = 10
    only\_missing: bool = True
```

**处理逻辑**：

```
1. 读取 Data/Raw/{customer}/Internal-URL.md → all\_urls
2. 列出 Data/Wiki card/{customer}/\*.json，
   反向解析每个卡片 JSON 的 url 字段 → existing\_urls
3. todo\_urls = all\_urls - existing\_urls（如果 only\_missing=True）
4. 按 batch\_size 分批：
   for batch in chunked(todo\_urls, batch\_size):
     for url in batch (并发 ≤ 3):
       a) Crawler.crawl(url)
          → 获取 HTML
          → 解析 Title / Description / H1-H6 层级
          → 提取正文文本（用于 LLM 输入）
       b) LLM.generate\_abstract(title, description, h\_hierarchy, body)
          → 返回 Web\_Abstract\_AI\_Generated
       c) 组装 Wiki Card JSON
       d) storage.save\_wiki\_card(customer, title, card)
       e) 写入 LLM 调用日志
5. 返回处理统计
```

**输出**：

```python
class GenerateResult(BaseModel):
    customer: str
    total\_todo: int
    success: int
    failed: list\[FailedItem]
    cards\_generated: list\[str]
    elapsed\_seconds: float
```

**关键约束**：

* 并发上限 3（避免 LLM 限流）
* 单 URL 全流程超时 30s
* 失败重试 2 次（间隔 2s）
* 单个失败不影响其他 URL
* 同名 Title 处理：`Wiki-{slug}-2.json`、`-3.json`...

\---

### 4.3 Step 3：博客匹配推荐（recommender）

**输入**：

```python
class RecommendRequest(BaseModel):
    customer: str
    blog\_url: str
    blog\_markdown: str
    blog\_title: str | None = None
    score\_threshold: float = 0.6
    max\_recommendations: int = 8
```

**处理逻辑（两段式匹配）**：

```
═══ 第一段：文件名筛选 ═══

1. 列出 Data/Wiki card/{customer}/\*.json 文件名 → all\_card\_names
2. 排除 blog\_url 对应的卡片（避免自我推荐）
3. 调用 LLM（card\_filter.md prompt）：
   输入：
     - blog\_title + blog\_markdown 摘要（前 1500 字符）
     - all\_card\_names 列表
   输出：matched\_card\_names（list，至多 30 个）

═══ 第二段：内容精排 ═══

4. 加载 matched\_card\_names 对应的 JSON 文件
5. 调用 LLM（content\_match.md prompt）：
   输入：
     - blog\_markdown 全文
     - matched\_cards 的结构化信息
   要求：
     - 对每张卡片评估语义匹配度（0-1）
     - 对匹配度 ≥ score\_threshold 的卡片：
       a) 找出博客中能自然嵌入锚文本的段落
       b) 返回 anchor\_text（必须是博客原文连续文本）
       c) 返回 insert\_paragraph（命中段落原文）
       d) 返回 reason
   输出：JSON 数组 \[Recommendation]
6. 硬校验：
   - anchor\_text 必须出现在 blog\_markdown 中（精确匹配）
   - 不能位于第一段
   - 同一 target\_url 只保留 1 条
   - 截断到 max\_recommendations
7. 返回推荐列表
```

**输出**：

```python
class Recommendation(BaseModel):
    target\_url: str
    target\_title: str
    anchor\_text: str
    insert\_paragraph: str
    relevance\_score: float
    reason: str

class RecommendResult(BaseModel):
    customer: str
    blog\_url: str
    blog\_title: str | None
    candidates\_filtered: int            # 第一段筛后数量
    recommendations: list\[Recommendation]
    discarded: list\[DiscardedItem]
    library\_size: int                   # 卡片库总量
    elapsed\_seconds: float
```

**关键约束**：

* 第一段 prompt 限制：返回卡片 ≤ 30
* 第二段 LLM 调用：max\_tokens 4096，超时 90s
* LLM `temperature=0.2`（提升结果稳定性）

\---

### 4.4 Step 4：Excel 报告生成（excel\_reporter）

**输入**：

```python
class ReportRequest(BaseModel):
    customer: str
    blog\_url: str
    recommend\_result: RecommendResult   # 来自 Step 3 的输出
```

**处理逻辑**：

```
1. 校验 customer + blog\_url + recommend\_result
2. blog\_slug = slugify(blog\_url 或 blog\_title)
3. timestamp = current\_time().strftime("%Y%m%d-%H%M%S")
4. 输出路径 = Data/Reference/{customer}/Recommendations-{blog\_slug}-{timestamp}.xlsx
5. 用 openpyxl 创建 Workbook：
   a) Sheet "Recommendations"：
      - 写表头（10 列，加粗 + 灰底）
      - 遍历 recommendations，按 relevance\_score 降序写入数据行
      - 应用条件格式（Score ≥ 0.8 绿色、0.6-0.8 黄色）
      - 设置列宽
      - Anchor Text 列加粗
   b) Sheet "Metadata"：
      - Key-Value 形式写元信息
6. 保存 .xlsx 文件
7. 返回路径 + 文件大小
```

**输出**：

```python
class ReportResult(BaseModel):
    customer: str
    blog\_url: str
    excel\_path: str                     # 绝对路径
    file\_name: str                      # 仅文件名
    rows\_written: int
    file\_size\_bytes: int
    generated\_at: datetime
```

**自动整合模式**：

* API `/api/recommend-and-report`：合并 Step 3 + Step 4，一步出 Excel
* CLI `recommend --output excel`：自动生成 Excel 而非 JSON

**重复文件处理**：

* 同博客多次推荐 → 时间戳后缀确保不覆盖
* 文件夹下同名文件不删除（保留历史版本）

\---

## 5\. LLM Prompt 模板规范

### 5.1 wiki\_generation.md（Step 2）

```
You are an SEO content analyst. Read the following webpage information and write a 200–500 character abstract describing what this page is about, who it targets, and its key content sections.

Title: {title}
Description: {description}
H Hierarchy:
{h\_hierarchy\_formatted}
Body Text (first 4000 chars): {body\_text\_excerpt}

Output JSON only:
{{"Web\_Abstract\_AI\_Generated": "..."}}
```

### 5.2 card\_filter.md（Step 3 第一段）

```
You are an SEO internal-linking expert. Below is a blog article and a list of Wiki card titles from the same customer. Identify which Wiki cards are topically relevant to this blog and could be candidates for internal linking targets.

\[Blog]
Title: {blog\_title}
Excerpt (first 1500 chars): {blog\_excerpt}

\[Wiki Card Titles]
{card\_titles\_numbered}

Rules:
1. Return at most 30 card titles.
2. Skip cards that are clearly off-topic.
3. Return the exact titles as given.

Output JSON:
{{"matched\_titles": \["...", "..."]}}
```

### 5.3 content\_match.md（Step 3 第二段）

```
You are an SEO internal-linking expert. Given a blog article and a set of candidate Wiki cards, recommend internal links.

\[Blog Markdown]
{blog\_markdown}

\[Candidate Wiki Cards]
{candidate\_cards\_formatted}

For each candidate, evaluate the semantic match (0.0 – 1.0). For matches with score ≥ {threshold}:
1. Pick an anchor\_text — must be a continuous span of text that already exists verbatim in the blog markdown.
2. Identify the paragraph where the anchor sits (insert\_paragraph).
3. Provide a one-sentence reason.

Hard rules:
- anchor\_text must NOT be in the first paragraph of the blog.
- anchor\_text must NOT be inside any heading (H1–H6).
- anchor\_text length: 2+ words / 4+ Chinese chars; not generic ("click here", "learn more").
- Each target\_url appears at most once.
- Maximum {max\_recommendations} recommendations.

Output JSON:
{{
  "recommendations": \[
    {{
      "target\_url": "...",
      "target\_title": "...",
      "anchor\_text": "...",
      "insert\_paragraph": "...",
      "relevance\_score": 0.85,
      "reason": "..."
    }}
  ]
}}
```

\---

## 6\. 接口设计

### 6.1 CLI

```bash
# Step 1：URL 入库
python -m app.cli intake \\
  --customer "BrandX-Inc" \\
  --urls-file urls.txt

# Step 2：批量生成 Wiki 卡片
python -m app.cli generate \\
  --customer "BrandX-Inc" \\
  --batch-size 10

# Step 3：博客匹配推荐（输出 JSON）
python -m app.cli recommend \\
  --customer "BrandX-Inc" \\
  --blog-url "https://brandx.com/blogs/foo" \\
  --blog-md ./foo.md

# Step 4：从 Step 3 的 JSON 生成 Excel
python -m app.cli report \\
  --customer "BrandX-Inc" \\
  --result ./recommend-result.json

# 一步到位（推荐用法）：Step 3 + Step 4 合并
python -m app.cli recommend-and-report \\
  --customer "BrandX-Inc" \\
  --blog-url "https://brandx.com/blogs/foo" \\
  --blog-md ./foo.md \\
  --threshold 0.6 \\
  --max 8
# 输出：自动生成 Excel 到 Data/Reference/{customer}/...xlsx，并打印路径
```

### 6.2 HTTP API

|Method|Path|Body|响应|
|-|-|-|-|
|POST|`/api/intake`|`IntakeRequest`|`IntakeResult`|
|POST|`/api/generate`|`GenerateRequest`|`GenerateResult`|
|POST|`/api/recommend`|`RecommendRequest`|`RecommendResult`|
|POST|`/api/report`|`ReportRequest`|`ReportResult`|
|POST|`/api/recommend-and-report`|`RecommendRequest`|`RecommendResult` + `ReportResult`|
|GET|`/api/customers/{customer}/urls`|—|URL 列表|
|GET|`/api/customers/{customer}/cards`|—|卡片列表（不含完整内容）|
|GET|`/api/customers/{customer}/cards/{title-slug}`|—|单张卡片完整内容|
|GET|`/api/customers/{customer}/reports`|—|Excel 报告列表|
|GET|`/api/customers/{customer}/reports/{filename}`|—|下载 Excel 文件|
|GET|`/api/health`|—|服务 + LLM 端点联通性|

\---

## 7\. 技术栈

|层|选型|版本|
|-|-|-|
|编程语言|Python|3.11+|
|Web 框架|FastAPI|≥ 0.110|
|ASGI 服务|uvicorn|≥ 0.27|
|HTTP 客户端|httpx|异步|
|HTML 解析|BeautifulSoup4 + trafilatura|—|
|LLM 客户端|openai SDK（指向 Qwen3-32B 私有 endpoint）|—|
|数据校验|Pydantic|v2|
|**Excel 生成**|**openpyxl**|**≥ 3.1**|
|CLI|typer|≥ 0.9|
|配置|pydantic-settings + .env|—|
|日志|loguru|—|
|测试|pytest + pytest-asyncio|—|

**.env 示例：**

```
DATA\_ROOT=../Data
LLM\_BASE\_URL=http://your-qwen-server/v1
LLM\_API\_KEY=sk-xxx
LLM\_MODEL=qwen3-32b-instruct
LLM\_MAX\_TOKENS=4096
LLM\_TIMEOUT=60
LLM\_MAX\_CONCURRENCY=3
CRAWLER\_TIMEOUT=30
CRAWLER\_MAX\_CONCURRENCY=5
CRAWLER\_USER\_AGENT=InternalLinkBot/1.0
DEFAULT\_BATCH\_SIZE=10
DEFAULT\_SCORE\_THRESHOLD=0.6
DEFAULT\_MAX\_RECOMMENDATIONS=8
```

\---

## 8\. 错误处理

|错误码|触发场景|处理|
|-|-|-|
|`INVALID\_CUSTOMER\_NAME`|customer 名包含路径非法字符且无法 slug 化|拒绝请求|
|`URL\_FETCH\_FAILED`|抓取超时 / 4xx / 5xx|记录失败，跳过该 URL，继续批次|
|`LLM\_TIMEOUT`|单次 LLM 调用超时|重试 2 次|
|`LLM\_INVALID\_JSON`|LLM 返回非合法 JSON|重试 1 次，仍失败则跳过|
|`ANCHOR\_NOT\_IN\_BLOG`|推荐返回的 anchor\_text 不在博客中|丢弃该条推荐，记录 discarded|
|`WIKI\_CARD\_EXISTS`|同 URL 已有卡片|only\_missing=True 时跳过；False 时覆盖|
|`EXCEL\_WRITE\_FAILED`|文件被占用 / 路径无权限|重试 1 次，仍失败则报错|

\---

## 9\. 验收标准

### 9.1 功能验收

|序号|验收项|
|-|-|
|AC-01|输入新客户名能自动创建 Raw / Wiki card / **Reference** 三个客户文件夹|
|AC-02|重复 URL 输入能去重，Internal-URL.md 不出现重复行|
|AC-03|Step 2 能批量爬取 20 个 URL 并生成 20 张合法 Wiki 卡片|
|AC-04|每张卡片包含 Title / Description / H\_Hierarchy / Web\_Abstract\_AI\_Generated 四个字段|
|AC-05|Step 3 输入博客 Markdown 后返回 ≤ max\_recommendations 条推荐|
|AC-06|所有推荐的 anchor\_text 100% 出现在博客 Markdown 中|
|AC-07|同一 target\_url 在一次推荐结果中只出现一次|
|AC-08|推荐不命中博客首段、不命中 H 标签|
|AC-09|Step 4 生成的 Excel 文件能在 Microsoft Excel / WPS / Numbers 中正常打开|
|AC-10|Excel Sheet 1 包含全部 10 列，Sheet 2 包含元信息|
|AC-11|Excel Score 列应用条件格式（绿/黄）正确显示|
|AC-12|Excel 文件名格式 `Recommendations-{slug}-{timestamp}.xlsx`，时间戳精确到秒|
|AC-13|同一博客多次跑 Step 4 生成多个文件，互不覆盖|
|AC-14|所有 LLM 调用记录到 `logs/llm\_calls/{date}.jsonl`|
|AC-15|重跑 Step 3 同博客，推荐 URL 集合一致率 ≥ 80%|

### 9.2 性能验收

|指标|目标|
|-|-|
|单 URL 爬取 + LLM 卡片生成|≤ 30s|
|100 URL 批量建卡（并发 3）|≤ 2 min|
|单博客两段匹配（500 张卡片库）|≤ 60s|
|Excel 生成（≤ 20 行推荐）|≤ 2s|

### 9.3 鲁棒性验收

|项|要求|
|-|-|
|单 URL 抓取失败不影响批次中其他 URL|✅|
|LLM 偶发返回非法 JSON 能重试|✅|
|同一脚本可重入|✅|
|客户名含中文 / 空格能正确创建文件夹|✅|
|Excel 文件被 Excel 应用打开锁定时不导致服务崩溃|✅|

\---

## 附录 A：完整数据流示意

```
用户输入
  ├── 客户名: "BrandX-Inc"
  ├── URL: "https://brandx.com/blogs/foo"
  └── blog.md
         │
         ▼
┌─────────────────────────────────────┐
│  Step 1：url\_intake                 │
│  - 创建 Data/Raw/BrandX-Inc/        │
│  - 创建 Data/Wiki card/BrandX-Inc/  │
│  - 创建 Data/Reference/BrandX-Inc/  │
│  - 追加 URL 到 Internal-URL.md       │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Step 2：wiki\_generator             │
│  - 读 Internal-URL.md                │
│  - 分批爬取 + LLM 生成卡片           │
│  - 写入 Wiki-\*.json                 │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Step 3：recommender                │
│  - 第一段：LLM 按卡片名筛选          │
│  - 第二段：LLM 读卡片 + 博客评分     │
│  - 校验 anchor\_text in blog          │
│  - 返回 RecommendResult              │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Step 4：excel\_reporter             │
│  - 生成 Excel（10 列 + 元信息）      │
│  - 应用样式 + 条件格式                │
│  - 保存到 Data/Reference/{客户}/    │
└─────────────────────────────────────┘
         │
         ▼
最终交付物：Recommendations-{blog}-{timestamp}.xlsx
（SEO 团队可直接执行内链插入）
```

\---

## 附录 B：Excel 报告样例（前 3 行预览）

|#|Source Blog URL|Source Blog Title|Actual Anchor Text|Target URL|Target Title|Insert Paragraph|
|-|-|-|-|-|-|-|
|1|https://brandx.com/blogs/dropshipping/find-suppliers|How to Find Reliable Dropshipping Suppliers|**dropshipping product research**|https://brandx.com/blogs/research/product-research-tools|Top 10 Product Research Tools|Once you've narrowed down your niche, the next critical step is dropshipping product research using data-driven tools to validate market demand.|
|2|（同上）|（同上）|**AliExpress vs Alibaba**|https://brandx.com/blogs/suppliers/aliexpress-alibaba-comparison|AliExpress vs Alibaba: Which Is Better?|When choosing a supplier platform, the AliExpress vs Alibaba decision is one of the first questions every dropshipper faces.|
|3|（同上）|（同上）|**MOQ negotiation tips**|https://brandx.com/blogs/business/moq-negotiation|How to Negotiate MOQ with Suppliers|For new sellers, MOQ negotiation tips can save thousands in initial inventory costs.|



