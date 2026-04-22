<div align="center">
  <h1>Revarie LM v1.0</h1>
  <h3>Cognitive Emulation Research Instrument</h3>
  <p>
    <em>A research-grade neuro-symbolic cognitive architecture by <strong>Project IMACE</strong></em>
  </p>
  
  <p>
    <a href="LICENSE">
      <img src="https://img.shields.io/badge/License-Apache_2.0-blue?style=flat-square" alt="License"/>
    </a>
  </p>
  <br />

  <p>
    <a href="https://github.com/project-imace/revarie-lm-v1/actions/workflows/core-math-engine.yml">
      <img src="https://github.com/project-imace/revarie-lm-v1/actions/workflows/core-math-engine.yml/badge.svg?branch=Production" alt="Core Math Engine"/>
    </a>
    <a href="https://github.com/project-imace/revarie-lm-v1/actions/workflows/memory-rag-systems.yml">
      <img src="https://github.com/project-imace/revarie-lm-v1/actions/workflows/memory-rag-systems.yml/badge.svg?branch=Production" alt="Memory & RAG"/>
    </a>
    <a href="https://github.com/project-imace/revarie-lm-v1/actions/workflows/persona-training.yml">
      <img src="https://github.com/project-imace/revarie-lm-v1/actions/workflows/persona-training.yml/badge.svg?branch=Production" alt="Persona Training"/>
    </a>
    <br />
    <a href="https://github.com/project-imace/revarie-lm-v1/actions/workflows/orchestrator-integration.yml">
      <img src="https://github.com/project-imace/revarie-lm-v1/actions/workflows/orchestrator-integration.yml/badge.svg?branch=Production" alt="Orchestrator"/>
    </a>
    <a href="https://github.com/project-imace/revarie-lm-v1/actions/workflows/ui-frontend.yml">
      <img src="https://github.com/project-imace/revarie-lm-v1/actions/workflows/ui-frontend.yml/badge.svg?branch=Production" alt="UI Frontend"/>
    </a>
    <a href="https://github.com/project-imace/revarie-lm-v1/actions/workflows/deploy-hf-space.yml">
      <img src="https://github.com/project-imace/revarie-lm-v1/actions/workflows/deploy-hf-space.yml/badge.svg?branch=Production" alt="Deploy to HF Space"/>
    </a>
  </p>
</div>

---


---

## 🧬 Overview

<p align="justify">
<strong>Revarie LM v1.0</strong> is a parametric cognitive system designed to investigate 
<strong>anthropomorphic reflection in language-based AI</strong>. It powers a controlled 
<strong>14-day longitudinal study</strong> with two distinct personas:
</p>

<ul>
  <li><strong>Samara</strong> → Warm, empathetic, high anthropomorphic reflection</li>
  <li><strong>Artery 1.0</strong> → Functional, precise, low anthropomorphic reflection</li>
</ul>

---

## 🏛️ Architecture Overview

<p align="center"><strong>Polyglot Cognitive Stack</strong></p>

<table align="center">
<tr>
<th>Layer</th>
<th>Language</th>
<th>Role</th>
</tr>
<tr>
<td><strong>API Gateway</strong></td>
<td>Rust (Axum)</td>
<td>High-performance HTTP server, auth, routing</td>
</tr>
<tr>
<td><strong>Orchestrator</strong></td>
<td>Python (FastAPI)</td>
<td>Multi-model coordination, memory management</td>
</tr>
<tr>
<td><strong>Reasoning Core</strong></td>
<td>C++ (Crow)</td>
<td>POMDP, Bayesian inference, rebound mechanisms</td>
</tr>
<tr>
<td><strong>Symbolic Rules</strong></td>
<td>Common Lisp (SBCL)</td>
<td>Belief space, cognitive priors, meta-reasoning</td>
</tr>
<tr>
<td><strong>Frontend</strong></td>
<td>TypeScript (Next.js)</td>
<td>Participant-facing interface</td>
</tr>
</table>

<p align="center">
All services are containerized via Docker, orchestrated with supervisord, and exposed through Nginx.
</p>

---

## 🧠 Theoretical Foundations

<ul>
  <li><strong>Turing’s Model of Mind</strong> – Strong vs Weak modelling</li>
  <li><strong>Global Workspace Theory</strong></li>
  <li><strong>Active Inference / Free Energy Principle</strong></li>
  <li><strong>Dual-Process Theory</strong></li>
  <li><strong>Bayesian Theory of Mind</strong></li>
  <li><strong>Piaget’s Constructivism</strong></li>
  <li><strong>Psychoanalytic Structures</strong> – Freudian & Jungian</li>
  <li><strong>Neuromodulatory Emotions</strong></li>
</ul>

---

## 📦 Repository Structure

<pre>
revarie-lm-v1/
├── .github/
├── turing-machine/
├── cognitive-architecture/
├── memory-systems/
├── theory-of-mind/
├── psychoanalytic-modules/
├── persona-engine/
├── orchestrator/
├── rag-pipeline/
├── training/
├── deployment/
├── ui/
├── config/
└── tests/
</pre>

---

## 🚀 Deployment Stack

<table>
<tr>
<th>Component</th>
<th>Platform</th>
<th>Purpose</th>
</tr>
<tr>
<td>Backend</td>
<td>Hugging Face Spaces</td>
<td>Containerized services</td>
</tr>
<tr>
<td>Frontend</td>
<td>Vercel</td>
<td>Next.js UI</td>
</tr>
<tr>
<td>Structured DB</td>
<td>Cloudflare D1</td>
<td>Session & participant data</td>
</tr>
<tr>
<td>Vector DB</td>
<td>Cloudflare Vectorize</td>
<td>Embeddings</td>
</tr>
<tr>
<td>Training</td>
<td>Kaggle / MI300X</td>
<td>LoRA fine-tuning</td>
</tr>
<tr>
<td>Keep Alive</td>
<td>cron-job.org</td>
<td>Prevent sleep</td>
</tr>
</table>

---

## 🔧 Quick Start

```bash
git clone https://github.com/project-imace/revarie-lm-v1.git
cd revarie-lm-v1

cd cognitive-architecture && make build
make test-all

docker-compose -f deployment/docker/docker-compose.yml up
 ```


---

📄 License

Apache 2.0 – see LICENSE


---

🤝 Contributing

Contributions are welcome. See CONTRIBUTING.md


---

<p align="center">
<strong>Project IMACE</strong><br/>
research@imace.online
</p>
