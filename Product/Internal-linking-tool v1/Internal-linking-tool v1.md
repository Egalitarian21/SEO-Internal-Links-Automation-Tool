# PRD：电商博客内链工作台（Internal Linking Workbench）v1

## 1\. 产品概述

### 1.1 定位

面向公司内部 SEO 实施团队的**交互式内链推荐与执行工具**。基于 Karpathy llm-wiki 思想，将客户 Shopify 博客通过 LLM 生成结构化 Wiki 知识卡片，构建语义知识图谱，实现锚文本的精准匹配与内链自动插入。

### 1.2 核心价值

* **效率提升**：AI 批量推荐 + 人工审核确认，替代人工逐篇查找
* **质量保障**：Wiki 卡片 + 语义匹配 > 关键词匹配，内链相关性更高
* **规范内嵌**：内链搭建规范编码为规则引擎，AI 推荐自动遵守规范约束
* **精准定位**：内链插入正文段落中间，非文末堆砌
* **直连执行**：审核通过后直接写入 Shopify，零手动操作

### 1.3 目标用户

公司内部 SEO 实施团队

### 1.4 项目约束

|约束|说明|
|-|-|
|开发人力|单人全栈|
|上线周期|40 天|
|成本策略|免费|

\---

## 2\. 工作流设计

### 2.1 完整流程（15 步）

```
┌─ 冷启动建库 ──────────────────────────────────────────────┐
│ ① 人工从 Sitemap 获取博客 URL                              │
│ ② 前端批量导入 URL                                         │
│ ③ 后端保存 Import Task                                     │
│ ④ 后端爬取博客内容                                         │
│ ⑤ 清洗 HTML / 提取正文 / 标题 / Meta / H标签              │
│ ⑥ LLM 批量生成 Wiki 知识卡片                               │
│ ⑦ Wiki Cards 入库（含向量索引）                             │
└────────────────────────────────────────────────────────────┘

┌─ 内链推荐 ────────────────────────────────────────────────┐
│ ⑧ 实施工程师在前端选择某篇博客进入推荐                      │
│ ⑨ 后端调用 LLM：                                           │
│    - 分析博客正文                                           │
│    - 依据「内链规范引擎」选择合适锚文本                       │
│    - 从 Wiki Cards 中语义匹配目标卡片                       │
│    - 三层相关性校验（锚文本↔目标、段落↔目标、目标可承接性）  │
│    - 生成内链建议（含精准插入位置）                           │
│ ⑩ 规范校验层：自动过滤违规建议 + 补充缺失类型                │
└────────────────────────────────────────────────────────────┘

┌─ 审核执行 ────────────────────────────────────────────────┐
│ ⑪ 前端展示待审批内链建议（含规范合规标记）                    │
│ ⑫ 人工 Approve / Reject（可编辑锚文本和目标）               │
│ ⑬ 发布前自动检查清单（对标规范第10节）                       │
│ ⑭ 生成最终博客 HTML（插入内链）                             │
│ ⑮ 调用 Shopify API 更新博客                                │
└────────────────────────────────────────────────────────────┘

┌─ 发布后维护 ──────────────────────────────────────────────┐
│ ⑯ 反向内链推荐：自动识别哪些旧文章应补加指向新文章的内链     │
└────────────────────────────────────────────────────────────┘
```

### 2.2 阶段视图

|阶段|步骤|关键动作|耗时特征|
|-|-|-|-|
|数据导入|①②③|人工操作 + 系统保存|秒级|
|内容抓取|④⑤|批量爬取 + 清洗|分钟级（异步）|
|知识库构建|⑥⑦|LLM 生成 Wiki 卡片 + 向量化|分钟级（异步）|
|内链推荐|⑧⑨⑩|LLM 分析 + 语义匹配 + 规范校验|10-30s/篇|
|审核执行|⑪⑫⑬⑭⑮|人工审核 + 检查清单 + 系统写入|人工决策 + 秒级执行|
|发布后维护|⑯|反向内链推荐|按需触发|

\---

## 3\. 内链规范引擎

> 将「锚文本选择与内链搭建规范」编码为系统规则，作为 AI 推荐的约束层和校验层。

### 3.1 插入位置规则（硬约束 — AI 推荐时强制过滤）

