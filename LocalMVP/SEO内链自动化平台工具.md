# SEO内链自动化平台工具

适用对象：Shopify 建站客户 产品定位：面向 SEO 实施团队的内链自动化、审核、写回与互链管理平台

核心原则：

```text
AI 负责，不负责最终决策；
规则负责兜底，不依赖模型自觉；
人工负责审核，不重复做低价值检索；
数据库负责可追踪，不让流程停留在 Prompt 层。
```

最终形态：

```text
客户站点管理
    ↓
内容数据库
    ↓
博客内链工作台
    ↓
候选锚文本
    ↓
候选链接
    ↓
人工审核
    ↓
插入预览
    ↓
Shopify 写回
    ↓
旧博客回链
    ↓
偏好沉淀
    ↓
审计与回滚
```
---

## 1. 项目背景

当前实施团队在为 Shopify 客户维护博客内容时，需要人工完成以下工作：

1.  检查博客正文是否存在足够的站内链接。
    
2.  判断哪些短语适合作为锚文本。
    
3.  从大量博客页、集合页、产品页中选择合适目标链接。
    
4.  手动插入链接。
    
5.  发布前检查链接数量、锚文本自然性、目标页面相关性。
    
6.  新博客发布后，回头检查旧博客是否应链接到新博客。
    

现有流程高度依赖人工经验，存在以下问题：

*   内链添加效率低。
    
*   不同人员标准不一致。
    
*   新旧博客之间缺少系统性互链。
    
*   内链目标页面选择缺乏可解释依据。
    
*   无法沉淀历史审核偏好。
    
*   Shopify 写回前后缺少可回滚快照。
    
*   大量客户站点并行处理时难以管理任务状态。
    

本项目基于现有方案中的核心思路：使用 **关键词簇 / 集群规划 / 博客、集合、产品存量表 / 博客原文** 建立数据库；输入博客后结合硬性规则和偏好文档生成候选锚文本；再通过 `集群 → 关键词 → 卡片` 三层筛选候选链接；最后触发旧博客链向新博客的互链流程。

---

## 2. 外部依据与关键约束

### 2.1 Google SEO 约束

Google 对链接文本的基本要求是：锚文本应具有描述性、合理简洁，并且同时与当前页面和目标页面相关；不使用 “click here”“read more” 这类泛锚文本。平台的锚文本候选规则必须遵守该原则。

### 2.2 Shopify API 约束

Shopify GraphQL Admin API 当前最新文档版本为 2026-07。新开发的 Shopify 集成应优先基于 GraphQL Admin API，而不是继续依赖 REST Admin API。

Shopify Article 对象包含文章内容、作者信息、元数据，文章属于 Blog，并可包含 HTML 格式正文、summary text 和图片。因此博客原文库应优先从 Shopify Article 相关字段中抽取正文、摘要、SEO 信息、发布时间、更新时间等数据。

Shopify API 存在分页和速率限制，大规模同步博客、集合页、产品页时必须设计分页、限流、失败重试和增量同步机制。

### 2.3 数据库与检索约束

PostgreSQL 支持全文检索，可用于页面标题、Meta Description、H 标签、Excerpt、正文块等内容的关键词召回和排序。

pgvector 支持在 PostgreSQL 中存储向量，并进行向量相似度搜索，适合将结构化过滤与语义检索放在同一数据层中。

PostgreSQL 支持 Row Level Security，可用于多租户数据隔离。

PostgreSQL 支持表分区，适合在大规模任务日志、候选锚文本、结果、正文分块等表持续增长后进行性能优化。

---

## 3. 产品目标

### 3.1 核心目标

构建一个面向 Shopify 客户站点的 内链自动化平台，实现：

```text
内容入库
→ 博客解析
→ 候选锚文本识别
→ 候选目标链接召回
→ 结果排序
→ 人工审核确认
→ 旧博客互链
→ Shopify 写回
→ 结果记录与偏好沉淀
```

### 3.2 业务目标

| 目标 | 说明 |
| --- | --- |
| 提升效率 | 将单篇博客人工内链处理时间从 20–40 分钟降低到 5–10 分钟 |
| 标准统一 | 所有候选锚文本和候选链接均受硬性规则和偏好文档约束 |
| 可解释 | 每个链接必须展示原因、匹配字段、分数构成 |
| 可审核 | 所有 AI 必须经过人工确认后才能写回 |
| 可回滚 | 每次写回 Shopify 前后必须保存快照 |
| 可扩展 | 支持多客户、多站点、多任务并发处理 |
| 可沉淀 | 人工确认结果可用于后续偏好文档更新，但必须人工审核 |

---

## 4. 产品边界

### 4.1 必须实现

1.  Shopify 内容同步。
    
2.  页面结构化卡片库。
    
