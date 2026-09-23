# SSRL — Semantic Software Representation Layer

> A persistent semantic representation of software for humans and AI.

[![Status](https://img.shields.io/badge/status-experimental-orange)]()
[![Version](https://img.shields.io/badge/version-v0.7.0-blue)]()
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

## Overview

AI has made software production significantly cheaper.

The bottleneck is increasingly **software understanding**.

Modern development tools can generate, search, navigate, and modify large codebases, but understanding the structure, behavior, intent, dependencies, and consequences of those changes still requires reconstructing context from source code and tooling.

**SSRL — Semantic Software Representation Layer** explores a different approach:

> Build a persistent representation of a software system that makes its structure, semantic interpretations, evidence, and uncertainty explicitly available to humans and AI systems.

SSRL is not a replacement for source code, static analysis, LSPs, search, or coding agents.

It is a **derived representation layer over the software itself**.

---

## The problem

A codebase contains substantially more information than what is directly visible from individual files.

Understanding a system often requires reconstructing relationships such as:

```text
Which components are involved?
        ↓
How are they connected?
        ↓
What behavior emerges from those connections?
        ↓
What is this subsystem responsible for?
        ↓
Why does it exist?
        ↓
What could change if I modify it?
```

Current tooling handles different parts of this problem well:

* search finds text
* ASTs expose syntax
* LSPs expose structural relationships
* static analyzers identify properties of code
* Git exposes historical changes
* dependency graphs expose relationships
* coding agents reason over all of the above

But the resulting understanding is generally reconstructed **on demand**.

SSRL investigates whether keeping a persistent, structured representation of that understanding can provide a useful abstraction for both developers and AI agents.

---

# Core model

SSRL separates information into two fundamentally different categories.

## Facts

Facts are deterministic observations derived from the source code.

Examples:

```text
Module A imports Module B

Function X calls Function Y

Class User contains method authenticate

Module API depends on Module Database
```

Facts should be directly verifiable against the underlying source.

## Hypotheses

Hypotheses are semantic interpretations derived from facts and other evidence.

Examples:

```text
authenticate() probably handles user authentication

This flow appears to represent payment processing

Module X may be responsible for session management
```

Hypotheses are not promoted to facts simply because a model generated them.

They carry metadata such as:

* confidence
* evidence
* production method
* provenance

Conceptually:

```text
                  SSRL
                   │
          ┌────────┴────────┐
          │                 │
        FACTS           HYPOTHESES
          │                 │
    deterministic      probabilistic
    verifiable         evidence-backed
          │                 │
          └────────┬────────┘
                   │
             REPRESENTATION
```

This distinction is one of the central design principles of SSRL.

---

# Semantic representation

The current model contains structural and semantic entities.

### Structural entities

```text
Repository
Module
Class
Function
Method
```

### Semantic entities

```text
Service
Flow
Intent
Domain Concept
```

### Structural relations

```text
CONTAINS
IMPORTS
CALLS
```

### Semantic relations

```text
PARTICIPATES_IN
SUPPORTS_INTENT
RELATED_TO
```

The representation uses stable deterministic identifiers so that entities can be referenced across projections and updates.

The semantic model is intentionally separate from any particular visualization or interface.

---

# The layer, not the graph

SSRL is sometimes described as a code graph.

A graph is only one possible projection.

The underlying representation can support multiple interfaces:

```text
                         SSRL
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
      Graph              Q&A            Narrative
        │                 │                 │
        ▼                 ▼                 ▼
    Explore             Ask             Explain
```

Other possible projections include:

* progressive system → subsystem → module → symbol exploration
* living documentation
* impact analysis
* AI context
* explanation auditing
* semantic navigation

**The graph is one projection. The representation layer is the underlying system.**

---

# Architecture

The current prototype follows a pipeline in which deterministic extraction forms the foundation for higher-level representations.

```text
Source Code
    │
    ▼
┌──────────────┐
│   Extract    │
└──────┬───────┘
       ▼
┌──────────────┐
│    Enrich    │
└──────┬───────┘
       ▼
┌──────────────┐
│   Calibrate  │
└──────┬───────┘
       │
       ├───────────────┐
       ▼               ▼
     Q&A            Narrative
       │               │
       └───────┬───────┘
               ▼
              CLI
               │
        ┌──────┴──────┐
        ▼             ▼
      Watch          MCP
        │             │
        └──────┬──────┘
               ▼
        Semantic workflows
```

The prototype additionally contains:

* micro-LLM hypothesis proposal
* explanation generation
* deterministic explanation verification
* deleted-symbol tracking

---

# AI integration

SSRL is designed to work alongside coding agents rather than replace them.

A coding agent can generate semantic interpretations, while SSRL provides the underlying structural representation and verifies whether claims are grounded in available evidence.

A simplified workflow is:

```text
Coding Agent
     │
     ▼
Repository changes
     │
     ▼
SSRL detects impact
     │
     ▼
Deterministic structural representation
     │
     ▼
AI generates explanation
     │
     ▼
SSRL verifies structural grounding
     │
     ▼
Audited explanation
```

The design principle is:

> **AI is a worker, not an oracle.**

The current explanation verifier checks identifiers, relationships, references, and structural consistency.

It does **not** prove that an AI's semantic interpretation is universally correct.

That distinction is explicit in the architecture.

See [`AI LAYER/`](AI%20LAYER/README.md) and [`research/decisions/ADR-009-explainable-ai-external-agents.md`](research/decisions/ADR-009-explainable-ai-external-agents.md).

---

# Prototype

The current implementation is located under:

```text
prototype/ssrl/
```

The prototype is designed to remain lightweight and currently has a dependency-free core implementation.

Current capabilities include:

* deterministic source extraction
* semantic enrichment
* confidence handling
* semantic Q&A
* narrative generation
* CLI interface
* incremental watch mode
* MCP server
* micro-LLM hypothesis proposal
* explanation generation
* explanation verification
* deleted-symbol representation

Prototype documentation:

[`prototype/README.md`](prototype/README.md)

---

# Validation

SSRL is currently an **experimental research project**.

The prototype has already undergone preliminary automated validation, but the central research claim has not been treated as established.

A draft automated study compared source-only answers with SSRL-grounded answers against deterministic facts.

Current preliminary results:

| Condition     | Entity-F1 |
| ------------- | --------: |
| Baseline      |      0.15 |
| SSRL-grounded |      0.61 |

The SSRL-grounded condition achieved recall of **1.00** in that experiment.

An additional explanation-auditing battery included:

| Test                            | Result       |
| ------------------------------- | ------------ |
| Faithful explanations           | 3/3 passed   |
| Fabricated structural reference | 1/1 detected |

These results demonstrate that the prototype can perform the tested tasks.

They do **not** establish that SSRL improves developer comprehension in general.

The remaining validation work therefore focuses on external and human evaluation.

Detailed reports:

* [`prototype/REPORT-P9.md`](prototype/REPORT-P9.md)
* [`prototype/REPORT-P10.md`](prototype/REPORT-P10.md)

---

# Research status

| Component                        | Status        |
| -------------------------------- | ------------- |
| Vision & principles              | Complete      |
| Semantic model                   | Complete      |
| Requirements                     | Frozen v1.0   |
| Architecture                     | Implemented   |
| Position paper                   | Draft v0.3    |
| Prototype V1                     | Shipped       |
| Deterministic extraction         | Implemented   |
| Semantic hypotheses              | Implemented   |
| Q&A                              | Implemented   |
| Narrative                        | Implemented   |
| Watch / incremental updates      | Implemented   |
| MCP                              | Implemented   |
| Explanation verification         | Implemented   |
| Preliminary automated validation | Complete      |
| Human comprehension evaluation   | In progress   |
| Confidence calibration           | Open research |
| Broad language support           | Open research |

---

# Research questions

The project is primarily investigating five questions.

### RQ1 — Comprehension

Does a persistent semantic representation improve understanding of unfamiliar software compared with source-only workflows?

### RQ2 — Interaction

Which representations are most useful for software comprehension?

### RQ3 — Trust

Does explicit evidence and confidence reduce unsupported or misleading explanations?

### RQ4 — Semantic generation

Which semantic information can be derived deterministically, and where are probabilistic models necessary?

### RQ5 — Agent workflows

What does a persistent semantic representation provide beyond an AI agent using search, ASTs, LSPs, Git, and other development tools?

The fifth question is particularly important.

If a sufficiently capable coding agent can reconstruct the same information on demand with comparable accuracy and cost, the value proposition of a persistent representation becomes weaker.

SSRL therefore treats existing agent workflows as an important baseline rather than assuming the representation layer is inherently superior.

---

# Design principles

## 1. Code is the source of truth

SSRL is derived from software rather than becoming an independent source of truth.

## 2. Facts and hypotheses remain distinct

Interpretation must not silently become fact.

## 3. Claims require evidence

Semantic information should expose its supporting evidence.

## 4. Continuity is part of the design

The representation should evolve with the source code and make changes detectable.

## 5. Developer friction matters

If SSRL requires more effort than the workflow it is intended to improve, it fails the usability requirement.

## 6. Projections are views

Graph, Q&A, narrative, and other interfaces are projections of the representation.

## 7. AI is not authoritative

AI-generated interpretations remain interpretations.

## 8. Comprehension is the target

The purpose of the representation is not to maximize metadata.

It is to make software easier to understand correctly.

---

# Current limitations

SSRL is still experimental.

### Language coverage

The current deterministic fact layer is primarily implemented around Python. Language-agnostic operation remains a broader architectural goal rather than a fully demonstrated property.

### Semantic correctness

The verifier can establish structural grounding.

It cannot guarantee that a grounded explanation represents the correct semantic intent of the original developers.

### Confidence calibration

Confidence values should not currently be interpreted as calibrated probabilities of semantic truth.

Calibration remains an open research problem.

### Scale

The current prototype has not yet established its behavior across very large production repositories.

### Human evaluation

The strongest claim — improved developer comprehension — still requires controlled human evaluation and broader external testing.

---

# Repository structure

```text
SSRL/
├── README.md
├── HowToUse.md
├── roadmap.md
├── LICENSE
│
├── AI LAYER/
│   ├── README.md
│   └── MCP-CONNECT.md
│
├── .opencode/
│   └── skills/
│       └── ssrl/
│
├── docs/
│   ├── vision.md
│   ├── concepts.md
│   ├── requirements.md
│   ├── architecture.md
│   ├── related-work.md
│   └── projections/
│       └── graph.md
│
├── paper/
│   ├── SSRL-v0.2.md
│   └── SSRL-v0.3.md
│
├── research/
│   ├── plan.md
│   ├── literature/
│   ├── prior-art/
│   ├── discourse/
│   ├── probes/
│   └── decisions/
│
└── prototype/
    ├── README.md
    ├── BUILDLOG.md
    ├── REPORT-V1.md
    ├── REPORT-P7.md
    ├── REPORT-P8.md
    ├── REPORT-P9.md
    ├── REPORT-P10.md
    ├── ssrl/
    ├── lab/
    └── tests/
```

---

# Documentation

### Core concepts

[`docs/concepts.md`](docs/concepts.md)

Semantic entities, facts, hypotheses, confidence, evidence, and relationships.

### Architecture

[`docs/architecture.md`](docs/architecture.md)

Architectural decisions and system boundaries.

### Requirements

[`docs/requirements.md`](docs/requirements.md)

The specification and requirements used to guide implementation.

### Practical usage

[`HowToUse.md`](HowToUse.md)

Using SSRL with the prototype, projections, MCP, and AI agents.

### Research

[`research/plan.md`](research/plan.md)

Research questions, methodology, prior work, experiments, and decisions.

### Position paper

[`paper/SSRL-v0.3.md`](paper/SSRL-v0.3.md)

The current research position and theoretical foundation of SSRL.

---

# Experimental status

SSRL should currently be understood as a **research prototype**, not as a finished production technology.

The implementation demonstrates the proposed architecture and several of its mechanisms.

The central hypothesis remains under evaluation:

> **A persistent, evidence-backed semantic representation can reduce the cost of understanding unfamiliar software for humans and AI systems.**

The project is intentionally keeping this question open.

---

# Contributing

Technical feedback, experiments, criticism, related work, and alternative approaches are welcome.

In particular, useful contributions include:

* testing SSRL on real codebases
* comparing it against existing development workflows
* identifying false or misleading semantic interpretations
* proposing stronger evaluation methodologies
* identifying relevant prior work
* testing scalability
* challenging the semantic model
* identifying situations where SSRL provides no meaningful advantage

The project is currently more interested in **evidence than agreement**.

---

## License

MIT — © 2026 JGDEV