|规则ID|规则|实现方式|
|-|-|-|
|P-01|第一段不插入任何链接|`paragraph\_index == 0` 的锚文本候选自动丢弃|
|P-02|H1-H6 标题中不插入链接|检测锚文本所在 HTML 节点，`<h1>`-`<h6>` 内的候选丢弃|
|P-03|标题和列表冒号前的内容不插入链接|正则匹配 `:` 前文本，丢弃匹配的锚文本候选|
|P-04|信息类链接应在段落解释完毕后，非段首|锚文本 `char\_offset` 需 > 段落字符数的 30%|
|P-05|链接分布应均衡，不集中堆砌|计算段落间距，连续 2 个段落已有链接则跳过|
|P-06|同一目标 URL 同一篇文章只链接一次|去重：per article per target\_url|

### 3.2 锚文本选择规则（LLM Prompt 约束 + 后校验）

|规则ID|规则|校验方式|
|-|-|-|
|A-01|锚文本必须是文章正文中实际存在的文本|正则精确匹配原文|
|A-02|不允许单个单词作为锚文本|`word\_count >= 2`|
|A-03|不允许被截断或拆分的单词|检测锚文本首尾是否为完整词边界|
|A-04|不允许堆砌关键词的短语|LLM 自然度评分 + 人工审核|
|A-05|不允许通用锚文本（"点击这里""了解更多"）|黑名单过滤|
|A-06|"全称 (缩写)" 格式应整体作为锚文本|正则匹配括号格式|
|A-07|锚文本类型应多样化|统计已用类型分布，推荐时优先欠缺类型|

### 3.3 三层相关性校验（LLM 评分）

```
每条内链建议必须通过三层校验：

1. 锚文本 ↔ 目标页面主题        → relevance\_anchor\_target ≥ 0.7
2. 锚文本所在段落 ↔ 目标页面主题  → relevance\_paragraph\_target ≥ 0.6
3. 目标页面能承接/补充当前内容    → continuity\_score ≥ 0.6

三层均通过 → 进入推荐列表
任一层未通过 → 标记为 low\_confidence，仍展示但带警告标记
```

### 3.4 内链数量标准

|类型|最低要求|系统行为|
|-|-|-|
|产品/集合页内链|≥ 3 条|不足时系统提示"缺少产品内链"|
|博客/信息页内链|≥ 3 条|不足时系统提示"缺少博客内链"|
|反向内链（发布后）|≥ 3 篇旧文章|自动推荐旧文章补链方案|

### 3.5 目标页面选择规则

**产品/集合页内链触发条件：**

* 段落提到具体产品、产品类型、购买意图或商业词
* 出现大词或类目词 → 优先链接集合页
* 出现商业词（"购买 xx""xx 产品""xx 解决方案"）→ 链接产品页或集合页
* 复数形式或类目泛词 → 链接集合页
* "品牌词 + 通用词" → 整体作为锚文本链接集合页

**博客/信息页内链触发条件：**

* 某个概念、分类点或步骤可以由另一篇博客展开解释
* 段落内容与已有博客主题高度相关
* 指南类文章的分类点可延伸到更详细的教程

**禁止情况：**

* 信息性短语（"一项研究表明"）不链接到商业页面
* 与当前上下文无明显关系的页面不强行链接
* 同一锚文本不在多处反复指向同一 URL

### 3.6 Shopify URL 规范化

```python
def normalize\_shopify\_url(url):
    """Shopify 产品链接必须使用 canonical 路径"""
    # /collections/\*\*/products/\*\* → /products/\*\*
    # 例: /collections/all/products/widget → /products/widget
    return re.sub(r'/collections/\[^/]+/products/', '/products/', url)
```

### 3.7 发布前自动检查清单

系统在执行写入 Shopify 前自动执行以下检查，任一项未通过则阻断发布并提示修正：

|检查项|规则|
|-|-|
|✅ 产品/集合页内链 ≥ 3|不足则警告|
|✅ 博客内链 ≥ 3|不足则警告|
|✅ 首段无链接|有则阻断|
|✅ H 标签无链接|有则阻断|
|✅ 锚文本自然、未截断|异常则警告|
|✅ 无单词锚文本、通用锚文本|有则阻断|
|✅ 同一目标只链接一次|重复则自动去重|
|✅ 链接分布均衡|集中则警告|
|✅ Shopify URL 使用 canonical `/products/` 路径|自动修正|