3.  博客原文库。
    
4.  HTML / Markdown 博客原文统一解析。
    
5.  候选锚文本生成。
    
6.  候选链接。
    
7.  人工审核界面。
    
8.  内链插入预览。
    
9.  Shopify 写回。
    
10.  写回前后快照。
    
11.  旧博客链向新博客互链流程。
    
12.  偏好文档版本管理。
    
13.  任务队列与任务状态追踪。
    
14.  基础权限和客户隔离。
    

### 4.2 不做

1.  不自动发布未发布博客。
    
2.  不自动删除已有内链。
    
3.  不绕过人工审核直接批量写回。
    
4.  不自动决定偏好文档正式生效。
    
5.  不做跨客户数据共享。
    
6.  不做外链自动插入。
    
7.  不做 Shopify 主题模板修改。
    
8.  不替代完整 SEO 审核系统。
    

---

## 5. 用户角色

| 角色 | 权限 |
| --- | --- |
| Super Admin | 管理所有租户、站点、用户、任务、系统配置 |
| SEO Specialist | 执行内链、审核候选链接、提交写回 |
| Content Editor | 查看博客、预览插入结果、提交修改 |
| Viewer | 只读查看任务、结果、日志 |

---

## 6. 核心业务流程

### 6.1 内容同步流程

```text
用户选择 Shopify 店铺
→ 点击同步
→ 系统拉取 blog / collection / product 数据
→ 标准化 URL、Title、Meta、H 标签、Excerpt
→ 生成页面结构化卡片
→ 保存原始 HTML / Markdown 快照
→ 清洗正文并生成 article_blocks
→ 生成全文检索索引和向量索引
→ 同步完成
```

**功能要求**

1.  支持全量同步。
    
2.  支持增量同步。
    
3.  支持按 page\_type 同步：
    
    *   blog
        
    *   collection
        
    *   product
        
4.  支持失败重试。
    
5.  支持查看同步日志。
    
6.  支持跳过未发布页面。
    
7.  支持记录 Shopify `updatedAt`。
    
8.  支持对 URL 做 canonical 规范化。
    
9.  产品 URL 如存在 `/collections/{handle}/products/{handle}`，系统应转换为 canonical 产品路径 `/products/{handle}`。
    

---

### 6.2 博客输入与解析流程

```text
用户输入 / 选择一篇博客
→ 系统读取原始正文
→ 判断格式 HTML / Markdown
→ 转换为统一 AST
→ 拆分为正文块
→ 标记首段、标题、列表、图片、已有链接
→ 进入候选锚文本识别
```

**正文块结构**

每个正文块至少包含：

```json
{
  "block_id": "string",
  "page_id": "string",
  "block_index": 1,
  "block_type": "paragraph",
  "heading_level": "h2",
  "section_title": "XXX",
  "topic": "XXX",
  "content": "paragraph content",
  "has_existing_link": false,
  "link_count": 0,
  "is_first_paragraph": false
}
```

**解析规则**

1.  H1–H6 不允许作为锚文本候选。
    
2.  首段默认不生成锚文本候选。
    
3.  已存在 `<a>` 标签或 Markdown link 的文本不允许再次作为候选。
    
4.  列表项可以参与候选识别，但冒号前的项目标题不允许加链接。
    
5.  图片、脚注、导航、广告块不参与候选识别。
    
6.  表格内容默认不参与候选识别，除非后续单独启用表格处理模式。
    

---

### 6.3 候选锚文本生成流程

```text
博客正文块
+ 硬性规则
+ 当前启用的 Preference Doc
→ LLM 识别候选锚文本
→ 系统二次规则校验
→ 保存 anchor_candidates
```

**输入内容**

1.  博客正文 AST。
    
2.  内链硬性规则。
    
3.  当前客户启用的锚文本偏好文档。
    
4.  已存在内链列表。
    
5.  当前博客的页面主题、关键词、集群信息。
    

**输出字段**

```json
{
  "candidates": [
    {
      "anchor_text": "glider recliner",
      "context": "The right glider recliner can make your nursery more comfortable...",
      "link_type": "collection",
      "block_id": "block_123",
      "start_offset": 12,
      "end_offset": 28,
      "reason": "Product category phrase with commercial relevance"
    }
  ]
}
```

**候选锚文本硬性过滤**

系统必须二次过滤以下情况：

| 规则 | 处理 |
| --- | --- |
| 锚文本为空 | 删除 |
| 锚文本只包含 1 个普通单词 | 删除 |
| 锚文本超过 12 个英文词或等价长度 | 降权或删除 |
| 锚文本位于标题中 | 删除 |
| 锚文本位于首段 | 删除 |
| 锚文本已被链接覆盖 | 删除 |
| 锚文本为 click here / read more / this / here | 删除 |
| 锚文本与上下文无明显语义关系 | 删除 |
| 同一段候选过多 | 最多保留 1–2 个 |
| 同一语义重复候选 | 保留最高分候选 |

