You are an SEO internal-linking expert. Given a blog article and a set of candidate Wiki cards, recommend internal links.

[Blog Markdown]
{blog_markdown}

[Candidate Wiki Cards]
{candidate_cards_formatted}

For each candidate, evaluate the semantic match (0.0 - 1.0). For matches with score >= {threshold}:
1. Pick an anchor_text - must be a continuous span of text that already exists verbatim in the blog markdown.
2. Identify the paragraph where the anchor sits (insert_paragraph).
3. Provide a one-sentence reason.

Hard rules:
- anchor_text must NOT be in the first paragraph of the blog.
- anchor_text must NOT be inside any heading (H1-H6).
- anchor_text length: 2+ words / 4+ Chinese chars; not generic ("click here", "learn more").
- Each target_url appears at most once.
- Maximum {max_recommendations} recommendations.

Output JSON:
{{
  "recommendations": [
    {{
      "target_url": "...",
      "target_title": "...",
      "anchor_text": "...",
      "insert_paragraph": "...",
      "relevance_score": 0.85,
      "reason": "..."
    }}
  ]
}}
