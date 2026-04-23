---
title: Revarie LM v1.0
emoji: 🧠
colorFrom: gray
colorTo: blue
sdk: docker
app_port: 7860
pinned: true
---

# Revarie LM v1.0 – Cognitive Emulation Engine

This Space hosts the complete neuro-symbolic cognitive architecture for **Project IMACE: Revarie LM v1.0**.

## Architecture

The Docker container runs four coordinated services:

| Service | Language | Port | Role |
|---------|----------|------|------|
| API Gateway | Rust (Axum) | 3000 | Main HTTP server, routing, auth |
| Orchestrator | Python (FastAPI) | 8000 | Multi-model LLM coordination, memory |
| Reasoner | C++ (Crow) | 9000 | POMDP, Bayesian inference, rebound |
| Symbolic | Common Lisp (SBCL) | – | Belief space, cognitive rules |

All services are managed by `supervisord` and exposed via `nginx` on port `7860`.

## Personas

- **Samara**: High anthropomorphic reflection (warm, empathetic, relational)
- **Artery 1.0**: Low anthropomorphic reflection (functional, neutral, precise)

## Endpoints

| Path | Method | Description |
|------|--------|-------------|
| `/health` | GET | Health check |
| `/api/chat` | POST | Send chat message |
| `/api/admin/stats` | GET | System statistics |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `VAULT_API_URL` | Yes | Cloudflare D1 Worker URL |
| `VAULT_API_KEY` | Yes | D1 API key |
| `VECTORIZE_API_URL` | Yes | Cloudflare Vectorize URL |
| `VECTORIZE_API_TOKEN` | Yes | Vectorize token |
| `GROQ_KEYS` | Yes | Comma-separated Groq keys |
| `CEREBRAS_KEYS` | Yes | Comma-separated Cerebras keys |
| `GEMINI_KEYS` | Yes | Comma-separated Gemini keys |

## Deployment

This Space is automatically rebuilt when changes are pushed to the `Production` branch of the [GitHub repository](https://github.com/project-imace/revarie-lm-v1).

## Research

Revarie LM v1.0 is part of Project IMACE (Integrated Modular Architecture for Cognitive Emulation). It investigates whether structured cognitive emulation can produce measurable psychological consequences in human subjects.

**Principal Investigator:** Project IMACE Research Team  
**Contact:** research@imace.online  
**License:** Apache 2.0