---

### 6.4 候选链接召回流程

```text
候选锚文本 + 上下文
→ 匹配所属集群
→ 匹配集群下关键词
→ 召回对应页面卡片
→ 按页面类型过滤
→ 初筛 Top 10
→ 语义重排
→ 返回 Top 3 给人工审核
```

**召回策略**

采用 Hybrid Retrieval：

```text
规则过滤
+ 集群匹配
+ 关键词匹配
+ 页面类型过滤
+ PostgreSQL 全文检索
+ pgvector 向量相似度
+ SEO 权重加权
+ 人工偏好加权
```

**结果字段**

```json
{
  "anchor_text": "glider recliner",
  "recommendations": [
    {
      "target_page_id": "page_456",
      "rank": 1,
      "url": "https://example.com/collections/glider-recliners",
      "title": "Glider Recliners",
      "page_type": "collection",
      "meta_description": "Shop comfortable glider recliners...",
      "score_total": 91.5,
      "score_cluster": 20,
      "score_keyword": 18,
      "score_page_type": 15,
      "score_semantic": 24,
      "score_title": 10,
      "score_history": 4.5,
      "reason": "Anchor text matches collection category and paragraph contains product selection intent."
    }
  ]
}

```

**评分公式**

```plaintext
score_total =score_cluster+ score_keyword+ score_page_type+ score_semantic+ score_title+ score_history+ score_quality- penalty_duplicate- penalty_competition- penalty_over_optimization- penalty_distance
score_total = min(max(score_total, 0), 100)  # 最终分数限制在 0–100
```

**分数字段含义**

| **字段** | **满分** | **含义** | **计算方式** |
| --- | --- | --- | --- |
| **score\_cluster** | 20 | 集群匹配分 | 目标页面集群与锚文本预测集群一致得 20；相关集群得 12；不相关得 0 |
| **score\_keyword** | 20 | 关键词匹配分 | 锚文本与目标关键词完全匹配得 20；单复数/词形变化得 18；部分匹配最高 15；同义词匹配得 12；无匹配得 0 |
| **score\_page\_type** | 15 | 页面类型匹配分 | 推荐类型与目标页面类型一致得 15；相近类型得 6–10；不匹配得 0–5 |
| **score\_semantic** | 25 | 语义相关分 | 使用锚文本 + 上下文与目标页面 Title + H1 + Meta + Excerpt + H标签摘要做向量相似度计算，score\_semantic = cosine\_similarity \* 25 |
| **score\_title** | 10 | 标题匹配分 | 锚文本与目标页面 Title / H1 的 token overlap 比例 × 10 |
| **score\_history** | 5 | 历史偏好分 | 根据同类锚文本、同类页面类型、同集群历史人工接受率计算；冷启动默认 2.5 |
| **score\_quality** | 5 | 目标页面质量分 | 页面已发布、可索引、Title/Meta/H1 完整、URL 为 canonical、重点页面，每项 1 分 |

### 惩罚项

| **字段** | **最高惩罚** | **触发条件** |
| --- | --- | --- |
| **penalty\_duplicate** | 50 | 当前文章已链接过同一目标页面 |
| **penalty\_competition** | 20 | 目标页面与当前文章关键词高度重复，可能造成内部竞争 |
| **penalty\_over\_optimization** | 10 | 同一目标页面历史锚文本中过多使用完全匹配关键词 |
| **penalty\_distance** | 15 | 语义相关分过低，说明目标页面与当前上下文距离较远 |

### 推荐等级

| score\_total | 等级 | 处理方式 |
| --- | --- | --- |
| 85–100 | Strong Match | 优先进入 Top 3 |
| 70–84 | Good Match | 可进入 Top 3 |
| 55–69 | Weak Match | 候选不足时展示 |
| 40–54 | Poor Match | 默认不展示 |
| 0–39 | Reject | 不进入推荐排序规则按 |

**排序规则**

*   按 `score_total` 从高到低排序。
    

*   若分差小于 3 分，优先选择 `page_type` 与 `link_type_suggestion` 完全一致的页面。
    

*   若仍相同，优先选择 `score_semantic` 更高的页面。
    

*   若仍相同，优先选择 `score_keyword` 更高的页面。
    

*   若仍相同，优先选择历史人工接受率更高的页面。
    

*   最终返回 Top 3 给人工审核。
    

---

### 6.5 人工审核流程

```text
系统展示候选锚文本
→ 每个锚文本展示 Top 3 候选链接
→ 用户查看原因
→ 用户选择 / 替换 / 拒绝
→ 系统生成插入预览
→ 用户确认保存
```

