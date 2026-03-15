# CLAUDE.md — ai_engineer

This file provides guidance to Claude Code when working in this repository.

---

## Project

10-month AI engineering learning journey (March 2026 – January 2027).
Master curriculum: `AI_Engineer_Plan.html`
Portfolio URL: https://emkex.github.io/ai_engineer/AI_Engineer_Plan.html
GitHub: https://github.com/emkex/ai_engineer — PUBLIC REPO

Goal: build progressively more complex AI systems culminating in deployable projects
and commercial contracts. Primary specialization: AI for analytical chemistry
(chromatography, spectral analysis).

---

## Environment

- Python 3.12.3 via `.venv/` — activate: `source .venv/bin/activate`
- Dependencies tracked in `requirements.txt` as added
- No build system yet

---

## Code Conventions

- Python 3.10+ syntax
- Comments in Russian
- Use `dataclasses` for structured data
- Each feature in its own module file
- Secrets via `python-dotenv` only — never hardcode keys

---

## Repository Structure

Organized by learning week/phase as the project evolves:

- `AI_Engineer_Plan.html` — master plan (portfolio artifact, safe to commit)
- `1_week/` — Week 1 exercises
- Future: `2_week/`, `rag_pipeline/`, etc.
- `files/` — excluded from git
- `test.py` — excluded from git (scratch file)

---

## Key Technologies by Phase

| Phase | Period | Focus | Key tools |
|-------|--------|-------|-----------|
| 0 | Mar–Apr | Foundations | Python, Git, Anthropic API, Ollama, pandas, asyncio |
| 1 | Apr–May | Agent systems | LangGraph, PydanticAI, Qdrant, Docker, MCP, n8n |
| 2 | Jun | Deployment | Docker Compose, PostgreSQL, nginx, LangSmith/Langfuse |
| 3 | Jul–Aug | Fine-tuning | HuggingFace, PEFT/LoRA, multimodal (Claude Vision) |
| 4 | Sep–Dec | Commercialization | Kubernetes, CI/CD, client projects |

---

## Git Workflow

- Commit daily with descriptive message (3–5 lines: what was done and why)
- Commits mark the end of each daily study block
- This is a PUBLIC repo — see git safety rules below

---

## Git Safety

This repo is PUBLIC. Every committed file is visible to anyone.
Full rules: `~/.claude/rules/git-safety.md` (global, always active)

Short version:
- Never commit `.env*`, `*.key`, `*.pem`, credentials of any kind
- Never hardcode API keys in code
- `.claude/settings.local.json` is excluded from git — keep personal settings there

---

## Global Skills Available

- `create-new-skill` — create a new skill from template
- `update-claude-md` — save validated knowledge to CLAUDE.md

## Global Agents Available

- `RESEARCHER` — investigation, analysis, preparing executor_brief
- `EXECUTOR` — implementation, file edits, running commands
