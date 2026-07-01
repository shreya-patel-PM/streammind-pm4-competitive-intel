\# StreamMind — PM Agent #4: Competitive Intelligence Agent



\*\*Part of the \[StreamMind](https://github.com/shreya-patel-PM) AI Product Builder portfolio — 20 agents across streaming, PM automation, and pharma.\*\*



\## What it does



Every Monday at 8 AM PT, a GitHub Actions cron triggers a Python script that researches 5 streaming competitors using Claude's web\_search tool, synthesizes cross-competitor patterns, emails a digest via Resend, and archives findings to a Notion database. No Make.com, no manual intervention — fully autonomous.



\## Why GitHub Actions instead of Make.com



Two reasons. First, it proves Python + cron as an alternative to no-code orchestration — demonstrating that the same logical pattern works on either surface. Second, it's more impressive in a portfolio demo: "this agent runs autonomously on a cron, no platform needed."



\## Architecture

GitHub Actions cron (Monday 8 AM PT)

→ Python script

→ Load 5 competitors from competitors.json

→ For each competitor:

→ Claude API + web\_search tool (research recent activity)

→ Parse structured findings (JSON)

→ Claude API (synthesize cross-competitor patterns + recommendations)

→ Resend API (send HTML email digest)

→ Notion API (archive findings to Competitive Watch database)



\*\*Stack:\*\* Python · GitHub Actions · Claude API (Sonnet 4.5 + web\_search) · Resend · Notion



\## The 5 competitors tracked



| Competitor | Focus areas |

|---|---|

| Netflix | Ad-supported tier growth, live sports expansion, games integration, content spend, AI features |

| Disney+ | Bundle pricing, Hulu integration, content library, subscriber growth, ad tier |

| Amazon Prime Video | Thursday Night Football, Freevee integration, X-Ray features, MGM catalog, ads |

| Apple TV+ | Original content strategy, MLS Season Pass, Apple One bundle, pricing, awards |

| Max (HBO) | Discovery+ merger content, pricing tiers, live sports, originals pipeline, international |



\## Digest structure



The weekly email contains:



\- \*\*Top 5 Developments\*\* — the most strategically important things across all competitors, ranked by impact

\- \*\*Per-Competitor Summary\*\* — 2-3 sentences each, including "quiet week" when nothing happened

\- \*\*Cross-Competitor Patterns\*\* — trends supported by 2+ competitors moving in the same direction

\- \*\*Recommended Actions\*\* — specific next steps ("investigate whether to match Netflix's new ad tier pricing") not generic ("keep monitoring")



Written for a product strategy lead who reads it in 5 minutes every Monday.



\## Key design decisions



\### Claude + web\_search over Perplexity

Claude's native web\_search tool handles both research and structured extraction in one call — no separate API to manage. Each competitor gets one Claude call that searches, reads, and returns structured JSON.



\### JSON extraction with fallback

If Claude's response can't be parsed as JSON, the system falls back gracefully — logs a warning and marks the competitor as having a quiet week rather than crashing the entire run.



\### Notion as audit trail

Every week's findings are archived with date, development count, and competitor tags. Over time this builds a searchable competitive history for trend analysis.



\### Resend over Gmail

Resend's API is simpler than Gmail's OAuth flow for automated sending. Free tier supports the weekly cadence without authentication complexity.



\## Repository layout



main.py                              Core script — research, synthesize, email, archive

competitors.json                     Competitor definitions + focus areas

requirements.txt                     Python dependencies

.env.example                         Template for local environment variables

.github/workflows/weekly-intel.yml   GitHub Actions workflow (Monday cron + manual dispatch)



\## Running locally



```bash

pip install -r requirements.txt

cp .env.example .env

\# Fill in your API keys in .env

python main.py

```



\## Running on GitHub Actions



1\. Add secrets in repo Settings → Secrets → Actions

2\. Workflow runs automatically every Monday 8 AM PT

3\. Manual trigger: Actions tab → Weekly Competitive Intel → Run workflow



\## What "shipped" looks like



\- \[x] 5 real competitors researched with Claude + web\_search

\- \[x] 22 developments found across competitors in first run

\- \[x] Cross-competitor pattern synthesis with specific recommendations

\- \[x] Email digest sent via Resend with professional formatting

\- \[x] Notion archive created with development count and competitor tags

\- \[x] GitHub Actions cron running autonomously every Monday

\- \[x] Manual dispatch for on-demand runs

\- \[x] Graceful error handling (email failure doesn't block Notion, and vice versa)



\## Related agents



\- \[Streaming #1 — Content Tagger](https://github.com/shreya-patel-PM/streammind-streaming1-content-tagger)

\- \[Streaming #7 — Content Gap Finder](https://github.com/shreya-patel-PM/streammind-streaming7-content-gap-finder)

\- \[Streaming #9 — Licensing Monitor](https://github.com/shreya-patel-PM/streammind-streaming9-licensing-monitor)

\- \[PM #3 — PRD Studio](https://github.com/shreya-patel-PM/PRD-Generator-form)



\## License



MIT