**审核界面要求**

每条候选锚文本展示：

1.  锚文本。
    
2.  所在段落上下文。
    
3.  所属正文位置。
    
4.  页面类型。
    
5.  Top 3 候选链接卡片。
    
6.  每个候选链接的：
    
    *   URL
        
    *   Title
        
    *   Page Type
        
    *   Meta Description
        
    *   所属集群
        
    *   所属关键词
        
    *   分数
        
    *   原因
        
7.  操作按钮：
    
    *   选择此链接
        
    *   替换 URL
        
    *   拒绝此候选
        
    *   查看目标页面
        

**人工决策类型**

| 决策 | 含义 |
| --- | --- |
| approve | 接受系统 |
| reject\_anchor | 拒绝该锚文本 |
| reject\_target | 锚文本可用，但目标链接不合适 |
| replace\_target | 用户手动替换目标 URL |
| skip | 本次跳过 |

---

### 6.6 内链插入与预览流程

```text
用户完成审核
→ 系统根据 block_id + offset 定位原文
→ 插入 HTML anchor
→ 生成预览正文
→ 检查规则
→ 用户确认
→ 创建写回任务
```

**插入规则**

1.  不改写原文句子，除非用户主动编辑。
    
2.  只对原文中精确匹配的锚文本加链接。
    
3.  如果同一锚文本出现多次，默认只链接审核时指定位置。
    
4.  插入后不得破坏 HTML 结构。
    
5.  插入后不得破坏 Shopify Liquid 片段。
    
6.  插入后需要重新解析正文，确认链接已成功生成。
    
7.  插入后需要重新统计正文内链数量。
    

**插入格式**

HTML 输入：

```html
<a href="https://example.com/collections/glider-recliners">glider recliner</a>
```

Markdown 输入：

```markdown
[glider recliner](https://example.com/collections/glider-recliners)
```

写回 Shopify 时如 Shopify Article 正文字段要求 HTML，应统一转换为 HTML。

---

### 6.7 Shopify 写回流程

```text
用户确认预览
→ 系统保存 before snapshot
→ 调用 Shopify GraphQL Admin API
→ 写回文章正文
→ 保存 after snapshot
→ 重新拉取 Shopify 正文校验
→ 标记任务成功 / 失败
```

**写回要求**

1.  写回前必须保存原文快照。
    
2.  写回后必须保存新正文快照。
    
3.  写回失败必须保留错误响应。
    
4.  写回成功后必须重新读取文章内容进行校验。
    
5.  同一篇博客同一时间只允许一个写回任务执行。
    
6.  写回任务必须支持失败重试，但不得重复插入同一链接。
    
7.  所有写回必须记录操作者、时间、目标 URL、锚文本、Shopify 响应。
    

**回滚要求**

用户可选择某次写回记录执行回滚：

```text
选择历史写回记录
→ 查看 before snapshot
→ 用户确认回滚
→ 系统写回 before snapshot 内容
→ 保存 rollback 记录
```
---

### 6.8 旧博客链向新博客流程

```text
新博客完成内链并保存
→ 系统进入互链环节
→ 从上一阶段 Top 10 候选卡片中筛选 blog 页面
→ 展示可反向互链旧博客
→ 用户选择旧博客
→ 系统创建反向互链任务队列
→ 逐篇读取旧博客正文
→ 在旧博客中寻找适合链接到新博客的锚文本
→ 用户确认
→ 写回旧博客
→ 输出互链结果
```

**互链候选旧博客筛选条件**

1.  页面类型为 blog。
    
2.  与新博客处于相同或相近集群。
    
3.  与新博客关键词相关。
    
4.  当前旧博客未链接到新博客。
    
5.  旧博客正文中存在适合承接新博客主题的锚文本。
    
6.  不与新博客主题重复竞争严重。
    
7.  旧博客状态为 published。
    

**互链结果输出**

```json
{
  "new_blog": {
    "title": "How to Choose a Glider Recliner",
    "url": "https://example.com/blogs/news/how-to-choose-a-glider-recliner"
  },
  "backlinks_created": [
    {
      "source_old_blog": "Nursery Chair Buying Guide",
      "anchor_text": "glider recliner for nursery",
      "target_url": "https://example.com/blogs/news/how-to-choose-a-glider-recliner",
      "status": "success"
    }
  ]
}
```
---

## 7. 偏好文档管理

### 7.1 Preference Doc 目标

Preference Doc 用于沉淀客户或团队对内链添加风格的偏好，例如：

1.  锚文本更偏自然短语还是精准关键词。
    
2.  产品页、集合页、博客页的使用场景。
    
3.  哪些段落位置更适合加链接。
    
4.  是否偏向少量高相关链接。
    
5.  是否避免某些 CTA 型锚文本。
    