\---

## 4\. 核心 AI 逻辑（llm-wiki 机制）

### 4.1 Wiki 知识卡片 — 核心抽象

> \*\*设计理念\*\*：不直接对原始文本做 embedding 检索，而是先让 LLM 将每篇博客"蒸馏"为结构化 Wiki 卡片。卡片是知识图谱的节点，承载语义关系、实体链接和主题标签，比 raw embedding 更精准、可解释、可调试。

**Wiki Card 结构示例：**

```json
{
  "card\_id": "wiki\_001",
  "source\_article\_id": "blog\_123",
  "title": "How to Optimize Shopify Product Pages for SEO",
  "slug": "optimize-shopify-product-pages-seo",
  "url": "https://store.com/blogs/seo/optimize-product-pages",
  "page\_type": "blog",
  "summary": "A comprehensive guide covering title tags, meta descriptions, image alt text, and URL structure for Shopify product pages.",
  "core\_topics": \["product page SEO", "Shopify optimization", "on-page SEO"],
  "entities": \["Shopify", "Google Search Console", "title tag", "meta description"],
  "target\_keywords": \["shopify product page seo", "optimize product pages"],
  "content\_type": "how-to guide",
  "semantic\_tags": \["technical-seo", "ecommerce", "shopify"],
  "linkable\_phrases": \[
    "product page optimization",
    "meta description best practices",
    "image alt text for ecommerce"
  ],
  "embedding": \[0.023, -0.145, ...]
}
```

> \*\*新增 `page\_type` 字段\*\*：`blog` | `product` | `collection`，用于区分目标页面类型，支持内链数量规范（产品类 ≥ 3、博客类 ≥ 3）的自动统计。

### 4.2 知识库构建流程（双轨制）

> \*\*设计决策\*\*：博客文章走完整 Wiki Card 流程（LLM 蒸馏）；产品页和集合页仅收录 URL + Meta Title，作为轻量链接目标参与匹配，不生成完整卡片。

**博客文章 → 完整 Wiki Card：**

```
每篇博客文章
    │
    ▼
LLM 分析（Qwen3-32B-Instruct）
    │  Prompt: "将这篇博客提炼为 Wiki 知识卡片，
    │           输出结构化 JSON，包含主题、实体、
    │           可链接短语等字段"
    ▼
结构化 Wiki Card（JSON）
    │
    ├──▶ 元数据字段 → PostgreSQL 存储（全文检索 + 过滤）
    │
    └──▶ summary + core\_topics → Embedding → pgvector 存储（语义检索）
```

**产品页 / 集合页 → 轻量记录：**

```
产品页 / 集合页
    │
    ▼
仅存储两个字段：
    - url（规范化后的 canonical URL）
    - meta\_title（页面 Meta Title）
    │
    ├──▶ PostgreSQL 存储（关键词匹配 + 过滤）
    │
    └──▶ meta\_title → Embedding → pgvector 存储（语义检索）
```

**匹配策略差异：**

|目标类型|匹配信号|匹配方式|
|-|-|-|
|博客（Wiki Card）|summary + core\_topics + entities + linkable\_phrases|向量语义检索 + 结构化字段匹配|
|产品/集合页（轻量）|meta\_title|向量语义检索 + 关键词匹配|

### 4.3 内链推荐流程（含规范校验）

