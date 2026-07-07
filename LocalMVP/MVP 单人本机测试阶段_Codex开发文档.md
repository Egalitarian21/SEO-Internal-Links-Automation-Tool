# MVP 单人本机测试阶段\_Codex开发文档

```text
本机浏览器前端
→ FastAPI 后端
→ PostgreSQL 数据库
→ 本地导入页面数据
→ 选择一篇博客
→ 解析正文
→ 生成候选锚文本
→ 生成候选链接 Top 3
→ 人工审核
→ 插入预览
→ 保存本地写回快照
→ 支持本地回
```

MVP 阶段不追求生产级多用户、多客户、多任务并发，也不接入真实 Shopify 写回。目标是先验证核心业务流程、数据结构、规则校验和审核体验。

---

## 1. MVP 阶段必须遵守的核心原则

1.  AI 或规则只负责推荐，不负责最终决策。
    
2.  所有候选锚文本必须经过硬性规则二次过滤。
    
3.  所有候选链接必须展示分数、原因和目标页面信息。
    
4.  所有插入操作必须先生成预览，不能直接覆盖原文。
    
5.  本地写回前后必须保存快照。
    
6.  人工审核结果必须入库，不能只停留在前端状态。
    
7.  MVP 以单人本机验证为目标，不提前开发生产化能力。
    

---

## 2. 技术栈

### 2.1 前端

使用：

```text
Vite
React
TypeScript
普通 CSS 或 CSS Modules
```

前端运行地址：

```text
http://localhost:5173
```

### 2.2 后端

使用：

```text
Python 3.11+
FastAPI
SQLAlchemy 2.x
Pydantic v2
Alembic
psycopg
BeautifulSoup4
markdown-it-py 或 markdown
pytest
```

后端运行地址：

```text
http://localhost:8000
```

API 文档地址：

```text
http://localhost:8000/docs
```

### 2.3 数据库

使用：

```text
PostgreSQL 16
Docker Compose 管理 PostgreSQL
```

MVP 不使用：

```text
Redis
Celery
pgvector
对象存储
PostgreSQL RLS
真实 Shopify API
登录权限系统
```
---

## 3. MVP 明确不做的内容

Codex 不得在 MVP 阶段实现以下内容：

1.  不做真实 Shopify 授权。
    
2.  不做真实 Shopify GraphQL API 同步。
    
3.  不做真实 Shopify 写回。
    
4.  不做 Redis。
    
5.  不做 Celery / RQ / Kafka 等队列。
    
6.  不做多用户登录。
    
7.  不做角色权限。
    
8.  不做多租户管理界面。
    
9.  不做 pgvector 向量检索。
    
10.  不做 Preference Doc 自动更新。
    
11.  不做旧博客自动互链完整流程。
    
12.  不做生产环境部署。
    
13.  不做复杂 UI 设计系统。
    
14.  不做自动发布、自动删除已有内链、自动批量写回。
    

MVP 中的“写回”只表示：

```text
把插入预览后的 HTML 保存到本地数据库，并记录 before / after 快照。
```
---

## 4. MVP 用户路径

MVP 前端必须支持以下路径：

```text
1. 用户打开 http://localhost:5173
2. 用户导入或手动创建页面数据
3. 用户进入页面库
4. 用户选择一篇 blog 页面作为 source page
5. 用户点击“解析正文”
6. 系统生成 article_blocks
7. 用户点击“生成候选锚文本”
8. 系统返回候选锚文本列表
9. 用户点击“生成候选链接”
10. 系统为每个候选锚文本返回 Top 3 推荐链接
11. 用户逐条 approve / reject / replace / skip
12. 用户点击“生成插入预览”
13. 系统展示 preview_html 和规则检查结果
14. 用户点击“保存本地写回”
15. 系统保存 before_snapshot 和 after_snapshot
16. 用户可在写回记录中执行 rollback
```
---

## 5. 项目目录结构

Codex 必须按以下结构创建项目：

```text
internal-link-mvp/
  README.md
  docker-compose.yml
  .env.example

  backend/
    pyproject.toml
    alembic.ini
    app/
      main.py
      core/
        config.py
      db/
        session.py
        base.py
        models.py
      schemas/
        page.py
        article.py
        anchor.py
        recommendation.py
        decision.py
        preview.py
        snapshot.py
      api/
        routes_health.py
        routes_pages.py
        routes_articles.py
        routes_internal_linking.py
        routes_snapshots.py
      services/
        canonical.py
        parser.py
        anchor_generator.py
        rule_engine.py
        recommender.py
        insertion.py
        snapshot.py
        seed.py
      tests/
        test_canonical.py
        test_parser.py
        test_rule_engine.py
        test_recommender.py
        test_insertion.py

    alembic/
      versions/

  frontend/
    package.json
    vite.config.ts
    index.html
    src/
      main.tsx
      App.tsx
      api.ts
      types.ts
      styles.css
      pages/
        Dashboard.tsx
        ImportPages.tsx
        PageLibrary.tsx
        BlogWorkspace.tsx
        ReviewPage.tsx
        PreviewPage.tsx
        SnapshotPage.tsx
      components/
        PageCard.tsx
        AnchorCandidateCard.tsx
        RecommendationCard.tsx
        DecisionPanel.tsx
        RuleCheckPanel.tsx

  sample_data/
    pages_sample.csv
    source_blog_sample.html
```
---

