# Technology Stack Selection

**Project Positioning:** An ecommerce blog internal-link automation system driven by LLM + Wiki knowledge graph.
**Constraints:** Solo development - launch in 40 days - free tools first.

## Technology Stack Overview

| Dimension | Choice |
|------------|-----------------------------|
| Frontend framework | Next.js 15 |
| UI component library | shadcn/ui |
| Backend runtime | Python + FastAPI |
| Database | Supabase (including pgvector) |
| Authentication approach | Auth.js v5 |
| Deployment platform | Vercel + Railway |

---

## Key Architecture Notes

- **Vector retrieval is core:** Supabase pgvector directly handles semantic vector storage and retrieval. This avoids introducing an independent vector database and is a key decision for controlling complexity in a solo project.
- **Frontend-backend separation is necessary:** LLM batch-processing tasks take a long time and must run on a platform that supports persistent processes (Railway). They cannot be placed inside Vercel Serverless functions.
- **The Python backend cannot be replaced:** The three core capabilities of Wiki knowledge graph construction, LLM orchestration, and NLP text processing all depend on the Python ecosystem. Forcing an implementation in Node.js would consume a large amount of time reinventing existing tools.
