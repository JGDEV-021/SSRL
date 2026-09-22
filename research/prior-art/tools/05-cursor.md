# Cursor — Prior Art Note

> Research date: 2026-09-22 · Sources: cursor.com/blog/secure-codebase-indexing (2026-01), multiple 2026 teardowns (bito.ai guide, zzet.org/gortex analysis, codezup, architecturallyspeaking.substack, turbopuffer case study via zenml), deepwiki getcursor/docs.

## What it is
An AI-IDE (Anysphere) whose differentiators are **codebase-wide semantic search (`@Codebase`)** + **agent mode**. Billions of completions/day; >50% of Fortune 500 (per ZenML LLMOps database case study); 80M+ namespaces in turbopuffer.

## How the codebase index actually works (best-documented in the ecosystem)
- **Chunking**: tree-sitter AST parse → **syntactic chunks** (function bodies, classes, config blocks; ~500 tokens each; metadata = obfuscated file path + start/end lines + content hash). Merge sibling nodes until under the embedding-model token limit. Function-level units, not arbitrary 256-token slices.
- **Embedding**: proprietary, code-tuned embedding model (successor to OpenAI embeddings; trained on **agent-session traces**: an LLM ranks which content would have been most useful at each retrieval step, then the embedder is aligned to those rankings).
- **Storage**: vectors only (no plaintext) in **turbopuffer** (object-storage vector DB; namespace-per-codebase; active namespaces cached in memory/NVMe, idle ones on S3 — 20x cost cut, "1 Trillion+ vectors" claim). The client holds the only copy of raw source; the server returns **masked path + line range** and the local client reads the actual lines into context. Embeddings are cached by chunk content hash.
- **Freshness**: **Merkle tree** over the working tree (leaf = file hash; internal node = hash of children; root = overall fingerprint). ~5-min sync cadence; only changed subtrees re-embed. For a 50k-file workspace the hashes alone are ~3.2 MB; team-index reuse ("simhash" similarity) drops time-to-first-query from hours→seconds (median 7.87s→525ms).
- **Retrieval**: hybrid — semantic (vector) + **lexical/regex** index (sparse n-grams; the classic problem that pure embeddings can't do "find all `db.execute` with a string literal"). Cursor's own eval: semantic search + grep lifted agent accuracy **12.5%** avg (up to 23.5% on large codebases) vs grep alone.
- **Context-frugal reads**: the agent's `read_file` tool returns ~250 lines (max ~750) unless you edited/attached the file — a deliberate cost/latency tradeoff (distinct from the index).

## The critical limitation (independent teardowns agree)
> Embeddings store *similarity*, not *relationships*. The index has **no resolved edges** — it cannot answer "who calls `chargeCard`?", "what implements this interface?", "what breaks if I change this signature?". There is nothing to traverse; nearest-neighbor returns things that *look like* the query, possibly half a function (chunk-boundary split).

Also: dependency on cursor servers (no offline/air-gapped semantic search), non-retention (not E2E encryption — paths obfuscated, chunks in clear at embed time).

## Relevance to SSRL
- **Direct, current proof of the structural gap**: the most capable commercial codebase index is a similarity map. SSRL's *resolved fact graph* (who-calls-what, what-changes-break-what) is exactly what no embedding index can do (RQ-2 H2/H4; D-6 vector-not-sufficient).
- **Engineering innovations worth copying for W5**: Merkle-tree incremental freshness, content-hash embedding cache, function-level (not token) chunking, hybrid lexical+semantic search, obfuscated-path / client-holds-source data architecture.
- **Anti-pattern to avoid**: storing code on a 3rd-party service / non-landable design; SSRL's self-hostable layer avoids the governance blocker.

## Licensing
Proprietary SaaS; nothing reusable as components. Engineering/architecture is documented publicly (cursor.com/blog) → design reference only.