## 6. Docker Compose 要求

`docker-compose.yml` 只需要管理 PostgreSQL。

```yaml
services:
  postgres:
    image: postgres:16
    container_name: internal_link_mvp_postgres
    environment:
      POSTGRES_USER: internal_link
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-CHANGE_ME_LOCAL_PASSWORD}
      POSTGRES_DB: internal_link_mvp
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

`.env.example`：

```env
DATABASE_URL=postgresql+psycopg://internal_link:CHANGE_ME_LOCAL_PASSWORD@localhost:5432/internal_link_mvp
POSTGRES_PASSWORD=CHANGE_ME_LOCAL_PASSWORD
APP_ENV=local
DEFAULT_TENANT_ID=00000000-0000-0000-0000-000000000001
ENABLE_LLM=false
LLM_API_KEY=
```
---

## 7. 数据模型

MVP 保留 `tenant_id` 字段，但不实现租户管理。所有数据默认写入：

```text
tenant_id = 00000000-0000-0000-0000-000000000001
```

### 7.1 pages

用途：保存 blog / collection / product 页面基础信息。

字段：

```sql
id UUID PRIMARY KEY
tenant_id UUID NOT NULL
page_type TEXT NOT NULL          -- blog / collection / product
url TEXT NOT NULL
canonical_url TEXT NOT NULL
handle TEXT
title TEXT NOT NULL
meta_title TEXT
meta_description TEXT
h1 TEXT
excerpt TEXT
status TEXT NOT NULL DEFAULT 'published'  -- published / draft / archived
cluster_name TEXT
keyword TEXT
raw_html TEXT                    -- blog 页面可存正文 HTML；collection/product 可为空
content_hash TEXT
created_at TIMESTAMP
updated_at TIMESTAMP
```

约束：

```text
page_type 只能是 blog / collection / product
status 只能是 published / draft / archived
canonical_url 在同一 tenant_id 下唯一
```
---

### 7.2 article\_blocks

用途：保存博客正文解析后的结构化块。

字段：

```sql
id UUID PRIMARY KEY
tenant_id UUID NOT NULL
page_id UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE
block_index INTEGER NOT NULL
block_type TEXT NOT NULL         -- paragraph / heading / list_item / other
heading_level TEXT               -- h1 / h2 / h3 / h4 / h5 / h6 / null
section_title TEXT
content TEXT NOT NULL
raw_html TEXT
has_existing_link BOOLEAN NOT NULL DEFAULT FALSE
link_count INTEGER NOT NULL DEFAULT 0
is_first_paragraph BOOLEAN NOT NULL DEFAULT FALSE
created_at TIMESTAMP
```
---

### 7.3 anchor\_candidates

用途：保存候选锚文本。

字段：

```sql
id UUID PRIMARY KEY
tenant_id UUID NOT NULL
source_page_id UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE
article_block_id UUID NOT NULL REFERENCES article_blocks(id) ON DELETE CASCADE
anchor_text TEXT NOT NULL
context_text TEXT NOT NULL
link_type_suggestion TEXT NOT NULL  -- blog / collection / product
start_offset INTEGER NOT NULL
end_offset INTEGER NOT NULL
reason TEXT
confidence_score NUMERIC(5,2) NOT NULL DEFAULT 0
status TEXT NOT NULL DEFAULT 'pending'  -- pending / accepted / rejected / skipped
created_at TIMESTAMP
```

约束：

```text
end_offset 必须大于 start_offset
同一个 article_block_id + anchor_text + start_offset 不得重复
```
---

### 7.4 link\_recommendations

用途：保存每个候选锚文本的目标链接推荐。

字段：

```sql
id UUID PRIMARY KEY
tenant_id UUID NOT NULL
anchor_candidate_id UUID NOT NULL REFERENCES anchor_candidates(id) ON DELETE CASCADE
target_page_id UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE
rank INTEGER NOT NULL
score_total NUMERIC(5,2) NOT NULL
score_cluster NUMERIC(5,2) NOT NULL
score_keyword NUMERIC(5,2) NOT NULL
score_page_type NUMERIC(5,2) NOT NULL
score_semantic NUMERIC(5,2) NOT NULL
score_title NUMERIC(5,2) NOT NULL
score_history NUMERIC(5,2) NOT NULL
score_quality NUMERIC(5,2) NOT NULL
penalty_duplicate NUMERIC(5,2) NOT NULL
penalty_competition NUMERIC(5,2) NOT NULL
penalty_over_optimization NUMERIC(5,2) NOT NULL
penalty_distance NUMERIC(5,2) NOT NULL
reason_json JSONB NOT NULL
status TEXT NOT NULL DEFAULT 'pending'  -- pending / selected / rejected
created_at TIMESTAMP
```
---

### 7.5 link\_decisions

用途：保存人工审核结果。

字段：

```sql
id UUID PRIMARY KEY
tenant_id UUID NOT NULL
source_page_id UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE
anchor_candidate_id UUID NOT NULL REFERENCES anchor_candidates(id) ON DELETE CASCADE
selected_target_page_id UUID REFERENCES pages(id)
manual_target_url TEXT
decision TEXT NOT NULL        -- approve / reject_anchor / reject_target / replace_target / skip
reviewer_note TEXT
created_at TIMESTAMP
```

规则：

```text
approve 必须有 selected_target_page_id
replace_target 必须有 manual_target_url
reject_anchor / reject_target / skip 可以没有 target
```
---

### 7.6 insertion\_previews

用途：保存插入预览。

字段：

```sql
id UUID PRIMARY KEY
tenant_id UUID NOT NULL
source_page_id UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE
before_html TEXT NOT NULL
preview_html TEXT NOT NULL
rule_check_json JSONB NOT NULL
created_at TIMESTAMP
```
---

### 7.7 snapshots

用途：保存本地写回和回滚快照。

字段：

```sql
id UUID PRIMARY KEY
tenant_id UUID NOT NULL
source_page_id UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE
snapshot_type TEXT NOT NULL     -- local_write / rollback
before_html TEXT NOT NULL
after_html TEXT NOT NULL
preview_id UUID REFERENCES insertion_previews(id)
created_at TIMESTAMP
```
---

### 7.8 audit\_logs

用途：记录关键操作。

字段：

```sql
id UUID PRIMARY KEY
tenant_id UUID NOT NULL
action TEXT NOT NULL
entity_type TEXT NOT NULL
entity_id UUID
before_json JSONB
after_json JSONB
created_at TIMESTAMP
```
---

## 8. 后端 API

所有 API 返回 JSON。

### 8.1 健康检查

```http
GET /api/health
```

Response:

```json
{
  "status": "ok"
}
```
---

### 8.2 导入页面数据

```http
POST /api/pages/import
```

支持 JSON 导入即可；CSV 导入可作为增强，但 MVP 必须至少支持 JSON。

Request:

```json
{
  "items": [
    {
      "page_type": "blog",
      "url": "https://example.com/blogs/news/how-to-choose-a-glider-recliner",
      "title": "How to Choose a Glider Recliner",
      "meta_description": "A guide to choosing a glider recliner.",
      "h1": "How to Choose a Glider Recliner",
      "excerpt": "A practical buying guide.",
      "status": "published",
      "cluster_name": "Nursery Furniture",
      "keyword": "glider recliner",
      "raw_html": "<h1>How to Choose...</h1><p>...</p>"
    }
  ]
}
```

Response:

```json
{
  "created": 1,
  "updated": 0,
  "skipped": 0
}
```

要求：

```text
导入时必须自动生成 canonical_url。
导入时必须计算 content_hash。
同一 canonical_url 重复导入时更新原记录。
```
---

### 8.3 获取页面列表

```http
GET /api/pages?page_type=blog&status=published&query=glider
```

Response:

```json
{
  "items": [
    {
      "id": "uuid",
      "page_type": "blog",
      "url": "https://example.com/blogs/news/how-to-choose-a-glider-recliner",
      "canonical_url": "https://example.com/blogs/news/how-to-choose-a-glider-recliner",
      "title": "How to Choose a Glider Recliner",
      "meta_description": "A guide to choosing a glider recliner.",
      "h1": "How to Choose a Glider Recliner",
      "excerpt": "A practical buying guide.",
      "status": "published",
      "cluster_name": "Nursery Furniture",
      "keyword": "glider recliner"
    }
  ]
}
```
---

### 8.4 获取单个页面

```http
GET /api/pages/{page_id}
```
---

### 8.5 创建或更新单个页面

```http
POST /api/pages
```

Request 与导入单条 item 相同。

---

### 8.6 解析博客正文

```http
POST /api/articles/{page_id}/parse
```

要求：

```text
page_id 必须是 page_type=blog。
raw_html 不能为空。
重新解析时先删除该 page_id 旧 article_blocks。
```

Response:

```json
{
  "page_id": "uuid",
  "block_count": 8,
  "blocks": [
    {
      "id": "uuid",
      "block_index": 1,
      "block_type": "paragraph",
      "heading_level": null,
      "section_title": "Choosing the Right Chair",
      "content": "The right glider recliner can make your nursery more comfortable...",
      "has_existing_link": false,
      "link_count": 0,
      "is_first_paragraph": false
    }
  ]
}
```
---

### 8.7 获取正文块

```http
GET /api/articles/{page_id}/blocks
```
---

### 8.8 生成候选锚文本

```http
POST /api/internal-linking/{source_page_id}/anchor-candidates/generate
```

Response:

```json
{
  "source_page_id": "uuid",
  "created": 6,
  "items": [
    {
      "id": "uuid",
      "anchor_text": "glider recliner",
      "context_text": "The right glider recliner can make your nursery more comfortable...",
      "link_type_suggestion": "collection",
      "start_offset": 10,
      "end_offset": 25,
      "reason": "Matches known keyword or page title phrase.",
      "confidence_score": 82
    }
  ]
}
```

MVP 生成逻辑必须先实现规则版，不强依赖 LLM：

```text
1. 读取 source_page_id 的 article_blocks。
2. 跳过 heading block。
3. 跳过 is_first_paragraph=true 的 block。
4. 跳过 has_existing_link=true 的 block。
5. 从 pages 表中读取所有 published 的 collection/product/blog 目标页。
6. 使用目标页 keyword、title、h1 中的 2-6 词短语作为候选匹配词。
7. 在正文块 content 中查找这些短语。
8. 同一正文块最多保留 2 个候选。
9. 同一 anchor_text 在同一文章中最多保留 1 个候选。
10. 每个候选必须有 block_id、start_offset、end_offset。
11. 生成后必须调用 Rule Engine 二次过滤。
```

LLM 作为可选增强：

```text
只有 ENABLE_LLM=true 时才调用 LLM。
即使调用 LLM，也必须经过相同 Rule Engine。
LLM 输出不合格时不得报错中断，应回退到规则版候选。
```
---

### 8.9 获取候选锚文本

```http
GET /api/internal-linking/{source_page_id}/anchor-candidates
```
---

### 8.10 生成候选链接推荐

```http
POST /api/internal-linking/{source_page_id}/recommendations/generate
```

要求：

```text
为该 source_page_id 下所有 pending anchor_candidates 生成推荐。
每个 anchor_candidate 最多保存 rank 1-3。
重新生成时删除该 anchor_candidate 下旧 recommendations。
```

Response:

```json
{
  "source_page_id": "uuid",
  "created": 12
}
```
---

### 8.11 获取候选链接推荐

```http
GET /api/internal-linking/{source_page_id}/recommendations
```

Response:

```json
{
  "items": [
    {
      "anchor_candidate_id": "uuid",
      "anchor_text": "glider recliner",
      "recommendations": [
        {
          "id": "uuid",
          "target_page_id": "uuid",
          "rank": 1,
          "url": "https://example.com/collections/glider-recliners",
          "title": "Glider Recliners",
          "page_type": "collection",
          "meta_description": "Shop comfortable glider recliners.",
          "score_total": 91.5,
          "score_cluster": 20,
          "score_keyword": 20,
          "score_page_type": 15,
          "score_semantic": 22,
          "score_title": 7,
          "score_history": 2.5,
          "score_quality": 5,
          "reason_json": {
            "summary": "Anchor matches target keyword and collection page type.",
            "matched_fields": ["keyword", "title", "cluster_name"]
          }
        }
      ]
    }
  ]
}
```
---

### 8.12 提交人工审核

```http
POST /api/internal-linking/{source_page_id}/decisions
```

Request:

```json
{
  "decisions": [
    {
      "anchor_candidate_id": "uuid",
      "decision": "approve",
      "selected_target_page_id": "uuid",
      "reviewer_note": ""
    },
    {
      "anchor_candidate_id": "uuid",
      "decision": "replace_target",
      "manual_target_url": "https://example.com/custom-url",
      "reviewer_note": "Manual replacement."
    },
    {
      "anchor_candidate_id": "uuid",
      "decision": "reject_anchor",
      "reviewer_note": "Too generic."
    }
  ]
}
```

Response:

```json
{
  "created": 3
}
```

要求：

```text
保存新 decisions 前，可以删除该 source_page_id 的旧 decisions，避免重复。
approve 后将对应 anchor_candidate.status 更新为 accepted。
reject_anchor 后将 anchor_candidate.status 更新为 rejected。
skip 后将 anchor_candidate.status 更新为 skipped。
```
---

### 8.13 生成插入预览

```http
POST /api/internal-linking/{source_page_id}/preview
```

Response:

```json
{
  "preview_id": "uuid",
  "preview_html": "<p>The right <a href=\"https://example.com/...\">glider recliner</a> can...</p>",
  "rule_check": {
    "passed": true,
    "errors": [],
    "warnings": []
  }
}
```

要求：

```text
只处理 decision=approve 或 replace_target。
reject_anchor / reject_target / skip 不插入。
每个 anchor_candidate 只插入指定 block_id + offset 位置。
如果 offset 已失效，返回 rule_check.errors，不得强行插入。
如果同一 target_url 已在 source_page raw_html 中存在，返回 warning，并跳过该插入。
```
---

### 8.14 保存本地写回

```http
POST /api/internal-linking/{source_page_id}/local-write
```

Request:

```json
{
  "preview_id": "uuid"
}
```

Response:

```json
{
  "snapshot_id": "uuid",
  "status": "saved"
}
```

要求：

```text
保存前：
1. before_html = pages.raw_html 当前值
2. after_html = insertion_previews.preview_html