6.  对完全匹配锚文本的容忍度。
    

---

### 7.2 偏好文档版本状态

| 状态 | 说明 |
| --- | --- |
| draft | AI 生成或人工编辑中 |
| pending\_review | 等待 OPS Manager 审核 |
| active | 当前生效版本 |
| archived | 历史版本 |
| rejected | 审核拒绝 |

---

### 7.3 动态偏好更新流程

```text
用户完成一批内链审核
→ 系统收集新增链接列表
→ 调用 Preference Updater
→ 生成偏好更新草稿
→ OPS Manager 审核
→ 通过后生成新版本
→ 新版本生效
```

**强制约束**

1.  AI 只能生成偏好更新草稿。
    
2.  偏好更新不得自动生效。
    
3.  不允许生成单一 URL 绑定规则。
    
4.  不允许生成单一 anchor → target 固定映射。
    
5.  不允许把单篇文章特征沉淀为长期规则。
    
6.  新规则必须抽象为结构性偏好、语义触发偏好或链接策略偏好。
    
7.  冲突规则必须提示人工确认。
    

---

## 8. 硬性规则管理

硬性规则独立于 Preference Doc，优先级高于偏好文档。

### 默认硬性规则

1.  首段不加内链。
    
2.  H1–H6 不加内链。
    
3.  已有链接文本不重复加链接。
    
4.  同一目标页面在同一篇文章中默认只链接一次。
    
5.  锚文本必须来自原文。
    
6.  锚文本不得被截断。
    
7.  不使用 click here / read more / learn more / this 等泛锚文本。
    
8.  不向 noindex / 404 / 重定向目标页面链接。
    
9.  产品 URL 优先使用 canonical 产品路径。
    
10.  每段最多 1–2 个候选锚文本。
    
11.  产品 / 集合页链接必须出现在商业意图、产品类别、购买决策或方案承接语境中。
    
12.  博客页链接必须能进一步解释、补充或承接当前内容。
    
13.  不强行将商业页面插入纯科普段落。
    
14.  不允许跨客户站点链接。
    

---

## 9. 数据库需求

### 9.1 数据库架构

```text
PostgreSQL：主业务库
Redis：缓存、任务状态、限流
Object Storage：原文快照、写回前后快照
pgvector：向量检索
PostgreSQL Full Text Search：关键词检索
Queue：异步任务
```
---

### 9.2 核心数据表

#### tenants

```sql
id
name
status
plan
created_at
updated_at
```

#### shops

```sql
id
tenant_id
platform
shop_domain
access_token_encrypted
api_version
sync_status
last_full_sync_at
last_incremental_sync_at
created_at
updated_at
```

#### pages

```sql
id
tenant_id
shop_id
page_type              -- blog / collection / product
shopify_gid
url
canonical_url
handle
title
meta_title
meta_description
h1
excerpt
status                 -- published / draft / archived
content_hash
last_synced_at
created_at
updated_at
```

#### page\_cards

```sql
id
tenant_id
page_id
cluster_id
keyword_id
page_type
card_text
structured_json
search_vector
embedding
version
created_at
updated_at
```

#### articles\_raw

```sql
id
tenant_id
page_id
source_format          -- html / markdown
raw_content_object_key
content_hash
shopify_updated_at
fetched_at
created_at
```

#### article\_blocks

```sql
id
tenant_id
page_id
block_index
block_type
heading_level
section_title
topic
content
content_hash
has_existing_link
link_count
is_first_paragraph
embedding
created_at
```

#### clusters

```sql
id
tenant_id
name
description
priority
created_at
updated_at
```

#### keywords

```sql
id
tenant_id
cluster_id
keyword
intent_type            -- informational / commercial / navigational / transactional
priority
created_at
updated_at
```

#### keyword\_page\_map

```sql
id
tenant_id
keyword_id
page_id
match_type             -- manual / imported / ai_suggested
confidence_score
approved_by
approved_at
created_at
```

#### anchor\_candidates

```sql
id
tenant_id
source_page_id
article_block_id
anchor_text
context_text
link_type_suggestion
start_offset
end_offset
model_name
prompt_version
confidence_score
status                 -- pending / accepted / rejected
created_at
```

#### link\_recommendations

```sql
id
tenant_id
anchor_candidate_id
target_page_id
rank
score_total
score_cluster
score_keyword
score_page_type
score_semantic
score_title
score_context
score_history
reason_json
status                 -- pending / selected / rejected
created_at
```

#### link\_decisions

```sql
id
tenant_id
anchor_candidate_id
selected_target_page_id
decision               -- approve / reject / replace / skip
reviewer_id
reviewer_note
decided_at
```

#### link\_insertions

```sql
id
tenant_id
source_page_id
target_page_id
anchor_text
target_url
before_snapshot_key
after_snapshot_key
shopify_write_status
shopify_response_json
inserted_by
inserted_at
```

