# October 2026 Austrian automation / LLMOps job evidence

Sources reviewed on 21 October 2026. Job adverts can change or expire; these are **specific examples**, not a representative quantitative labour-market sample.

| Employer / public advert | Explicit demands | Portfolio implication |
| --- | --- | --- |
| [hello again, (Junior) Revenue Automation Engineer](https://at.linkedin.com/jobs/view/junior-revenue-automation-engineer-d-w-m-at-hello-again-4416146084) | n8n, LLM-powered workflows, Python/Node.js, SQL, APIs/Webhooks, dashboards/data quality | Projects 01+02 address the implementation stack |
| [Data Dynamics AI, AI Workflow Developer / Automation Engineer](https://at.linkedin.com/jobs/view/ai-workflow-developer-automation-engineer-at-data-dynamics-ai-4344522341) | n8n or comparable automation tools, Python/JavaScript, API/LLM integrations, internal reporting/lead workflows | Projects 01+02 demonstrate bounded mock integrations |
| [VIG, ML & LLM Ops Spezialist:in](https://group.vig/karriere/bewerben/stellenangebot/?handle=163) | Prompt/model versioning, automated testing, monitoring, guardrails, AI-judge/feedback processes | Project 03 demonstrates deterministic quality gating and prompt version metadata **only** |
| [n8n, Agentic Engineering Platform Engineer](https://at.linkedin.com/jobs/view/agentic-engineering-platform-engineer-at-n8n-4471682074) | Testing infrastructure, security-aware platform engineering, AI evaluation and quality metrics | Automated CI tests and quality gate provide early-career evidence |
| [ristl.IT, Automation Engineer Microsoft 365 & API Workflow](https://at.linkedin.com/jobs/view/automation-engineer-microsoft-365-api-workflow-techops-m-w-d-at-ristl-it-gmbh-4473471387) | REST/Graph API integration, monitoring, alerting, modular repositories, automation testing | Project 01 exemplifies integration plus observability |

**Design decision:** A third intake/summarisation bot would duplicate Project 02. A bounded quality/review gate addresses a distinct technical risk and illustrates testability, risk handling and responsible automation. Python + SQLite + n8n keep it comparable in scope, without a new cloud dependency.

**Do not overstate:** Project 03 is a deterministic policy prototype, not LLM-based evaluation or fully calibrated guardrails; the VIG vacancy is more senior and much broader than this portfolio project. Earlier IMS Nanofabrication, Gateway Ventures and Ventum Consulting briefs informed the initial project series, but their full original job-posting texts were not available for fresh line-by-line verification in this review.


## Added 21 October 2026 — demand for retrieval / RAG skills

These are verified examples of stated requirements, **not** a statistically representative job-market estimate.

| Employer / posting | Relevant explicit requirements | Project 04 mapping |
| --- | --- | --- |
| [Fronius, AI Engineer](https://at.linkedin.com/jobs/view/ai-engineer-m-w-d-at-fronius-%C3%B6sterreich-4297191502) | LLMs, RAG, LangChain/LlamaIndex, guardrails, evaluation, semantic/hybrid vector search | Evidence retrieval and simple evaluation (not full LLMOps) |
| [Klartext AI, AI Engineer (Vienna)](https://at.linkedin.com/jobs/view/software-developer-ai-engineer-nlp-llms-at-klartext-ai-4300683431) | Python, FastAPI, RAG, vector DB incl. pgvector, Docker, CI/CD | Direct stack match for retrieval backend |
| [Qualysoft, Python Developer – Generative AI / RAG (Vienna)](https://at.linkedin.com/jobs/view/python-developer-%E2%80%93-generative-ai-rag-m-f-d-at-qualysoft-4443388550) | Document ingestion, parsing/chunking, embeddings, vector retrieval, reranking, source attribution, evaluation | Ingestion, chunking, vector storage, source attribution and four-case evaluation; reranking omitted |
| [Waterglass.ai, AI/Agents Developer (Austria)](https://at.linkedin.com/jobs/view/full-stack-engineer-specializing-in-llms-ai-agents-at-waterglass-4340076751) | Python/JavaScript, n8n, LLMs, vector databases and RAG | n8n workflow + local retrieval API |

**Scope selection:** Exact pgvector retrieval with a no-cost lexical fallback keeps the implementation reproducible. A real semantic embedding provider is optional; it is misleading to call the hashed lexical baseline state-of-the-art semantic search. Senior-level advertised requirements (cloud infrastructure, large-scale evaluation, production operations) are outside this junior-scale project.

Technology reference: [pgvector reference and cosine search](https://github.com/pgvector/pgvector/blob/master/README.md).