保存后：
1. 更新 pages.raw_html = after_html
2. 更新 pages.content_hash
3. snapshots 新增 snapshot_type=local_write
4. audit_logs 记录 local_write
```
---

### 8.15 获取快照列表

```http
GET /api/snapshots?source_page_id=uuid
```
---

### 8.16 回滚

```http
POST /api/snapshots/{snapshot_id}/rollback
```

Response:

```json
{
  "snapshot_id": "uuid",
  "rollback_snapshot_id": "uuid",
  "status": "rolled_back"
}
```

要求：

```text
将 pages.raw_html 恢复为目标 snapshot.before_html。
新增一条 snapshot_type=rollback 的快照。
audit_logs 记录 rollback。
```
---

## 9. URL Canonical 规则

实现 `services/canonical.py`。

### 9.1 基础规则

```text
1. 去掉 URL hash。
2. 去掉常见追踪参数：utm_source, utm_medium, utm_campaign, utm_term, utm_content, fbclid, gclid。
3. 去掉末尾 slash，但保留根路径。
4. host 转小写。
5. scheme 默认保留原值；如缺失，补 https。
```

### 9.2 Shopify 产品 URL 规则

如果 URL 路径符合：

```text
/collections/{collection_handle}/products/{product_handle}
```

必须转换为：

```text
/products/{product_handle}
```

保留原域名。

---

## 10. 正文解析规则

实现 `services/parser.py`。

### 10.1 输入

```text
pages.raw_html
```

### 10.2 输出

```text
article_blocks
```

### 10.3 解析要求

```text
1. 使用 BeautifulSoup 解析 HTML。
2. 识别 h1-h6 为 heading block。
3. 识别 p 为 paragraph block。
4. 识别 li 为 list_item block。
5. 跳过 script、style、nav、footer、aside。
6. 跳过 table。
7. 跳过 img-only block。
8. 第一个 paragraph block 标记 is_first_paragraph=true。
9. block 的 section_title 使用最近一个 h2/h3 文本。
10. has_existing_link=true：该 block 内存在 a 标签。
11. link_count：该 block 内 a 标签数量。
12. raw_html 保存该 block 原始 HTML。
13. content 保存纯文本。
```

### 10.4 Markdown

MVP 支持 Markdown 原始输入，转 HTML，再走同一 HTML Parser。

---

## 11. 锚文本硬性规则

实现 `services/rule_engine.py`。

候选锚文本必须满足：

```text
1. anchor_text 非空。
2. anchor_text 必须来自 article_block.content。
3. anchor_text 不得位于 heading block。
4. anchor_text 不得位于 is_first_paragraph=true 的 block。
5. anchor_text 不得位于 has_existing_link=true 的 block。
6. anchor_text 英文词数必须 >= 2。
7. anchor_text 英文词数必须 <= 12。
8. anchor_text 不能是 click here / read more / learn more / this / here。
9. 同一 article_block 最多保留 2 个候选。
10. 同一 source_page_id 下，同一 anchor_text 最多保留 1 个候选。
11. start_offset / end_offset 必须能精确截取出 anchor_text。
```

泛锚文本黑名单：

```python
["click here", "read more", "learn more", "this", "here", "more", "link"]
```
---

## 12. 候选链接推荐算法

实现 `services/recommender.py`。

### 12.1 候选池过滤

对每个 anchor\_candidate：

```text
1. 从 pages 表读取所有 status=published 的目标页。
2. 排除 source_page_id 自己。
3. 排除 canonical_url 为空的页面。
4. 排除 raw_html 或 source_page 已经链接过的 target canonical_url。
5. MVP 允许 blog / collection / product 都参与推荐。
```

### 12.2 link\_type\_suggestion 规则

```text
如果 anchor_text 或 context_text 命中商业词：
  link_type_suggestion = collection
