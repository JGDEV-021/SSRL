# SSRL — Semantic Software Representation Layer

> Making software understandable — to humans and to AI.

[![Status](https://img.shields.io/badge/status-research%20%2F%20docs--phase-orange)]()
[![Version](https://img.shields.io/badge/docs-v0.2-blue)]()
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
| Spec-driven Requirements | Draft |
| Position Paper | Draft (v0.2) |
| Research Plan | Draft |
| Research & Analysis | **Not started — next** |
| Prototype | No code yet (gated by research) |

> Code is intentionally deferred. The design space is still under investigation; writing a parser now would be guessing.

---

## Repository structure

```text
SSRL/
├── README.md
├── roadmap.md
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
│   └── SSRL-v0.2.md           # Position paper
├── research/
│   ├── plan.md                # Research questions, hypotheses, methods, sources
│   ├── literature/            # W1 — papers
│   ├── prior-art/             # W2 — tools
│   ├── discourse/             # W3 — practitioner pain points
│   ├── probes/                # W4 — throwaway experiments (not the prototype)
│   └── decisions/             # W5 — ADR-001…007
└── prototype/                 # Intentionally empty until research concludes
```

---

## Getting involved

SSRL is currently a research project. The most valuable contributions today:

- Criticism of the vision and principles ([`docs/vision.md`](docs/vision.md))
- Pointers to related work ([`docs/related-work.md`](docs/related-work.md))
- Real-world comprehension pain points

---

## License

[MIT](LICENSE) — © 2026 JGDEV