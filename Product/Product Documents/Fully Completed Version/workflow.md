# Workflow

1. Manually obtain blog URLs from the Sitemap.
2. Batch-import URLs through the frontend.
3. The backend saves the Import Task.
4. The backend crawls blog content.
5. Clean HTML / extract body text / title / Meta.
6. Batch-generate Wiki cards with the LLM.
7. Store Wiki Cards in the database.
8. The implementation engineer selects a blog post in the frontend and enters review.
9. The backend calls the LLM:
   - Analyze the blog body text.
   - Select suitable anchor text.
   - Match target cards from Wiki Cards.
   - Generate internal-link suggestions.
10. The frontend displays internal-link suggestions pending approval.
11. A human Approves / Rejects.
12. Generate the final blog HTML.
13. Call the Shopify API to create the blog.
