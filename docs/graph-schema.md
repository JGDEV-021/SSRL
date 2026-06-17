# SSRL Graph Schema
## Formal Graph Definition & JSON Schema Specification (v0.1)

> This document defines the canonical graph structure used by SSRL.
>
> The SSRL graph is the foundational representation layer responsible for storing software knowledge in a machine-readable, human-auditable format.

---

# 1. Introduction

SSRL represents software as a directed knowledge graph.

A graph consists of:

```text
Nodes
+
Edges
+
Metadata
```

---

## Graph Model

Formally:

```math
G = (V, E)
```

Where:

```math
V = Set of Nodes
```

```math
E = Set of Edges
```

---

Each node may contain:

```text
Identity
Type
Properties
Confidence
Evidence
Metadata
```

Each edge may contain:

```text
Source
Target
Relationship
Confidence
Evidence
Metadata
```

---

# 2. Design Principles

## Principle 1

Facts and hypotheses must be separated.

---

Facts:

```text
Function Exists
Module Imports Module
Function Calls Function
```

---

Hypotheses:

```text
Authentication Flow
Inventory System
Purchase Validation Intent
```

---

## Principle 2

Everything must be traceable.

Every node and edge must reference its origin.

---

## Principle 3

Confidence is optional.

Facts:

```json
{
  "confidence": 1.0
}
```

Hypotheses:

```json
{
  "confidence": 0.82
}
```

---

# 3. Node Model

## Canonical Structure

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

---

# 4. Node Types

---

## Repository

Represents an entire software repository.

Example:

```text
JG-CODE
```

---

## Package

Represents a package.

Example:

```text
InventoryPackage
```

---

## Module

Represents a module or file.

Example:

```text
InventoryService.lua
```

---

## Class

Represents a class.

Example:

```text
InventoryManager
```

---

## Function

Represents a function.

Example:

```text
LoadInventory()
```

---

## Interface

Represents a contract.

Example:

```text
IInventoryService
```

---

## Event

Represents a software event.

Example:

```text
PlayerJoined
```

---

## Entity

Represents a domain object.

Example:

```text
Player
Inventory
Item
Currency
```

---

## Service

Represents a service layer component.

Example:

```text
PurchaseService
```

---

## Rule

Represents business logic.

Example:

```text
Money > 100
```

---

## Flow

Represents a software process.

Example:

```text
Player Join Flow
```

---

## Intent

Represents semantic purpose.

Example:

```text
Inventory Synchronization
```

---

## DomainConcept

Represents abstract business knowledge.

Example:

```text
Economy
Trading
Persistence
```

---

## ExternalDependency

Represents third-party dependencies.

Example:

```text
DataStoreService
Stripe
Redis
```

---

# 5. Node JSON Schema

## Base Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",

  "title": "SSRLNode",

  "type": "object",

  "required": [
    "id",
    "type",
    "name"
  ],

  "properties": {
    "id": {
      "type": "string"
    },

    "type": {
      "type": "string"
    },

    "name": {
      "type": "string"
    },

    "description": {
      "type": "string"
    },

    "confidence": {
      "type": "number",
      "minimum": 0,
      "maximum": 1
    },

    "evidence": {
      "type": "array"
    },

    "metadata": {
      "type": "object"
    }
  }
}
```

---

# 6. Edge Model

## Canonical Structure

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

---

# 7. Relationship Types

---

## CALLS

Function invokes another function.

```text
LoadInventory
    ↓
CALLS
    ↓
GetProfile
```

---

## IMPORTS

Module imports another module.

```text
InventoryService
    ↓
IMPORTS
    ↓
ProfileService
```

---

## DEPENDS_ON

Component depends on another.

```text
InventoryService
    ↓
DEPENDS_ON
    ↓
Database
```

---

## TRIGGERS

Event activates a handler.

```text
PlayerJoined
    ↓
TRIGGERS
    ↓
LoadInventory
```

---

## CONTAINS

Parent-child relationship.

```text
Repository
    ↓
CONTAINS
    ↓
Module
```

---

## IMPLEMENTS

Implementation relationship.

```text
InventoryService
    ↓
IMPLEMENTS
    ↓
IInventoryService
```

---

## USES

Generic usage relationship.

```text
Function
    ↓
USES
    ↓
Entity
```

---

## MODIFIES

Changes state.

```text
PurchaseService
    ↓
MODIFIES
    ↓
Inventory
```

---

## READS

Reads state.

```text
ProfileLoader
    ↓
READS
    ↓
Profile
```

---

## WRITES

Writes state.

```text
SaveProfile
    ↓
WRITES
    ↓
Profile
```

---

## CREATES

Creates entity.

```text
Shop
    ↓
CREATES
    ↓
Purchase
```

---

## DESTROYS

Removes entity.

```text
Inventory
    ↓
DESTROYS
    ↓
Item
```

---

## PARTICIPATES_IN

Links components to flows.

```text
LoadInventory
    ↓
PARTICIPATES_IN
    ↓
Player Join Flow
```

---

## SUPPORTS_INTENT

Links implementation to semantic intent.

```text
PurchaseService
    ↓
SUPPORTS_INTENT
    ↓
Purchase Validation
```

---

## RELATED_TO

Fallback semantic relationship.

```text
Inventory
    ↓
RELATED_TO
    ↓
Currency
```

---

# 8. Edge JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",

  "title": "SSRLEdge",

  "type": "object",

  "required": [
    "id",
    "source",
    "target",
    "relationship"
  ],

  "properties": {
    "id": {
      "type": "string"
    },

    "source": {
      "type": "string"
    },

    "target": {
      "type": "string"
    },

    "relationship": {
      "type": "string"
    },

    "confidence": {
      "type": "number",
      "minimum": 0,
      "maximum": 1
    },

    "evidence": {
      "type": "array"
    },

    "metadata": {
      "type": "object"
    }
  }
}
```

---

# 9. Evidence Model

Evidence explains WHY a node or edge exists.

---

Example:

```json
{
  "type": "NamingPattern",

  "source": "InventoryService",

  "weight": 0.82
}
```

---

Possible Evidence Sources:

```text
Parser
AST
Call Graph
Documentation
Comments
Git History
LLM Analysis
Embedding Similarity
Human Annotation
```

---

# 10. Confidence Model

## Facts

Generated by deterministic analysis.

```json
{
  "confidence": 1.0
}
```

Examples:

```text
CALLS
IMPORTS
CONTAINS
IMPLEMENTS
```

---

## Hypotheses

Generated by semantic inference.

```json
{
  "confidence": 0.74
}
```

Examples:

```text
Intent
DomainConcept
Flow Detection
```

---

# 11. Graph Versioning

Every graph snapshot must contain:

```json
{
  "graph_version": "0.1",

  "repository_version": "commit_hash",

  "generated_at": "timestamp"
}
```

---

This enables:

```text
Architecture Drift Detection
Historical Analysis
Graph Comparison
Semantic Evolution
```

---

# 12. Future Extensions

Planned node types:

```text
TestCase
APIEndpoint
DatabaseTable
Queue
Message
Microservice
Agent
Workflow
```

---

Planned edge types:

```text
AUTHORIZES
VALIDATES
ENCRYPTS
OBSERVES
MONITORS
PUBLISHES
SUBSCRIBES
```

---

# Canonical Principle

> Source code stores implementation.
>
> The SSRL graph stores software knowledge.
>
> Every node and edge must remain derivable,
> explainable,
> auditable,
> and versionable.