#### preference\_docs

```sql
id
tenant_id
name
version
content_markdown
status                 -- draft / pending_review / active / archived / rejected
created_by
approved_by
created_at
activated_at
```

#### hard\_rules

```sql
id
tenant_id
rule_key
rule_name
rule_content
severity               -- error / warning / info
is_enabled
created_at
updated_at
```

#### jobs

```sql
id
tenant_id
job_type
status                 -- queued / running / success / failed / cancelled
priority
payload_json
result_json
error_message
retry_count
created_at
started_at
finished_at
```

#### audit\_logs

```sql
id
tenant_id
actor_id
action
entity_type
entity_id
before_json
after_json
created_at
```
---

## 10. 系统模块划分

### 10.1 前端模块

| 模块 | 功能 |
| --- | --- |
| 登录与权限 | 用户登录、角色权限 |
| 客户 / 店铺管理 | 管理 Shopify 客户站点 |
| 内容同步页 | 发起同步、查看同步状态 |
| 页面库 | 查看 blog / collection / product 卡片 |
| 集群关键词管理 | 管理 cluster / keyword / page mapping |
| 博客输入页 | 选择或粘贴博客内容 |
| 候选锚文本页 | 展示 AI 识别结果 |
| 链接审核页 | 展示 Top 3 卡片 |
| 插入预览页 | 查看插入后正文 |
| 写回记录页 | 查看写回状态和快照 |
| 互链任务页 | 处理旧博客链向新博客 |
| 偏好文档页 | 管理 Preference Doc |
| 规则配置页 | 管理 Hard Rules |
| 任务中心 | 查看后台任务 |
| 审计日志页 | 查看关键操作记录 |

---

### 10.2 后端服务模块

| 服务 | 职责 |
| --- | --- |
| Auth Service | 登录、权限、租户隔离 |
| Shopify Sync Service | 拉取 Shopify 内容 |
| Content Parser Service | HTML / Markdown 清洗与 AST 化 |
| Page Card Service | 结构化卡片生成 |
| Embedding Service | 生成向量 |
| Anchor Candidate Service | 候选锚文本生成 |
| Link Recommendation Service | 候选目标链接召回与排序 |
| Review Service | 人工审核结果保存 |
| Insertion Service | 链接插入与预览 |
| Shopify Write-back Service | 写回 Shopify |
| Snapshot Service | 写回前后快照 |
| Backlink Service | 旧博客互链任务 |
| Preference Service | 偏好文档管理与版本控制 |
| Rule Engine Service | 硬性规则校验 |
| Job Service | 异步任务调度 |
| Audit Service | 审计日志 |

---

## 11. API 需求

### 11.1 内容同步

**创建同步任务**

```http
POST /api/shops/{shop_id}/sync
```

Request:

```json
{
  "sync_type": "incremental",
  "page_types": ["blog", "collection", "product"]
}
```

Response:

```json
{
  "job_id": "job_123",
  "status": "queued"
}
```
---

### 11.2 获取页面卡片

```http
GET /api/pages?shop_id=xxx&page_type=blog&cluster_id=xxx&keyword_id=xxx
```

Response:

```json
{
  "items": [
    {
      "page_id": "page_123",
      "page_type": "blog",
      "title": "How to Choose a Glider Recliner",
      "url": "https://example.com/blogs/news/how-to-choose-a-glider-recliner",
      "meta_description": "A guide to choosing...",
      "cluster": "Nursery Furniture",
      "keyword": "glider recliner"
    }
  ]
}
```
---

### 11.3 生成候选锚文本

```http
POST /api/internal-linking/anchor-candidates
```

Request:

```json
{
  "source_page_id": "page_123",
  "preference_doc_id": "pref_001",
  "hard_rule_set_id": "rule_001"
}
```

Response:

```json
{
  "job_id": "job_456",
  "status": "queued"
}
```
---

### 11.4 获取候选锚文本

```http
GET /api/internal-linking/anchor-candidates?source_page_id=page_123
```

Response:

```json
{
  "items": [
    {
      "anchor_candidate_id": "ac_123",
      "anchor_text": "glider recliner",
      "context": "The right glider recliner can make your nursery...",
      "link_type_suggestion": "collection",
      "status": "pending"
    }
  ]
}
```
---

### 11.5 获取链接

```http
GET /api/internal-linking/anchor-candidates/{id}/recommendations
```

Response:

```json
{
  "items": [
    {
      "recommendation_id": "rec_123",
      "target_page_id": "page_456",
      "rank": 1,
      "url": "https://example.com/collections/glider-recliners",
      "title": "Glider Recliners",
      "page_type": "collection",
      "score_total": 91.5,
      "reason": "Anchor text matches product category and commercial context."
    }
  ]
}
```
---

