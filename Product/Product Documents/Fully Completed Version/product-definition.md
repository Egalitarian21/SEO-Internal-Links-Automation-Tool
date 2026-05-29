# Product Definition

## 1. One-Sentence Product Positioning

> An ecommerce blog internal-link automation system based on LLM semantic understanding and a Wiki knowledge graph. It is used to batch-discover, validate, and manage high-quality internal links that comply with SEO standards. It is intended for use by the local team, and its output is linked directly to the Shopify admin.

---

## 2. Core User Stories

**Story 1 - Semantic Discovery**
- **As a** SEO implementation engineer,
- **I want** the system to automatically understand each blog post's core topic and product intent,
- **So that** I can obtain a semantically relevant list of candidate internal-link recommendations without manually reading the full article.

---

**Story 2 - Standards Implementation**
- **As a** SEO implementation engineer,
- **I want** recommendation results to be automatically filtered according to preset internal-linking standards (anchor text diversity, an upper limit on link density, and avoidance of orphan pages),
- **So that** every inserted internal link complies with the site's SEO standards without requiring a second round of manual verification.

---

**Story 3 - Batch Efficiency Improvement**
- **As a** SEO implementation engineer,
- **I want** to run a one-click batch scan across the entire blog library and generate an auditable internal-link change report,
- **So that** I can complete internal-link organization for a blog cluster within 30 minutes instead of the several days it originally required.

---

## 3. Functional Scope

### Must Have

- **Wiki-Style Knowledge Graph View**
  - Visualize the internal-link topology of the blog cluster as a node graph, intuitively showing link density and orphan distribution.
  - The core underlying logic is that relationships between article nodes are derived by the LLM based on the blog wiki card database:
    1. Read one blog post.
    2. Produce the wiki card for that blog post.
    3. According to the anchor text standards, find words suitable for internal links.
    4. Find the most suitable article to link to within the existing blog library.
    5. Continuously organize the entire site's blog posts into topical content clusters.

- **Internal-Link Candidate Recommendations**
  - Recommend Top-N candidate internal links for each article based on semantic similarity plus product-topic matching.
  - Recommendation results include: target URL, suggested anchor text, insertion paragraph location, and semantic relevance score.

- **Standards Validation Layer**
  - Anchor text diversity detection (to avoid repeated anchor text stuffing).
  - Upper-limit control for internal-link density within a single article (with a configurable threshold).
  - Orphan page detection and priority link-supplement prompts.

- **Change Report Output**
  - Generate structured CSV / JSON reports with fields including: article ID, insertion location, anchor text, target link, and confidence.
  - Support three-state labels: "Accepted / Rejected / Pending Review".

- **Minimal Web UI**
  - Task trigger entry point (single article / batch).
  - Recommendation list display with one-click manual confirmation / rejection.

---

### Should Have

- **Incremental Scan Mode**
  - After a new article is published, automatically trigger partial re-indexing and only re-recommend for affected nodes, avoiding a full rerun.

- **Anchor Text Generation Suggestions**
  - The LLM automatically generates 2-3 natural-language anchor text options based on context for the engineer to choose from.

- **CMS Integration Adapter**
  - Provide write-back interfaces for the WordPress REST API / Shopify Blog API, supporting one-click updates of confirmed internal links directly to the CMS.

- **Standards Configuration Panel**
  - Visually configure rule parameters such as internal-link density, anchor text blacklist, and product-cluster mapping relationships.

---

## 4. Core Differentiation

The underlying logic of Link Whisper and Internal Link Juicer is **keyword matching + rules engine**.
The core difference of this tool is the introduction of an **LLM-Wiki semantic reasoning layer**:

- The associations between articles do not depend on keyword co-occurrence. Instead, they are inferred after the LLM understands the **content intent and product context**.
- The recommendation logic is explainable: each recommendation includes an LLM-generated "reason for association", allowing engineers to audit the basis for the decision.
- As the blog library expands, the semantic index continuously self-optimizes, and recommendation quality does not decline as content scale grows.
