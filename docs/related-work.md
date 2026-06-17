# Related Work
## SSRL Literature Review & Prior Art

> This document surveys existing technologies, research areas, frameworks, and methodologies related to software understanding, software representation, knowledge extraction, and AI-assisted software engineering.
>
> SSRL does not attempt to replace these systems.
>
> Instead, SSRL aims to investigate whether a unified software knowledge representation layer can complement them.

---

# Introduction

Any proposal for a new software representation paradigm must be evaluated against existing research and industry practices.

Many of the ideas explored by SSRL already exist in partial form across different fields:

- Static Analysis
- Program Analysis
- Knowledge Graphs
- Software Architecture Recovery
- Code Intelligence
- Semantic Search
- AI-Assisted Development

The purpose of this document is to understand:

1. What already exists.
2. What problems are already solved.
3. What problems remain unsolved.
4. Where SSRL potentially fits.

---

# 1. Abstract Syntax Trees (AST)

## What It Is

An Abstract Syntax Tree (AST) represents source code as a hierarchical tree structure.

Example:

```lua
if money > 100 then
    vip = true
end
```

May become:

```text
IfStatement
├── Condition
│   └── money > 100
└── Assignment
    └── vip = true
```

---

## Strengths

- Deterministic
- Precise
- Language-aware
- Foundation of compilers

---

## Limitations

ASTs represent syntax.

They do not represent:

- Intent
- Business meaning
- Architecture
- Domain concepts

---

## SSRL Relationship

ASTs are expected to be one of the primary inputs of the SSRL Structural Layer.

---

# 2. Control Flow Graphs (CFG)

## What It Is

A Control Flow Graph models execution paths.

Example:

```text
Start
 ↓
Check Money
 ↓
VIP?
 ↓
End
```

---

## Strengths

- Models execution
- Useful for optimization
- Useful for static analysis

---

## Limitations

Does not explain:

- Why the flow exists
- Business purpose
- Architectural role

---

## SSRL Relationship

CFGs provide execution evidence for flow discovery.

---

# 3. Program Dependence Graphs (PDG)

## What It Is

Program Dependence Graphs represent:

- Control dependencies
- Data dependencies

within software systems.

---

## Example

```text
Money
 ↓
Condition
 ↓
VIP
```

---

## Strengths

- Precise dependency analysis
- Powerful static analysis foundation

---

## Limitations

Still operates at implementation level.

No semantic abstraction.

---

## SSRL Relationship

PDGs provide evidence for:

- Rule extraction
- Flow detection
- Dependency modeling

---

# 4. Code Property Graphs (CPG)

## What It Is

Code Property Graphs combine:

```text
AST
+
CFG
+
PDG
```

into a single graph.

---

## Examples

Tools:

- Joern
- CodeQL
- ShiftLeft

---

## Strengths

- Extremely powerful
- Excellent for security analysis
- Production proven

---

## Limitations

Focus remains primarily:

- Structural
- Security-oriented

rather than:

- Semantic
- Knowledge-oriented

---

## SSRL Relationship

CPGs are arguably the closest existing structural relative to SSRL.

However:

```text
CPG = Code Structure

SSRL = Software Knowledge
```

---

# 5. CodeQL

## What It Is

:contentReference[oaicite:0]{index=0}

CodeQL is GitHub's semantic code analysis engine.

It converts source code into a queryable database.

Developers can run queries such as:

```text
Find SQL injections
Find unsafe data flows
Find insecure API usage
```

---

## Strengths

- Mature ecosystem
- Strong security tooling
- Query-based analysis
- Large-scale adoption

---

## Limitations

Primarily focused on:

- Vulnerability discovery
- Static analysis

rather than:

- Knowledge representation
- Architectural understanding

---

## SSRL Relationship

CodeQL demonstrates the value of turning software into a queryable representation.

SSRL extends this concept toward software knowledge.

---

# 6. Software Architecture Recovery

## What It Is

Research field focused on reconstructing architecture from source code.

---

## Goals

Discover:

- Layers
- Components
- Services
- Boundaries

without documentation.

---

## Strengths

Useful for legacy systems.

---

## Limitations

Often stops at architecture diagrams.

Does not preserve semantic reasoning.

---

## SSRL Relationship

Architecture recovery becomes one subsystem inside SSRL.

---

# 7. Knowledge Graphs

## What It Is

Knowledge Graphs represent information through:

```text
Entities
Relationships
Properties
```

---

## Examples

Knowledge graph concepts power:

- Search engines
- Recommendation systems
- Enterprise knowledge systems

---

## Strengths

- Explainable
- Navigable
- Queryable

---

## Limitations

Require knowledge extraction.

Knowledge quality depends on extraction quality.

---

## SSRL Relationship

SSRL is fundamentally built upon knowledge graph principles.

---

# 8. Software Knowledge Graphs

## What It Is

Research area applying knowledge graphs directly to software systems.

---

## Examples

Represent:

- Files
- Classes
- APIs
- Dependencies

as graph entities.

---

## Strengths

Closer to SSRL than traditional analysis.

