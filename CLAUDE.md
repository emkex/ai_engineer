# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

This is a 10-month AI engineering learning journey (March 2026 – January 2027). The master curriculum is in `AI_Engineer_Plan.html`. The goal is to build progressively more complex AI systems, culminating in deployable projects and commercial contracts.

**Primary specialization:** AI for analytical chemistry (chromatography, spectral analysis).

## Environment

- Python 3.12.3 via `.venv/` (activate: `source .venv/bin/activate`)
- No build system yet — dependencies will be tracked in `requirements.txt` as added

## Code Conventions

- Python 3.10+ syntax
- Comments in Russian
- Use `dataclasses` for structured data
- Each feature in its own module file

## Repository Structure

Code is organized by learning week/phase as the project evolves:

- `1_week/` — Week 1 Python basics exercises
- Future directories will follow the same pattern (e.g. `2_week/`, `rag_pipeline/`, etc.)
- `files/` — excluded from git (in `.gitignore`)
- `test.py` — excluded from git (scratch file)

## Key Technologies by Phase

| Phase | Focus | Key tools |
|-------|-------|-----------|
| 0 (Mar–Apr) | Foundations | Python, Git, Anthropic API, Ollama, pandas, asyncio |
| 1 (Apr–May) | Agent systems | LangGraph, PydanticAI, Qdrant, Docker, MCP, n8n |
| 2 (Jun) | Deployment | Docker Compose, PostgreSQL, nginx, LangSmith/Langfuse |
| 3 (Jul–Aug) | Fine-tuning | HuggingFace, PEFT/LoRA, multimodal (Claude Vision) |
| Fall | Commercialization | Kubernetes, CI/CD, client projects |

## Git Workflow

- Commit daily with a descriptive message (3–5 lines explaining what was done and why)
- Commits mark the end of each daily study block