### 11.6 提交人工审核

```http
POST /api/internal-linking/decisions
```

Request:

```json
{
  "source_page_id": "page_123",
  "decisions": [
    {
      "anchor_candidate_id": "ac_123",
      "decision": "approve",
      "selected_target_page_id": "page_456"
    }
  ]
}
```
---

### 11.7 生成插入预览

```http
POST /api/internal-linking/preview
```

Request:

```json
{
  "source_page_id": "page_123",
  "decision_ids": ["dec_001", "dec_002"]
}
```

Response:

```json
{
  "preview_html": "<p>The right <a href=\"...\">glider recliner</a>...</p>",
  "rule_check": {
    "passed": true,

    "warnings": [ ]

  }
}
```
---

### 11.8 写回 Shopify

```http
POST /api/internal-linking/write-back
```

Request:

```json
{
  "source_page_id": "page_123",
  "preview_id": "preview_001"
}
```

Response:

```json
{
  "job_id": "job_789",
  "status": "queued"
}
```
---

### 11.9 创建互链任务

```http
POST /api/internal-linking/backlinks
```

Request:

```json
{
  "new_blog_page_id": "page_123",
  "old_blog_page_ids": ["page_201", "page_202"]
}
```

Response:

```json
{
  "job_id": "job_900",
  "status": "queued"
}
```
---

## 12. 权限与安全

### 12.1 多租户隔离

1.  所有核心表必须包含 `tenant_id`。
    
2.  所有查询必须带 `tenant_id` 过滤。
    
3.  生产环境启用 PostgreSQL Row Level Security。
    
4.  禁止跨租户召回页面、候选链接、偏好文档。
    
5.  所有对象存储路径必须按租户隔离。
    

---

### 12.2 Shopify Token 安全

1.  Shopify access token 必须加密存储。
    
2.  后端日志不得打印 token。
    
3.  Token 访问必须走服务端。
    
4.  前端不得直接接触 token。
    
5.  Token 失效时应提示重新授权。
    

---

### 12.3 写回安全

1.  写回 Shopify 必须二次确认。
    
2.  写回前必须保存快照。
    
3.  写回失败不得覆盖本地状态为成功。
    
4.  同一篇文章并发写回必须加锁。
    
5.  支持回滚到任意历史快照。
    

---

## 13. 性能需求

| 场景 | 指标 |
| --- | --- |
| 单篇博客解析 | ≤ 5 秒 |
| 单篇候选锚文本生成 | ≤ 30 秒 |
| 单个锚文本候选链接 | ≤ 3 秒 |
| 页面卡片检索 | ≤ 1 秒 |
| 插入预览生成 | ≤ 3 秒 |
| Shopify 写回任务创建 | ≤ 1 秒 |
| Shopify 实际写回 | 受 API 限制，异步完成 |
| 任务状态查询 | ≤ 500ms |
| 页面库分页查询 | ≤ 1 秒 |

---

## 14. 并发与任务设计

### 14.1 异步任务类型

| 任务类型 | 是否异步 |
| --- | --- |
| Shopify 全量同步 | 是 |
| Shopify 增量同步 | 是 |
| 博客正文清洗 | 是 |
| Embedding 生成 | 是 |
| 候选锚文本生成 | 是 |
| 候选链接 | 可同步 / 可异步 |
| Shopify 写回 | 是 |
| 旧博客互链 | 是 |
| 偏好更新草稿生成 | 是 |

---

### 14.2 限流要求

1.  按 shop 维度限制 Shopify API 调用。
    
2.  按 tenant 维度限制并发任务数。
    
3.  按用户维度限制候选生成频率。
    
4.  按模型供应商限制 LLM 调用并发。
    
5.  支持任务排队、暂停、取消、重试。
    

---

## 15. 日志与审计

必须记录以下行为：

1.  用户登录。
    
2.  Shopify 授权。
    
3.  内容同步。
    
4.  候选锚文本生成。
    
5.  候选链接。
    
6.  人工审核操作。
    
7.  手动替换 URL。
    
8.  插入预览生成。
    
9.  Shopify 写回。
    
10.  回滚。
    
11.  偏好文档更新。
    
12.  硬性规则修改。
    
13.  权限变更。
    

每条日志至少包含：

```json
{
  "tenant_id": "tenant_001",
  "actor_id": "user_001",
  "action": "approve_link",
  "entity_type": "anchor_candidate",
  "entity_id": "ac_123",
  "before": {},
  "after": {},
  "created_at": "2026-07-01T10:00:00Z"
}

```
---

## 16. 测试需求

### 16.1 单元测试

覆盖：

1.  HTML 解析。
    
2.  Markdown 解析。
    
3.  已有链接识别。
    
