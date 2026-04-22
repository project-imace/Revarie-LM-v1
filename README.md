# Revarie LM v1.0 – Cognitive Emulation Research Instrument

[

![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)

](LICENSE)
[

![Cognitive Core Tests](https://github.com/project-imace/revarie-lm-v1/actions/workflows/test-cognitive-core.yml/badge.svg)

](https://github.com/project-imace/revarie-lm-v1/actions/workflows/test-cognitive-core.yml)

[

![Python Ecosystem Tests](https://github.com/project-imace/revarie-lm-v1/actions/workflows/test-python-ecosystem.yml/badge.svg)

](https://github.com/project-imace/revarie-lm-v1/actions/workflows/test-python-ecosystem.yml)
[

![UI Tests](https://github.com/project-imace/revarie-lm-v1/actions/workflows/test-ui.yml/badge.svg)

](https://github.com/project-imace/revarie-lm-v1/actions/workflows/test-ui.yml)

**Revarie LM v1.0** is a research-grade neuro-symbolic cognitive architecture developed by **Project IMACE**. It serves as a parametric instrument for investigating anthropomorphic reflection in language-based AI systems. The system powers a 14-day longitudinal study with two distinct personas:

- **Samara**: High anthropomorphic reflection – warm, empathetic, relational.
- **Artery 1.0**: Low anthropomorphic reflection – functional, precise, neutral.

---

## 🏛️ Architecture Overview

Revarie LM v1.0 is a **polyglot cognitive stack** spanning four languages:

| Layer | Language | Role |
|-------|----------|------|
| **API Gateway** | Rust (Axum) | High-performance HTTP server, auth, routing |
| **Orchestrator** | Python (FastAPI) | Multi-model LLM coordination, memory management |
| **Reasoning Core** | C++ (Crow) | POMDP, Bayesian inference, rebound mechanism |
| **Symbolic Rules** | Common Lisp (SBCL) | Belief space, cognitive priors, meta-reasoning |
| **Frontend** | TypeScript (Next.js) | Participant-facing chat interfaces |

All services are containerized and run under `supervisord`, exposed via Nginx on a single Hugging Face Space.

---

## 🧠 Theoretical Foundations

The architecture integrates:

- **Turing's Model of Mind** (Sprevak, 2017) – strong vs. weak modelling
- **Global Workspace Theory** (Baars, 1988; Dehaene, 2014)
- **Active Inference / Free Energy Principle** (Friston, 2010)
- **Dual-Process Theory** (Kahneman, 2011)
- **Bayesian Theory of Mind** (Baker, Saxe, Tenenbaum, 2009)
- **Piaget's Constructivism**
- **Freudian / Jungian Psychoanalytic Structures** (Id, Ego, Superego; cognitive functions)
- **Neuromodulatory Emotions** (Larue et al., 2013; Fellous, 1999)

---

## 📦 Repository Structure

```text
revarie-lm-v1/
├── .github/                    # CI/CD workflows
├── turing-machine/             # Physical Symbol System
├── cognitive-architecture/     # Dual-process, GWT, Active Inference, Belief Space, Rebound, POMDP, JEPA
├── memory-systems/             # Sensory, Working, Episodic, Semantic, Procedural, Consolidation
├── theory-of-mind/             # Bayesian Inverse Planning, ToMNet
├── psychoanalytic-modules/     # Id, Ego, Superego, Jungian functions
├── persona-engine/             # Core parameters, Affective modulator, Social interaction, Narrative self, Persona shaper, Safety guardrail, Participant context
├── orchestrator/               # API key vault, Model router, Provider clients, API gateway, Task scheduler
├── rag-pipeline/               # Retriever, Re-ranker, Context assembler
├── training/                   # AMD MI300X LoRA training, Kaggle nightly, Colab fallback
├── deployment/                 # Docker, Vercel, Hugging Face, cron
├── ui/                         # Next.js TypeScript frontend
├── config/                     # Environment templates
└── tests/                      # Cross-module integration & load tests
```

---

## 🚀 Deployment (Zero-Cost Stack)

| Component | Platform | Purpose |
|-----------|----------|---------|
| **Backend** | Hugging Face Spaces (Docker) | Runs all services in one container |
| **Frontend** | Vercel | Next.js static + SSR |
| **Structured DB** | Cloudflare D1 | Participant data, VAMS, session logs |
| **Vector DB** | Cloudflare Vectorize | Episodic memory embeddings |
| **LLM APIs** | Groq (8 keys), Cerebras (8 keys), Gemini (2 keys) | Neural substrate |
| **Nightly Training** | Kaggle (GPU) | Daily consolidation & LoRA fine-tuning |
| **Heavy Training** | DigitalOcean AMD MI300X | One-time persona LoRA training |
| **Keep-Alive** | cron-job.org | Prevents HF Space sleep |

---

## 🔧 Quick Start

```bash
# Clone the repository
git clone https://github.com/project-imace/revarie-lm-v1.git
cd revarie-lm-v1

# Build all services
cd cognitive-architecture && make build

# Run tests
make test-all

# Start locally (Docker)
docker-compose -f deployment/docker/docker-compose.yml up
```

---

## 📄 License

Apache 2.0 – see [LICENSE](LICENSE)

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md).

---

*Project IMACE – Revarie LM V1*  
research@imace.online