商业词包括：buy, choose, best, review, product, products, collection, shop, price, type, option

如果 anchor_text 命中产品名或具体型号：
  link_type_suggestion = product

否则：
  link_type_suggestion = blog
```

### 12.3 评分公式

```text
score_total =
  score_cluster
+ score_keyword
+ score_page_type
+ score_semantic
+ score_title
+ score_history
+ score_quality
- penalty_duplicate
- penalty_competition
- penalty_over_optimization
- penalty_distance

score_total = min(max(score_total, 0), 100)
```

### 12.4 具体分数

#### score\_cluster，满分 20

```text
目标页 cluster_name 与 source_page cluster_name 完全一致：20
目标页 cluster_name 与 source_page cluster_name 都非空但不一致：12
目标页 cluster_name 为空：0
```

#### score\_keyword，满分 20

```text
anchor_text 与 target.keyword 完全一致：20
anchor_text 包含 target.keyword 或 target.keyword 包含 anchor_text：15
anchor_text 与 target.title / target.h1 有明显短语重叠：12
无匹配：0
```

#### score\_page\_type，满分 15

```text
target.page_type == link_type_suggestion：15
link_type_suggestion=collection 且 target.page_type=product：10
link_type_suggestion=product 且 target.page_type=collection：8
link_type_suggestion=blog 且 target.page_type in collection/product：5
其他：0
```

#### score\_semantic，满分 25

MVP 不使用向量。使用 token Jaccard 相似度：

```text
source_text = anchor_text + " " + context_text
target_text = target.title + " " + target.h1 + " " + target.meta_description + " " + target.excerpt + " " + target.keyword