4.  首段识别。
    
5.  H 标签过滤。
    
6.  锚文本 offset 定位。
    
7.  URL canonical 规范化。
    
8.  硬性规则校验。
    
9.  分数计算。
    
10.  插入 HTML anchor。
    
11.  插入 Markdown link。
    
12.  快照保存。
    
13.  回滚逻辑。
    

---

### 16.2 集成测试

覆盖：

1.  Shopify 同步 → 入库。
    
2.  入库 → 卡片生成。
    
3.  博客解析 → 候选锚文本。
    
4.  候选锚文本 → 链接。
    
5.  人工审核 → 插入预览。
    
6.  插入预览 → Shopify 写回。
    
7.  写回失败 → 重试。
    
8.  写回成功 → 快照校验。
    
9.  新博客 → 旧博客互链。
    
10.  偏好更新草稿 → 人工审核 → 新版本生效。
    

---

### 16.3 验收测试

#### 用例 1：新博客添加内链

Given：用户选择一篇未处理的新博客 When：点击生成候选锚文本 Then：系统返回候选锚文本、上下文、页面类型和 Top 3 链接。

#### 用例 2：过滤已有链接

Given：博客中已有 `<a>` 标签 When：系统生成候选锚文本 Then：已有链接文本不得出现在候选锚文本列表中。

#### 用例 3：人工选择链接

Given：系统返回 3 个候选链接 When：用户选择第 1 个链接 Then：系统保存人工选择记录，并用于生成插入预览。

#### 用例 4：写回 Shopify

Given：用户确认插入预览 When：点击写回 Then：系统保存 before snapshot，写回 Shopify，保存 after snapshot，并重新读取校验。

#### 用例 5：回滚

Given：某次写回存在错误 When：用户选择回滚 Then：系统将正文恢复到 before snapshot，并记录 rollback 日志。

#### 用例 6：旧博客互链

Given：新博客已完成内链写回 When：用户进入互链环节并选择旧博客 Then：系统为旧博客生成反向链接候选，并允许人工审核后写回。

---

## 17. 风险与解决方案

| 风险 | 说明 | 解决方案 |
| --- | --- | --- |
| AI 不稳定 | 不同模型输出不同 | 规则后处理 + JSON Schema 校验 + 人工审核 |
| 锚文本定位失败 | 原文重复出现相同短语 | 保存 block\_id + start\_offset + end\_offset |
| Shopify 写回覆盖人工修改 | 同步后内容已变化 | 写回前比对 content\_hash |
| API 限流 | 大量客户同步 | 队列 + shop 维度限流 |
| 跨客户数据泄露 | 多租户系统风险 | tenant\_id + RLS + 对象存储隔离 |
| 偏好污染 | 单篇文章经验变长期规则 | 偏好更新必须人工审核 |
| 链接过度优化 | 过多完全匹配锚文本 | 硬性规则 + 多样性检查 |
| HTML 结构损坏 | 插入链接破坏标签 | AST 插入 + 写回后重新解析校验 |
| 重复内链 | 同目标多次出现 | 插入前检查 source\_page\_id + target\_page\_id |
| 内部竞争 | 相似博客互链错误 | 集群内相似主题惩罚机制 |

---

## 18. 上线验收标准

### 功能验收

1.  能成功同步 Shopify blog / collection / product。
    
2.  能生成页面结构化卡片。
    
3.  能解析 HTML / Markdown 博客。
    
4.  能识别候选锚文本。
    
5.  能为每个候选锚文本 Top 3 链接。
    
6.  能人工审核结果。
    
7.  能生成插入预览。
    
8.  能写回 Shopify。
    
9.  能保存写回前后快照。
    
10.  能执行回滚。
    
11.  能触发旧博客互链流程。
    
12.  能管理 Preference Doc。
    
13.  能查看任务日志和审计日志。
    

### 质量验收

1.  候选锚文本不得包含已链接文本。
    
2.  候选锚文本不得出现在 H 标签中。
    
3.  首段不得锚文本。
    
4.  链接必须属于同一 tenant。
    
5.  链接必须是 published 页面。
    
6.  写回前必须保存快照。
    
7.  写回后必须重新校验。
    
8.  人工拒绝记录必须被保存。
    
9.  所有 AI 输出必须通过 JSON Schema 校验。
    
10.  所有任务失败必须可追踪。
    

### 性能验收

1.  页面卡片检索 P95 ≤ 1 秒。
    
2.  单篇博客解析 P95 ≤ 5 秒。
    
3.  单个锚文本 P95 ≤ 3 秒。
    
4.  任务状态查询 P95 ≤ 500ms。
    
5.  100 个并发任务不应导致数据库连接耗尽。
    
6.  Shopify API 限流时任务应排队，不应失败雪崩。