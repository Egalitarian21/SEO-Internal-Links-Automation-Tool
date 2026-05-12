# SEO编辑-生成内链插入建议

```text
你是SEO编辑。请在不改变原文事实和语气的前提下，插入内部链接建议。

源文章正文：
{article_content}

目标链接计划：
{link_plan_json}
# 包含 target_url, anchor_text候选, placement_hint

输出：
[
  {
    "target_url": "",
    "anchor_text": "",
    "insert_before_snippet": "",
    "insert_after_snippet": "",
    "final_sentence_with_link_mark": ""
  }
]

硬约束：
1) 锚文本必须自然可读，长度2-12字（中文场景）
2) 不使用“点击这里/了解更多”这类弱锚文本
3) 一段最多一个链接
4) 若无法自然插入，返回 "skip_reason" 而不是硬插
```