similarity = len(source_tokens ∩ target_tokens) / len(source_tokens ∪ target_tokens)
score_semantic = similarity * 25
```

要求：

```text
统一小写。
移除常见英文停用词。
只保留 a-z0-9 token。
```

#### score\_title，满分 10

```text
anchor_tokens 与 target.title + target.h1 tokens 的 overlap_ratio * 10
```

#### score\_history，满分 5

MVP 冷启动固定：

```text
2.5
```

#### score\_quality，满分 5

```text
status=published：1
canonical_url 非空：1
title 非空：1
meta_description 非空：1
h1 非空：1
```
---

### 12.5 惩罚项

#### penalty\_duplicate，最高 50

```text
如果 source_page.raw_html 已包含 target.canonical_url：50
否则：0
```

#### penalty\_competition，最高 20

```text
如果 target.page_type=blog 且 target.keyword 与 source_page.keyword 完全一致：20
否则：0
```

#### penalty\_over\_optimization，最高 10

MVP 固定：

```text
0
```

#### penalty\_distance，最高 15

```text
如果 score_semantic < 3：15
如果 score_semantic >= 3 且 < 6：8
否则：0
```
---

### 12.6 排序规则

```text
1. 按 score_total 降序。
2. 如果分差 < 3，优先 page_type 等于 link_type_suggestion。
3. 如果仍相同，优先 score_semantic 更高。
4. 如果仍相同，优先 score_keyword 更高。
5. 每个 anchor_candidate 最终保存 Top 3。
```
---

## 13. 插入预览规则

实现 `services/insertion.py`。

### 13.1 插入目标

只插入已审核通过的决策：

```text
decision=approve
decision=replace_target
```

### 13.2 approve 的 target\_url

```text
使用 selected_target_page_id 对应 pages.canonical_url
```

### 13.3 replace\_target 的 target\_url

```text
使用 manual_target_url
```

### 13.4 插入格式

HTML：

```html
<a href="TARGET_URL">ANCHOR_TEXT</a>
```

### 13.5 定位规则

```text
1. 根据 anchor_candidate.article_block_id 找到 block。
2. 根据 block.raw_html 找到原 HTML block。
3. 使用 start_offset / end_offset 验证 block.content 截取结果等于 anchor_text。
4. 如果验证失败，不插入，记录 error。
5. 如果验证成功，只替换该 block 中第一次精确匹配 anchor_text 的纯文本位置。
6. 不修改句子文字。
7. 不插入到已有 a 标签内部。
8. 不插入到 heading 内。
```

MVP 允许限制：

```text
如果 anchor_text 跨多个 HTML text node，返回 error，不强行插入。
```
---

## 14. 前端页面要求

### 14.1 Dashboard

路径：

```text
/
```

展示：

```text
页面总数
Blog 数量
Collection 数量
Product 数量
最近 5 条快照
入口按钮：导入页面 / 页面库
```
---

### 14.2 ImportPages

路径：

```text
/import
```

功能：

```text
1. 文本框粘贴 JSON。
2. 点击 Import。
3. 调用 POST /api/pages/import。
4. 展示 created / updated / skipped。
```

必须提供示例 JSON 按钮，一键填入 sample。

---

### 14.3 PageLibrary

路径：

```text
/pages
```

功能：

```text
1. 表格展示 pages。
2. 支持 page_type 筛选。
3. 支持 query 搜索。
4. 每条 blog 页面有按钮：进入工作台。
5. collection/product 只展示，不进入工作台。
```
---

### 14.4 BlogWorkspace

路径：

```text
/workspace/:pageId
```

展示：

```text
页面标题
URL
Meta Description
H1
Cluster
Keyword
raw_html 预览
按钮：解析正文
按钮：生成候选锚文本
按钮：生成候选链接
按钮：进入审核页
```

下方展示：

```text
article_blocks 列表
anchor_candidates 列表
```
---

### 14.5 ReviewPage

路径：

```text
/review/:pageId
```

展示：

```text
每个 anchor_candidate 一张卡片
卡片内展示：
- anchor_text
- context_text
- link_type_suggestion
- reason
- Top 3 recommendations
```

每个 recommendation 展示：

```text
Title
URL
Page Type
Meta Description
score_total
score_cluster
score_keyword
score_page_type
score_semantic
score_title
score_quality
reason_json.summary
```

操作：

```text
approve：选择某个 recommendation
reject_anchor
reject_target
replace_target：手动输入 URL
skip
保存审核结果
进入预览页
```
---

### 14.6 PreviewPage

路径：

```text
/preview/:pageId
```

功能：

```text
1. 点击生成预览。
2. 展示 rule_check errors / warnings。
3. 展示 preview_html 渲染效果。
4. 展示 preview_html 源码。
5. passed=true 时允许点击保存本地写回。
6. 保存后展示 snapshot_id。
```
---

### 14.7 SnapshotPage

路径：

```text
/snapshots/:pageId
```

功能：

```text
1. 展示该 page 的所有 snapshots。
2. 展示 snapshot_type 和 created_at。
3. 可查看 before_html / after_html。
4. 可点击 rollback。
5. rollback 后刷新当前页面 raw_html。
```
---

## 15. 测试要求

Codex 必须实现并通过以下测试。

### 15.1 单元测试

```text
test_canonical.py
- 去除 utm 参数
- 去除 hash
- Shopify collection product URL 转 canonical product URL