```python
def recommend\_links(target\_article, wiki\_cards\_db, rules\_engine):
    # ═══ Step 1: LLM 提取锚文本候选 ═══
    anchor\_candidates = llm.analyze(
        content=target\_article.body\_html,
        instruction="""分析文章正文，提取适合作为内链锚文本的短语。
        规范约束：
        - 必须是正文中实际存在的文本（可精确查找）
        - 不少于 2 个词，不允许单个单词
        - 不允许通用锚文本（click here, learn more 等）
        - 应为自然的名词/名动词组/完整短语
        - 锚文本类型应多样化（完全匹配、部分匹配、语义相关、品牌词等）
        输出 JSON: \[{text, paragraph\_index, char\_offset, sentence\_context, anchor\_type}]"""
    )
    
    # ═══ Step 2: 插入位置硬约束过滤 ═══
    filtered = rules\_engine.filter\_positions(anchor\_candidates)
    # 自动丢弃：首段锚文本、H标签内锚文本、冒号前锚文本
    # 自动调整：段首信息链接移至段落后半部分
    
    # ═══ Step 3: 语义匹配 Wiki Cards + 轻量 Link Targets ═══
    for anchor in filtered:
        embedding = embed(anchor.text + anchor.sentence\_context)
        
        # 博客目标：从 Wiki Cards 检索（完整语义匹配）
        blog\_matches = pgvector.search(
            embedding, top\_k=10, table="wiki\_cards",
            filter={"source\_article\_id": {"$ne": target\_article.id}}
        )
        
        # 产品/集合目标：从 link\_targets 检索（meta\_title 语义匹配）
        product\_matches = pgvector.search(
            embedding, top\_k=10, table="link\_targets",
            filter={"page\_type": {"$in": \["product", "collection"]}}
        )
        
        # LLM 精排 + 三层相关性评分（合并博客 + 产品/集合候选）
        all\_matches = blog\_matches + product\_matches
        ranked = llm.rank\_with\_relevance\_check(
            anchor=anchor,
            candidates=all\_matches,
            checks=\["anchor\_target", "paragraph\_target", "continuity"]
        )
    
    # ═══ Step 4: 规范校验 \& 补充 ═══
    suggestions = rules\_engine.validate\_and\_enrich(ranked)
    # - 去重：同一 target\_url 只保留最高分
    # - URL 规范化：Shopify canonical 路径
    # - 数量检查：产品类 ≥ 3、博客类 ≥ 3，不足则补充推荐
    # - 分布检查：链接不集中在某段
    # - 类型多样性：锚文本类型分布检查
    
    return suggestions
```

### 4.4 反向内链推荐

```python
def recommend\_reverse\_links(new\_article, wiki\_cards\_db):
    """新文章发布后，找出应该补加指向新文章内链的旧文章"""
    new\_card = wiki\_cards\_db.get\_card(new\_article.id)
    
    # 在所有旧文章中搜索与新文章主题相关的段落
    candidates = pgvector.search(
        embed(new\_card.summary + new\_card.core\_topics),
        top\_k=20,
        filter={"page\_type": "blog", "source\_article\_id": {"$ne": new\_article.id}}
    )
    
    # LLM 对每个候选旧文章：找出可以插入新文章链接的位置
    reverse\_suggestions = \[]
    for old\_article in candidates:
        suggestion = llm.find\_insertion\_point(
            source=old\_article.body,
            target=new\_card,
            rules=rules\_engine  # 同样遵守所有规范
        )
        if suggestion:
            reverse\_suggestions.append(suggestion)
    
    # 至少推荐 3 篇旧文章（规范要求）
    return reverse\_suggestions\[:max(3, len(reverse\_suggestions))]
```

\---

## 5\. 技术架构

### 5.1 技术栈

|维度|选择|理由|
|-|-|-|
|前端框架|**Next.js 15**|全栈能力、SSR、单人项目效率最高|
|UI 组件库|**shadcn/ui**|现代、轻量、高度可定制|
|后端运行时|**Python + FastAPI**|LLM 编排 + NLP + Wiki 图谱构建依赖 Python 生态|
|数据库|**Supabase**（含 pgvector）|托管 PostgreSQL + 向量检索一体化，免费起步|
|认证方案|**Auth.js v5**|内部团队身份管理|
|LLM|**Qwen3-32B-Instruct**（私有部署）|英文理解强、JSON 稳定、OpenAI-Compatible、成本可控|
|Embedding|**bge-large-en-v1.5**（私有部署）|英文语义匹配优秀、可本地部署|
|部署平台|**Vercel**（前端）+ **Railway**（后端）|免费起步、无需运维|

### 5.2 系统架构图