---

## Limitations

Most implementations remain structural.

Semantic intent remains limited.

---

## SSRL Relationship

Software Knowledge Graphs are likely one of the strongest academic foundations for SSRL.

---

# 9. Semantic Code Search

## What It Is

Search systems that understand meaning rather than exact text.

---

## Example

Query:

```text
Load player inventory
```

May retrieve:

```lua
RestorePlayerItems()
```

---

## Strengths

Developer productivity.

---

## Limitations

Usually retrieves code.

Does not construct software knowledge.

---

## SSRL Relationship

Semantic search may operate on top of SSRL graphs.

---

# 10. Vector Databases

## What It Is

Databases optimized for embeddings.

Examples:

- Qdrant
- Weaviate
- Milvus
- pgvector

---

## Strengths

Enable:

- Similarity search
- Clustering
- Retrieval

---

## Limitations

Poor explainability.

Embeddings alone do not expose relationships.

---

## SSRL Relationship

SSRL combines vectors with graph structures.

---

# 11. Retrieval-Augmented Generation (RAG)

## What It Is

RAG provides external context to language models.

---

## Pipeline

```text
Question
 ↓
Retrieve Documents
 ↓
LLM
 ↓
Answer
```

---

## Strengths

Improves context quality.

Reduces hallucinations.

---

## Limitations

Documents often remain unstructured.

Retrieval quality varies.

---

## SSRL Relationship

SSRL can serve as a structured retrieval source.

---

# 12. GraphRAG

## What It Is

GraphRAG extends RAG using graph structures.

---

## Pipeline

```text
Question
 ↓
Graph Retrieval
 ↓
Context Assembly
 ↓
LLM
 ↓
Answer
```

---

## Strengths

Captures relationships.

Improves context quality.

---

## Limitations

Most implementations assume a graph already exists.

They do not solve software understanding itself.

---

## SSRL Relationship

GraphRAG is one potential consumer of SSRL.

SSRL may generate the graph that GraphRAG uses.

---

# 13. Large Language Models for Code Understanding

## What It Is

Modern LLMs can:

- Explain code
- Summarize repositories
- Infer architecture
- Suggest intent

---

## Strengths

Flexible.

General-purpose.

---

## Limitations

Non-deterministic.

May hallucinate.

Knowledge is not persistent.

---

## SSRL Relationship

LLMs become semantic contributors rather than primary truth sources.

---

# 14. Domain-Driven Design (DDD)

## What It Is

Introduced by :contentReference[oaicite:1]{index=1}.

Focuses on modeling software around business domains.

---

## Concepts

- Entity
- Value Object
- Domain Event
- Aggregate
- Ubiquitous Language

---

## Strengths

Strong semantic modeling.

---

## Limitations

Requires human effort.

Not automatically extracted.

---

## SSRL Relationship

Many SSRL abstractions resemble DDD concepts.

However, SSRL attempts automatic discovery.

---

# 15. Repository Intelligence

## What It Is

Emerging field focused on understanding repositories holistically.

Includes:

- Architecture extraction
- Dependency analysis
- Knowledge extraction
- AI-assisted navigation

---

## Examples

Used by:

- GitHub Copilot Workspace
- Sourcegraph
- Cursor
- Repository analysis systems

---

## SSRL Relationship

Repository intelligence is one of the primary application domains of SSRL.

---

# Comparative Summary

| System | Structure | Semantics | Intent | Queryable | AI Ready |
|----------|----------|----------|----------|----------|----------|
| AST | ✅ | ❌ | ❌ | ❌ | ⚠️ |
| CFG | ✅ | ❌ | ❌ | ⚠️ | ⚠️ |
| PDG | ✅ | ❌ | ❌ | ⚠️ | ⚠️ |
| CPG | ✅ | ⚠️ | ❌ | ✅ | ⚠️ |
| CodeQL | ✅ | ⚠️ | ❌ | ✅ | ⚠️ |
| Knowledge Graphs | ⚠️ | ✅ | ⚠️ | ✅ | ✅ |
| Software Knowledge Graphs | ✅ | ⚠️ | ⚠️ | ✅ | ✅ |
| RAG | ❌ | ⚠️ | ❌ | ⚠️ | ✅ |
| GraphRAG | ⚠️ | ⚠️ | ❌ | ✅ | ✅ |
| LLMs | ⚠️ | ✅ | ⚠️ | ❌ | ✅ |
| SSRL (Proposed) | ✅ | ✅ | ✅ | ✅ | ✅ |

---

# Positioning of SSRL

SSRL does not attempt to replace:

- CodeQL
- Knowledge Graphs
- GraphRAG
- LLMs
- Software Analysis Tools

Instead, SSRL investigates whether software can be represented as structured, explainable knowledge that bridges:

```text
Code
+
Architecture
+
Semantics
+
Intent
+
AI Context
```

into a unified representation layer.

---

# Final Observation

Most existing systems answer:

> How does the software work?

SSRL investigates whether we can also answer:

> What knowledge does the software contain?

and

> Why does this software exist?

at scale.