test_parser.py
- h1/h2 被识别为 heading
- 第一个 paragraph 被标记为 is_first_paragraph
- 含 a 标签的段落 has_existing_link=true
- table 被跳过

test_rule_engine.py
- 首段候选被过滤
- heading 候选被过滤
- click here 被过滤
- 单词候选被过滤
- offset 不匹配被过滤

test_recommender.py
- 完全 keyword 匹配得高分
- 已链接 target 触发 penalty_duplicate
- 每个 anchor 只返回 Top 3
- score_total 被限制在 0-100

test_insertion.py
- approve decision 成功插入 a 标签
- reject_anchor 不插入
- offset 失效时报 error
- 已有 target URL 时跳过重复插入
```

### 15.2 API 冒烟测试

至少验证：

```text
GET /api/health
POST /api/pages/import
GET /api/pages
POST /api/articles/{page_id}/parse
POST /api/internal-linking/{source_page_id}/anchor-candidates/generate
POST /api/internal-linking/{source_page_id}/recommendations/generate
POST /api/internal-linking/{source_page_id}/decisions
POST /api/internal-linking/{source_page_id}/preview
POST /api/internal-linking/{source_page_id}/local-write
POST /api/snapshots/{snapshot_id}/rollback
```
---

## 16. README 必须包含的启动命令

README 必须写清楚以下命令。

### 16.1 启动 PostgreSQL

```bash
docker compose up -d
```

### 16.2 启动后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Windows 可补充：

```bash
.venv\Scripts\activate
```

### 16.3 启动前端

```bash
cd frontend
npm install
npm run dev
```

### 16.4 运行测试

```bash
cd backend
pytest
```
---

## 17. MVP 验收标准

### 17.1 功能验收

必须做到：

```text
1. 能在本机打开前端页面。
2. 能连接 Docker Compose PostgreSQL。
3. 能导入 blog / collection / product 页面数据。
4. 能展示页面库。
5. 能选择一篇 blog 进入工作台。
6. 能解析 HTML 正文为 article_blocks。
7. 能生成候选锚文本。
8. 候选锚文本不包含首段、标题、已有链接文本。
9. 能为每个候选锚文本生成 Top 3 推荐链接。
10. 推荐链接展示分数和原因。
11. 能保存人工审核结果。
12. 能生成插入预览。
13. 能保存本地写回快照。
14. 能回滚到某次 before_html。
15. pytest 全部通过。
```

### 17.2 质量验收

必须做到：

```text
1. 后端不能在控制台打印敏感 env。
2. API 错误必须返回清晰 detail。
3. 插入失败不得静默成功。
4. score_total 必须在 0-100。
5. 所有数据库主键使用 UUID。
6. 所有时间字段使用 UTC。
7. 前端刷新后，审核结果和快照仍存在。
8. 不允许只用前端内存保存关键状态。
```
---

## 18. Codex 执行顺序

Codex 必须按以下阶段开发。

### Phase 1：项目骨架

完成：

```text
docker-compose.yml
.env.example
backend FastAPI 启动
frontend Vite React 启动
GET /api/health
README 启动说明
```

验收：

```text
http://localhost:8000/api/health 返回 ok
http://localhost:5173 能打开 Dashboard
```
---

### Phase 2：数据库与页面导入

完成：

```text
SQLAlchemy models
Alembic migration
PostgreSQL 连接
POST /api/pages/import
GET /api/pages
GET /api/pages/{page_id}
POST /api/pages
canonical_url 生成
content_hash 生成
ImportPages 前端
PageLibrary 前端
```

验收：

```text
能导入 sample JSON
能在页面库看到 blog / collection / product
重复导入同一 canonical_url 会更新而不是重复创建
```
---

### Phase 3：正文解析

完成：

```text
parser.py
POST /api/articles/{page_id}/parse
GET /api/articles/{page_id}/blocks
BlogWorkspace 前端展示 blocks
test_parser.py
```

验收：

```text
能把 blog raw_html 拆成 article_blocks
首段、heading、已有链接识别正确
```
---

### Phase 4：候选锚文本

完成：

```text
anchor_generator.py
rule_engine.py
POST /api/internal-linking/{source_page_id}/anchor-candidates/generate
GET /api/internal-linking/{source_page_id}/anchor-candidates
AnchorCandidateCard 前端
test_rule_engine.py
```

验收：

```text
候选锚文本来自正文原文
候选锚文本不来自首段、标题、已有链接段落
每段最多 2 个候选
```
---

### Phase 5：候选链接推荐

完成：

```text
recommender.py
POST /api/internal-linking/{source_page_id}/recommendations/generate
GET /api/internal-linking/{source_page_id}/recommendations
RecommendationCard 前端
test_recommender.py
```

验收：

```text
每个 anchor_candidate 返回 Top 3
每个 recommendation 有完整分数字段
排序符合 score_total 规则
```
---

### Phase 6：人工审核

完成：

```text
POST /api/internal-linking/{source_page_id}/decisions
ReviewPage 前端
DecisionPanel 前端
```

验收：

```text
能 approve / reject_anchor / reject_target / replace_target / skip
保存后刷新页面仍能看到状态
```
---

### Phase 7：插入预览与本地写回

完成：

```text
insertion.py
snapshot.py
POST /api/internal-linking/{source_page_id}/preview
POST /api/internal-linking/{source_page_id}/local-write
GET /api/snapshots
POST /api/snapshots/{snapshot_id}/rollback
PreviewPage 前端
SnapshotPage 前端
test_insertion.py
```

验收：

```text
能生成 preview_html
能保存 local_write 快照
能 rollback
插入错误时展示 rule_check.errors
```
---

### Phase 8：测试、样例数据、文档收尾

完成：

```text
sample_data/pages_sample.csv
sample_data/source_blog_sample.html
pytest 全部通过
README 完整
前端基础样式整理
```

验收：

```text
给用户一个双击后在浏览器打开工具的快捷方式，用户能通过交互完成mvp全链路
```
---

## 19. Sample JSON 数据要求

Codex 必须在前端 Import 页面内置一个 sample JSON，至少包含：

```text
1 篇 source blog，raw_html 至少包含 h1、h2、3 个 paragraph、1 个已有 a 标签。
2 个 collection 页面。
2 个 product 页面。
3 篇 blog 页面。
```

Sample 中必须能产生至少：

```text
3 个候选锚文本
每个候选锚文本至少 2 个推荐链接
至少 1 个候选因首段规则被过滤
至少 1 个 block 因已有链接被跳过
```
---

## 20. 最终交付物

Codex 完成后，项目必须具备：

```text
1. 可运行前端
2. 可运行 FastAPI 后端
3. 可运行 PostgreSQL Docker Compose
4. Alembic migration
5. 页面导入功能
6. 页面库
7. 博客工作台
8. 正文解析
9. 候选锚文本生成
10. 候选链接推荐
11. 人工审核
12. 插入预览
13. 本地写回快照
14. 回滚
15. pytest 测试
16. README
17. sample_data
```
---

## 21. Codex 禁止事项

Codex 不得：

```text
1. 把 MVP 做成生产级大系统。
2. 引入 Redis / Celery / pgvector。
3. 引入真实 Shopify API。
4. 实现登录注册。
5. 实现复杂权限。
6. 使用前端 localStorage 保存关键业务数据替代数据库。
7. 在没有人工审核的情况下自动插入链接。
8. 在 preview 失败时仍允许 local_write。
9. 忽略 offset 校验。
10. 删除或改写原文句子。
11. 静默吞掉 API 错误。
12. 省略测试。
```