```
┌─────────────────────────────────────────────────────────┐
│  前端 (Next.js 15 + shadcn/ui) — Vercel                 │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │项目管理  │ │文章/卡片  │ │内链推荐   │ │审核执行   │   │
│  └─────────┘ └──────────┘ └──────────┘ └──────────┘   │
└────────────────────────┬────────────────────────────────┘
                         │ REST API
┌────────────────────────▼────────────────────────────────┐
│  后端 (Python + FastAPI) — Railway                       │
│  ┌───────────────┐ ┌───────────────┐ ┌──────────────┐  │
│  │sitemap\_importer│ │wiki\_card\_gen  │ │anchor\_matcher│  │
│  ├───────────────┤ ├───────────────┤ ├──────────────┤  │
│  │web\_crawler     │ │content\_cleaner│ │rules\_engine  │  │
│  ├───────────────┤ ├───────────────┤ ├──────────────┤  │
│  │shopify\_pub    │ │html\_inserter  │ │review\_service│  │
│  └───────────────┘ └───────────────┘ └──────────────┘  │
│                    ┌───────────────┐                     │
│                    │ LangChain     │                     │
│                    └───────────────┘                     │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│  数据层                                                   │
│  ┌──────────────────┐  ┌────────────────────────────┐   │
│  │ Supabase         │  │ 私有 LLM 服务器             │   │
│  │ (PostgreSQL +    │  │ Qwen3-32B + bge-large-en   │   │
│  │  pgvector)       │  │ (OpenAI-Compatible API)    │   │
│  └──────────────────┘  └────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**架构关键说明：**

* **向量检索是核心**：Supabase pgvector 直接承载 Wiki 卡片的语义向量存储与检索，避免引入独立向量数据库，控制复杂度
* **前后端分离是必要的**：LLM 批量处理任务耗时长，必须运行在支持持久进程的平台（Railway），不能放在 Vercel Serverless 中
* **Python 后端不可替代**：Wiki 知识图谱构建、LLM 编排、NLP 文本处理三项核心能力均依赖 Python 生态
* **规范引擎是独立模块**：`rules\_engine` 封装所有内链规范，AI 推荐结果必须经过规范校验后才能进入审核队列

\---

## 6\. 后端模块设计

```
backend/app/
├── sitemap\_importer.py       # 处理人工导入 URL
├── web\_crawler.py            # 根据 URL 爬取博客内容
├── content\_cleaner.py        # 清洗 HTML、提取正文/标题/Meta/H标签
├── wiki\_card\_generator.py    # LLM 批量生成 Wiki 知识卡片
├── anchor\_matcher.py         # LLM 选择锚文本 + 语义匹配 Wiki Cards
├── rules\_engine.py           # 内链规范引擎（位置/锚文本/数量/分布/URL校验）
├── html\_inserter.py          # 精准定位插入内链到正文段落
├── reverse\_linker.py         # 反向内链推荐（新文章发布后）
├── shopify\_publisher.py      # 调用 Shopify API 更新博客
├── review\_service.py         # 审核流程管理
├── models.py                 # SQLAlchemy / Supabase ORM
├── schemas.py                # Pydantic 请求/响应模型
└── routers/
    ├── imports.py            # URL 导入接口
    ├── drafts.py             # 博客草稿/内容接口
    ├── cards.py              # Wiki 卡片 CRUD
    ├── suggestions.py        # 内链推荐接口
    ├── review.py             # 审核操作接口
    └── publish.py            # Shopify 发布接口
