---
name: stock-event-research
description: Research a specified A-share stock or a small screened candidate set using current announcements, structured events, investor Q&A, and news with traceable evidence. Use for news, announcement, catalyst, risk, unlock, placement, repurchase, shareholder-change, or investor-Q&A requests; do not use for community sentiment or trading execution.
---

# Stock Event Research

Use the project's `run_event_research` capability for one stock, or the bounded LangGraph research route for up to three screened candidates.

## Workflow

1. Resolve the stock code from project data; never guess a code from a name.
2. Default to 7 days and never request more than 90 days.
3. Collect sources on demand. Do not crawl all A-shares or persist a PDF archive.
4. Prefer official announcements, then company Q&A, then established news sources.
5. Download only a small number of material announcement PDFs. Extract limited pages and delete the temporary files.
6. Separate facts from possible impact. Cite evidence IDs for every event conclusion.
7. Return `partial` when a source is unavailable and state the data gap.

Read [references/evidence-policy.md](references/evidence-policy.md) when classifying sources or wording impact conclusions.

## Boundaries

- Do not use Tushare or community posts in V0.3.
- Do not treat an unlock as a completed sale, a repurchase plan as completed repurchase, or a placement proposal as issuance completion.
- Do not convert correlation into causation or produce buy/sell instructions.
- Quant scores remain deterministic and are not changed by news sentiment.
