# Graph Projection (Candidate)

- Version: 0.2
- Status: Candidate — NOT the product

> The graph is **one projection** of the SSRL layer, not the product (see [`../concepts.md`](../concepts.md), §4). This schema is a first draft to be validated or adjusted by the research phase. It exists so the "what does software look like as a graph" hypothesis is concrete enough to test — and to discard if a better primary projection emerges.

---

## 1. Framing

The graph answers: *"show me everything and how it connects."* It is strong for navigation and dependency questions. It is weak at intent and narrative. That asymmetry is why it is a candidate projection, not the default.

Formally, `G = (V, E)`:

- `V` — nodes (software entities)
- `E` — directed edges (relationships)
- Every node/edge carries identity, type, properties, and (for hypotheses) confidence + evidence.

---

## 2. Design principles specific to the projection

1. Facts and hypotheses occupy different, labeled categories.
2. Everything traces back to a code location.
3. Facts carry `confidence = 1.0`; hypotheses carry a computed probability.
4. The graph is always derived from code, never authoritative.

---

## 3. Node model (candidate)

```json
{
  "id": "node_001",
  "type": "Function",
  "name": "LoadInventory",
  "description": "Loads player inventory",
  "confidence": 1.0,
  "evidence": [],
  "metadata": {}
}
```

### Candidate node types

**Structural:** Repository, Package, Module, Class, Interface, Function, Event, ExternalDependency.

**Semantic:** Service, Rule, Flow, Intent, DomainConcept.

## 4. Edge model (candidate)

```json
{
  "id": "edge_001",
  "source": "function_load_inventory",
  "target": "function_get_profile",
  "relationship": "CALLS",
  "confidence": 1.0,
  "metadata": {}
}
```

### Candidate relationship types

| Relationship | Meaning |
| --- | --- |
| `CONTAINS` | parent-child (Repository → Module) |
| `IMPORTS` | module imports module |
| `CALLS` | function invokes function |
| `TRIGGERS` | event activates handler |
| `DEPENDS_ON` | component depends on component |
| `IMPLEMENTS` | class/service implements contract |
| `USES` | generic usage (function → entity) |
| `READS` / `WRITES` | reads/writes a state or entity |
| `MODIFIES` | changes state |
| `CREATES` / `DESTROYS` | creates/removes entity |
| `PARTICIPATES_IN` | component participates in a flow |
| `SUPPORTS_INTENT` | implementation supports a semantic intent |
| `RELATED_TO` | fallback semantic relation |

> Some of these edges (READS, WRITES, MODIFIES) require data-flow analysis — a cost decision for research (architecture D-4).

---

## 5. Confidence & evidence in the graph

- **Facts:** `confidence: 1.0` — e.g., `IMPORTS`, `CALLS`, `CONTAINS`.
- **Hypotheses:** probabilistic — e.g., `Flow`, `Intent`, `DomainConcept` (e.g., `confidence: 0.74`, with `evidence[]`).

Evidence model:

```json
{
  "type": "NamingPattern",
  "source": "InventoryService",
  "weight": 0.82
}
```

Possible evidence sources: parser/AST, call graph, documentation, comments, git history, embedding similarity, LLM proposal, human annotation.

---

## 6. JSON Schemas (draft)

### Node

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SSRLNode",
  "type": "object",
  "required": ["id", "type", "name"],
  "properties": {
    "id": { "type": "string" },
    "type": { "type": "string" },
    "name": { "type": "string" },
    "description": { "type": "string" },
    "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
    "evidence": { "type": "array" },
    "metadata": { "type": "object" }
  }
}
```

### Edge

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SSRLEdge",
  "type": "object",
  "required": ["id", "source", "target", "relationship"],
  "properties": {
    "id": { "type": "string" },
    "source": { "type": "string" },
    "target": { "type": "string" },
    "relationship": { "type": "string" },
    "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
    "evidence": { "type": "array" },
    "metadata": { "type": "object" }
  }
}
```

---

## 7. Versioning (candidate)

```json
{
  "graph_version": "0.2",
  "repository_version": "commit_hash",
  "generated_at": "timestamp"
}
```

Enables drift detection and historical comparison.

---

## 8. What stays open

- Storage technology (embedded files? SQLite? graph DB?) — architecture D-3.
- Whether the graph is a runtime surface at all, or only an intermediate model for another primary projection.
- Whether node/edge taxonomies survive contact with a real validation corpus.