```

\---

## 7\. 核心数据表

|表名|用途|关键字段|
|-|-|-|
|`imported\_blog\_urls`|存储人工导入的 Sitemap 博客 URL|project\_id, url, status, imported\_at|
|`blog\_drafts`|存储爬取后的博客标题、正文、HTML、Meta|article\_id, title, body\_html, body\_text, meta\_description, headings(JSONB), shopify\_article\_id|
|`wiki\_cards`|存储 LLM 生成的 Wiki 知识卡片（**仅博客文章**）|card\_id, source\_article\_id, **page\_type='blog'**, title, summary, core\_topics, entities, semantic\_tags, linkable\_phrases, embedding(vector)|
|`link\_targets`|存储产品页/集合页的轻量记录（**仅 URL + Meta Title**）|target\_id, project\_id, **page\_type**('product'/'collection'), url, meta\_title, embedding(vector)|
|`anchor\_suggestions`|存储某篇博客的内链锚文本建议|source\_article\_id, target\_card\_id, anchor\_text, **anchor\_type**, insert\_position(JSONB), relevance\_score, **relevance\_details**(JSONB), reason, status, **rule\_violations**(JSONB)|
|`review\_tasks`|存储人工审核任务状态|suggestion\_id, reviewer, action(approve/reject), edited\_anchor, reviewed\_at|
|`shopify\_publish\_jobs`|存储发布到 Shopify 的任务和结果|article\_id, before\_html, after\_html, **checklist\_result**(JSONB), shopify\_response, success, executed\_at|

### 7.1 v2.1 新增/变更字段

|字段|所属表|说明|
|-|-|-|
|`page\_type`|wiki\_cards / link\_targets|`blog`(wiki\_cards) / `product` / `collection`(link\_targets)|
|`anchor\_type`|anchor\_suggestions|锚文本类型：`exact\_match` / `partial\_match` / `semantic` / `brand` / `title`|
|`relevance\_details`|anchor\_suggestions|三层相关性评分 JSON：`{anchor\_target, paragraph\_target, continuity}`|
|`rule\_violations`|anchor\_suggestions|规范校验结果：`\[{rule\_id, severity, message}]`，空数组 = 合规|
|`checklist\_result`|shopify\_publish\_jobs|发布前检查清单结果 JSON|

\---

## 8\. API 设计

### 8.1 项目 \& 导入

|Method|Endpoint|描述|
|-|-|-|
|POST|`/api/projects`|创建客户项目（Shopify domain + token）|
|GET|`/api/projects`|项目列表|
|POST|`/api/projects/:id/import`|上传 URL 表格，触发批量爬取|
|GET|`/api/projects/:id/import-status`|导入/爬取进度|

### 8.2 文章 \& Wiki 卡片

|Method|Endpoint|描述|
|-|-|-|
|GET|`/api/projects/:id/articles`|文章列表（含状态）|
|GET|`/api/articles/:id`|文章详情 + 关联 Wiki Card|
|POST|`/api/projects/:id/build-cards`|触发 LLM 批量生成 Wiki Cards|
|GET|`/api/projects/:id/cards`|Wiki 卡片列表（可搜索、按 page\_type 过滤）|
|GET|`/api/cards/:id`|单张卡片详情|
|PATCH|`/api/cards/:id`|手动编辑卡片（调优推荐）|

### 8.3 内链推荐

|Method|Endpoint|描述|
|-|-|-|
|POST|`/api/articles/:id/recommend`|单篇文章内链推荐（含规范校验）|
|POST|`/api/projects/:id/batch-recommend`|批量推荐（异步）|
|GET|`/api/projects/:id/suggestions`|推荐列表（筛选 status、page\_type、rule\_violations）|
|POST|`/api/articles/:id/reverse-recommend`|反向内链推荐（新文章→旧文章补链）|

### 8.4 审核 \& 执行

|Method|Endpoint|描述|
|-|-|-|
|PATCH|`/api/suggestions/:id`|Approve / Reject（可编辑锚文本）|
|POST|`/api/suggestions/batch-review`|批量审核|
|POST|`/api/articles/:id/pre-publish-check`|执行发布前检查清单|
|POST|`/api/suggestions/:id/execute`|执行写入 Shopify|
|POST|`/api/suggestions/batch-execute`|批量执行|
|POST|`/api/publish-jobs/:id/rollback`|回滚到原始 HTML|

\---

## 9\. 前端页面规划

### 9.1 页面结构

```
├── Dashboard            （项目概览、任务进度）
├── 项目管理
│   ├── 项目列表
│   └── 新建项目（Shopify 凭证配置）
├── 项目工作台
│   ├── URL 导入         （上传表格、查看爬取进度）
│   ├── Wiki 知识库      （卡片列表、按 page\_type 分组、搜索、手动编辑）
│   ├── 内链推荐         （选择文章 → 触发推荐 → 查看结果 + 规范合规标记）
│   ├── 审核 \& 发布      （Approve/Reject 看板 → 检查清单 → 批量执行）
│   └── 反向内链         （新文章发布后 → 推荐旧文章补链方案）
└── 任务监控             （异步任务队列状态）
```

### 9.2 关键交互设计

**推荐审核卡片（含规范标记）：**

```
┌──────────────────────────────────────────────────────┐
│ 📝 源文章: How to Start Dropshipping on Shopify      │
│ ────────────────────────────────────────────────────  │
│ 📍 段落 3:                                            │
│ "...you'll need to find reliable \[dropshipping        │
│ suppliers] that offer fast shipping times..."         │
│                         ↑ 锚文本（高亮）               │
│ ────────────────────────────────────────────────────  │
│ 🔗 推荐目标: Top 10 Dropshipping Suppliers (blog)     │
│    URL: /blogs/guides/dropshipping-suppliers          │
│    匹配度: 0.92 | 类型: partial\_match                 │
│    理由: "suppliers" 主题与目标博客高度相关            │
│ ────────────────────────────────────────────────────  │
│ ✅ 规范合规    三层校验: ✓ ✓ ✓                         │
│ ────────────────────────────────────────────────────  │
│ \[✅ Approve]  \[✏️ Edit]  \[❌ Reject]                   │
└──────────────────────────────────────────────────────┘
```

**发布前检查清单面板：**

```
┌──────────────────────────────────────────────────────┐
│ 📋 发布前检查 — "How to Start Dropshipping"           │
│ ────────────────────────────────────────────────────  │
│ ✅ 产品/集合页内链: 4 条 (≥ 3)                        │
│ ✅ 博客内链: 5 条 (≥ 3)                               │
│ ✅ 首段无链接                                         │
│ ✅ H 标签无链接                                       │
│ ✅ 锚文本自然、未截断                                  │
│ ✅ 无单词/通用锚文本                                   │
│ ✅ 同一目标仅链接一次                                  │
│ ✅ 链接分布均衡                                       │
│ ✅ Shopify URL 已规范化                               │
│ ────────────────────────────────────────────────────  │
│ 状态: 全部通过 ✅                                     │
│ \[🚀 确认发布到 Shopify]                               │
└──────────────────────────────────────────────────────┘
```

\---

## 10\. 非功能需求

|维度|要求|
|-|-|
|性能|单篇推荐 < 30s；Wiki 卡片生成 < 10s/篇|
|可靠性|Shopify 写入前快照 before\_html，支持一键回滚|
|安全|Shopify Token 加密存储；Auth.js 内部认证|
|成本|免费方案起步（Supabase Free + Vercel Hobby + Railway Starter）|
|可观测|异步任务进度可视化；发布日志完整；规范违规统计|

\---

## 11\. 里程碑（40天）

|阶段|天数|范围|
|-|-|-|
|**M1 - 基础框架**|Day 1-8|项目骨架搭建、Supabase 数据表、FastAPI 基础路由、Next.js 页面骨架、Shopify API 对接验证|
|**M2 - 爬取 \& 知识库**|Day 9-18|URL 导入 → 批量爬取 → 内容清洗 → LLM Wiki Card 生成 → pgvector 入库|
|**M3 - 内链推荐引擎**|Day 19-28|锚文本提取 → 规范引擎 → 语义匹配 → 三层校验 → 推荐排序 → 精准定位 → 前端推荐界面|
|**M4 - 审核 \& 发布**|Day 29-36|审核看板 → 检查清单 → 批量操作 → HTML 生成 → Shopify 写入 → 回滚 → 反向内链|
|**M5 - 打磨上线**|Day 37-40|推荐质量调优、规范引擎微调、边界 case、团队试用、bug 修复|

\---

## 12\. 开放问题

* \[ ] Embedding 模型最终选型：bge-large-en-v1.5 够用还是需要 benchmark？
* \[ ] Wiki Card Prompt 模板设计：需要几轮迭代确定最优结构
* \[ ] Shopify API Rate Limit（REST: 40/s，GraphQL: 50 points/s）应对策略
* \[ ] 知识库是否需要包含产品页和集合页？（当前规范要求产品内链 ≥ 3，需要产品页信息入库）
* \[ ] 规范引擎的规则是否需要支持前端可配置？（不同客户不同规则）
* \[ ] 后续是否需要"内链健康度"仪表盘（孤岛页面检测、内链分布热力图、404 断链检查）

