# SSRL Architecture
## Technical Architecture Specification (v0.1)

> This document describes the physical architecture of SSRL and the complete lifecycle of software knowledge extraction, enrichment, storage, and retrieval.

---

# 1. Overview

SSRL is designed as a multi-stage knowledge extraction pipeline.

The system transforms source code into structured software knowledge through a sequence of deterministic and probabilistic processing layers.

High-level flow:

```text
Source Code
    ↓
Parser Layer
    ↓
Structural Graph Builder
    ↓
Vector Layer
    ↓
Semantic Engine
    ↓
Knowledge Storage
    ↓
Query Engine
    ↓
Humans / AI / Tools
```

---

# 2. Design Goals

The architecture must:

- Remain language-agnostic.
- Support incremental updates.
- Scale to large repositories.
- Separate facts from hypotheses.
- Support both humans and AI systems.
- Preserve traceability.
- Allow confidence-based reasoning.

---

# 3. Core Pipeline

```text
Repository
    ↓
Parser
    ↓
Structural Extraction
    ↓
Graph Builder
    ↓
Knowledge Graph
    ↓
Vector Layer
    ↓
Semantic Engine
    ↓
Semantic Graph
    ↓
Storage Layer
    ↓
Query Engine
    ↓
Consumers
```

---

# 4. Parser Layer

## Purpose

Convert source code into deterministic structural representations.

This layer performs no semantic inference.

It only extracts facts.

---

## Inputs

Examples:

```text
Lua
Python
JavaScript
TypeScript
Go
Java
C#
Rust
```

---

## Outputs

Examples:

```json
{
  "type": "function",
  "name": "LoadInventory",
  "file": "InventoryService.lua"
}
```

---

## Responsibilities

Extract:

- Files
- Modules
- Classes
- Functions
- Interfaces
- Imports
- Exports
- Events
- Variables
- Constants

---

## Future

Each language may have its own parser adapter:

```text
ParserAdapter
├── LuaAdapter
├── PythonAdapter
├── JavaAdapter
├── RustAdapter
└── ...
```

---

# 5. Structural Graph Builder

## Purpose

Transform parser output into a deterministic software graph.

---

## Input

```json
{
  "function": "LoadInventory",
  "calls": [
    "GetProfile",
    "LoadItems"
  ]
}
```

---

## Output

```text
LoadInventory
    ↓
GetProfile

LoadInventory
    ↓
LoadItems
```

---

## Generated Relationships

### Calls

```text
Function A
    ↓
calls
    ↓
Function B
```

---

### Imports

```text
Module A
    ↓
imports
    ↓
Module B
```

---

### Event Triggers

```text
Event
    ↓
triggers
    ↓
Handler
```

---

### Dependencies

```text
Service A
    ↓
depends_on
    ↓
Service B
```

---

## Result

Structural Knowledge Graph.

This graph contains only verifiable facts.

---

# 6. Vector Layer

## Purpose

Create semantic representations of graph elements.

---

## Why?

Graphs are excellent for relationships.

Vectors are excellent for meaning.

SSRL combines both.

---

## Input

Graph nodes:

```text
InventoryService
PurchaseHandler
PlayerProfile
SaveProfile
```

---

## Embedding Generation

Possible sources:

- Node names
- Comments
- Documentation
- Function signatures
- Structural context
- Call patterns

---

## Output

```json
{
  "node": "InventoryService",
  "embedding": [0.13, -0.22, ...]
}
```

---

## Benefits

Supports:

- Semantic similarity
- Clustering
- Search
- Retrieval
- AI context generation

---

# 7. Semantic Engine

## Purpose

Generate semantic hypotheses from structural evidence.

---

## Inputs

### Graph

```text
Player
Inventory
Purchase
Currency
```

### Vectors

Embeddings generated previously.

---

## Semantic Sources

### Structural Patterns

Example:

```text
Purchase
    ↓
Currency
    ↓
Inventory
```

May indicate:

```text
Purchase System
```

---

### Naming Patterns

Example:

```text
InventoryService
InventoryManager
InventoryController
```

---

### Documentation

Example:

```text
Handles player inventory persistence.
```

---

### LLM Analysis

The LLM never becomes the source of truth.

It only proposes hypotheses.

---

## Outputs

```yaml
Hypothesis:
  Inventory Management System

Confidence:
  0.87
```

---

## Important Principle

Facts and hypotheses remain separate.

Never:

```text
Hypothesis → Fact
```

Always:

```text
Fact → Hypothesis
```

---

# 8. Knowledge Storage Layer

## Purpose

Persist SSRL knowledge.

---

## Storage Types

### Graph Database

Stores:

- Nodes
- Edges
- Relationships

Examples:

```text
Neo4j
Memgraph
ArangoDB
```

---

### Vector Database

Stores:

- Embeddings
- Similarity indexes

Examples:

```text
Qdrant
Weaviate
Milvus
pgvector
```

---

### Metadata Store

Stores:

- Confidence
- Versions
- Statistics
- Analysis metadata

Examples:

```text
PostgreSQL
SQLite
```

---

# 9. Query Engine

## Purpose

Provide a unified interface for knowledge retrieval.

---

## Example Questions

### Human Questions

```text
What happens when a player joins?
```

```text
Which systems depend on Inventory?
```

```text
Which components interact with payments?
```

---

### AI Questions

```text
Generate architecture summary.
```

```text
Explain the onboarding flow.
```

```text
Find potential architectural bottlenecks.
```

---

## Query Pipeline

```text
Question
    ↓
Intent Detection
    ↓
Graph Retrieval
    ↓
Vector Retrieval
    ↓
Semantic Context
    ↓
Response
```

---

# 10. Incremental Update Engine

## Problem

Rebuilding everything after every change does not scale.

---

## Proposed Flow

```text
Code Change
    ↓
Affected Nodes
    ↓
Affected Edges
    ↓
Affected Semantic Region
    ↓
Partial Regeneration
```

---

## Example

```text
InventoryService.lua modified
```

Only reprocess:

```text
InventoryService

LoadInventory

SaveInventory

Related Flows
```

Not the entire repository.

---

# 11. Consumers

## Human Developers

Use SSRL to:

- Understand systems
- Navigate architecture
- Onboard faster
- Audit dependencies

---

## AI Systems

Use SSRL to:

- Retrieve context
- Understand architecture
- Generate summaries
- Explain behavior

---

## IDE Plugins

Potential integrations:

- VSCode
- Roblox Studio
- JetBrains
- Neovim

---

## CI/CD

Potential usage:

```text
Pull Request
    ↓
SSRL Analysis
    ↓
Architecture Impact Report
```

---

# 12. Reference Architecture

```text
                    ┌───────────────┐
                    │ Source Code   │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Parser Layer  │
                    └───────┬───────┘
                            │
                            ▼
               ┌────────────────────────┐
               │ Structural Graph Builder│
               └───────────┬────────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ Knowledge Graph     │
                └───────┬─────────────┘
                        │
                        ▼
                ┌─────────────────────┐
                │ Vector Layer        │
                └───────┬─────────────┘
                        │
                        ▼
                ┌─────────────────────┐
                │ Semantic Engine     │
                └───────┬─────────────┘
                        │
                        ▼
                ┌─────────────────────┐
                │ Storage Layer       │
                └───────┬─────────────┘
                        │
                        ▼
                ┌─────────────────────┐
                │ Query Engine        │
                └───────┬─────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
    Humans            AI            Tooling
```

---

# Architecture Philosophy

> Source code stores implementation.
>
> SSRL stores knowledge.
>
> Knowledge must remain derivable, traceable, and explainable.
