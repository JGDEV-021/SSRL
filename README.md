# SSRL — Semantic Software Representation Layer

> Making software understandable — to humans and to AI.

[![Status](https://img.shields.io/badge/status-prototype%20%2F%20validation-orange)]()
[![Version](https://img.shields.io/badge/docs-v0.3-blue)]()
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

AI made writing code cheap. SSRL asks the next question: **how do we make code easy to understand?**

SSRL is a research initiative for a *semantic representation layer* — an abstraction built on top of source code that makes the structure, behavior, and intent of a software system explicit, navigable, and answerable. For developers, for teams, and for the AI agents that increasingly write the code.

---

## The problem

```
Cost of producing code  <<  Cost of understanding code
```

Generating code with AI is fast and easy. Understanding it — what it does, why it exists, what it breaks, whether it is correct — is still slow, hard, and usually locked in someone's head.

### The comprehension gap

| Mode | What they do | What they can do |
| --- | --- | --- |
| **AI SLOP** | Generate code without understanding it | Cannot judge, fix, explain, or trust it |
| **AI DEV** | Generate code, understand what they produce | Can judge and maintain the result |
| **DEV** | Builds structure and logic with full control | Deepest understanding of the system |

SSRL exists to compress the distance between the first two and the third — and to make that understanding survive the people and models that created it.

---

## What SSRL is

A semantic layer over software, grounded and honest:

- **Facts first.** Deterministic structure (modules, functions, calls, imports, events) extracted from code — verifiable, not invented.
- **Hypotheses marked as hypotheses.** Semantic interpretation (intent, flows, domain concepts) is always probabilistic, never dressed as fact.
- **Confidence and evidence.** Every hypothesis carries a confidence score and the evidence behind it. You can always ask "why does SSRL believe this?"
- **Continuously derived.** The layer regenerates incrementally as code changes. It never goes stale by design.
- **Dev-friendly.** Adoption must be low-friction. If it costs more than a quick `git grep`, it has already failed the developer bar.

### Projections, not the product

A semantic layer can be experienced through many **projections**:

- Graph exploration
- Question & answer over the codebase
- Progressive zoom: system → subsystem → module → line
- Live narrative / self-explaining documentation
- Agent context supply

The graph is *one* projection. The product is the layer. Which projection becomes the **primary** interaction is an open research question — the first deliverable of the research phase.

---

## Status

| Stage | State |
| --- | --- |
| Vision & Principles | Done |
| Spec-driven Requirements | Frozen v1.0 (Gate G1 passed) |
| Position Paper | Draft (v0.3 — G1 resolution + prototype findings) |
| Research Plan | Executed (G1 passed; W1–W5, ADR-001…008) |
| Research & Analysis | Done |
| Prototype (V1 MVP) | **Shipped — v0.7.0**, Phases 3–9 complete, 67 unit tests |
| Validation | Phase 9 draft automated study + refusal probe executed; definitive human-graded study next (Phase 10) |

The prototype is no longer deferred: `prototype/ssrl/` is a working, dependency-free
package (extract → enrich → calibrate → Q&A → narrative → CLI → watch → MCP →
micro-LLM proposer). Validation evidence lives in `prototype/REPORT-P9.md`
(§6.1 draft study, §6.2 refusal probe battery) — the grounded condition scored
entity-F1 **0.61** (recall 1.0) vs baseline 0.15.

## Repository structure

```text
SSRL/
├── README.md
├── roadmap.md              # Phases 0–10; 3–9 done, 10 (publication) next
├── LICENSE
├── docs/
│   ├── vision.md              # Mentality, objectives, non-goals, principles
│   ├── concepts.md            # The semantic model (facts, hypotheses, confidence)
│   ├── requirements.md        # Spec-driven requirements
│   ├── architecture.md        # Design concerns + resolved decisions (ADR-backed)
│   ├── related-work.md        # Research leads / prior art
│   └── projections/
│       └── graph.md           # Graph projection — a candidate, not the product
├── paper/
│   ├── SSRL-v0.2.md           # Position paper (research phase)
│   └── SSRL-v0.3.md           # Position paper (G1 + prototype findings)
├── research/
│   ├── plan.md                # Research questions, hypotheses, methods, sources
│   ├── literature/            # W1 — papers
│   ├── prior-art/             # W2 — tools
│   ├── discourse/             # W3 — practitioner pain points
│   ├── probes/                # W4 — throwaway experiments (not the prototype)
│   └── decisions/             # W5 — ADR-001…008 (all accepted)
└── prototype/
    ├── README.md              # Prototype readme (quick start, verified properties)
    ├── BUILDLOG.md            # Per-phase build log (Phases 1–9)
    ├── REPORT-V1.md           # V1 MVP delivery report (Phases 3–6.5)
    ├── REPORT-P7.md / REPORT-P8.md / REPORT-P9.md
    ├── ssrl/                  # The V1 package (stdlib only, zero deps)
    ├── lab/                   # Phase 7–9 labs + study/probe harnesses
    └── tests/                 # 67 unit tests
```

---

## Getting involved

SSRL has a working V1 prototype (`prototype/`) and an active validation track.
Valuable contributions today:

- Criticism of the vision and principles ([`docs/vision.md`](docs/vision.md))
- Pointers to related work ([`docs/related-work.md`](docs/related-work.md))
- Real-world comprehension pain points
- Feedback on the prototype's output quality (facts vs hypotheses vs `ask`)

---

## License

[MIT](LICENSE) — © 2026 JGDEV