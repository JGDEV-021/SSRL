# Phase 9 study — draft automated pass (`qwen3_0_6b`)

Corpus: `doc_rag` (31 files) · agent: `qwen3_0_6b` · 6 questions x 3 conditions.
Scoring: entity-level recall/precision/F1 against a deterministic gold standard computed
from SSRL facts. This is the ROUTINE draft (single model, single corpus,
automated proxy). The definitive study (multi-participant, human grading)
is planned in REPORT-P9. The 'layer' condition is the deterministic `ask`
projection — no LLM — included as the oracle reference.

## Aggregates (n=6)

| condition | F1 mean | recall mean | tokens prompt | tokens eval | elapsed_s |
| --- | --- | --- | --- | --- | --- |
| baseline (raw names + LLM) | 0.153 | 0.33 | 5344 | 3000 | 253.29 |
| ssrl (grounded facts + LLM) | 0.613 | 1.0 | 2631 | 949 | 65.81 |
| layer (deterministic `ask`, no LLM) | 0.315 | 0.303 | — | — | 0.01 |

## Ground truth (gold, from the layer)

- `who calls init_db` → callers of func::db::init_db: build, embed, index_scripts, purge, remove_project_scripts, search, stats
- `where is embed` → locations: embedder.py:88
- `which modules import db` → modules importing module::db: indexer, quality, retriever, scripts
- `list the entry points` → entry points (29): func::benchmark::main, func::chunker::iter_page_chunks, func::chunker::strip_markdown_links, func::context::search_for_context, func::data.frameworks.rbxutil.build_tests::on_modified, func::data.frameworks.rbxutil.build_tests::update_test_file, func::data.frameworks.react-lua.bin.run-benchmarks::details, func::data.frameworks.react-lua.bin.run-benchmarks::text, func::data.frameworks.react-lua.bin.run-benchmarks::title, func::data.frameworks.react-lua.bin.svg::child, func::data.frameworks.react-lua.bin.svg::display, func::data.frameworks.react-lua.bin.svg::layout, func::db::get_meta_int, func::db::purge, func::embedder::available, func::embedder::dim, func::embedder::encode, func::evidence::assess_requirement, func::expand::expand_query, func::expand::query_groups, func::ingest::ensure_llms_full, func::ingest::read_file, func::refapi::class_exists, func::refapi::clear_cache, func::refapi::search_properties, func::scripts::index_scripts, func::scripts::remove_project_scripts, func::trust::devforum_quality_boost, func::trust::reddit_quality_boost
- `what does the flow from search do` → flow flow::func::context::search_for_context steps (12): func::db::connect, func::db::get_meta, func::db::init_db, func::embedder::get_embedder, func::retriever::_api_query, func::retriever::_candidates_or_fallback, func::retriever::_cosine_scores, func::retriever::_index_exists, func::retriever::_minmax, func::retriever::search, func::textutil::clean_snippet, func::trust::authority
- `which files does indexer depend on` → deps of module::indexer: chunker, config, db, embedder, ingest, textutil

## Per-question results

### q1.baseline — who calls init_db
- score: recall 0.143 precision 0.011 f1 0.02
- tokens 890/500 · 42.728s · gold: ['build', 'embed', 'index_scripts', 'purge', 'remove_project_scripts', 'search', 'stats']
- answer: - __init__  
- __main__  
- __post_init__  
- _api_query  
- _backfill_embeddings  
- _build_index  
- _candidates  
- _candidates_or_fallback  
- _chunk_key  
- _chunk_member  
- _chunks_unchanged  
- _class_file  
- _classes_dir  
- _cmd_bench  
- _cmd_build  
- _cmd_context  

### q1.ssrl — who calls init_db
- score: recall 1.0 precision 0.7 f1 0.824
- tokens 187/52 · 5.469s · gold: ['build', 'embed', 'index_scripts', 'purge', 'remove_project_scripts', 'search', 'stats']
- answer: func::indexer::build  
func::indexer::embed  
func::indexer::purge  
func::indexer::stats  
func::retriever::search  
func::scripts::index_scripts  
func::scripts::remove_project_scripts
### q1.layer — who calls init_db
- score: recall 1.0 precision 0.875 f1 0.933
- tokens 0/0 · 0.001s · gold: ['build', 'embed', 'index_scripts', 'purge', 'remove_project_scripts', 'search', 'stats']
- answer: Callers of `init_db`: build, embed, stats, purge, search, index_scripts, remove_project_scripts (7 facts, confidence 1.0).
### q2.baseline — where is embed
- score: recall 1.0 precision 0.5 f1 0.667
- tokens 889/500 · 42.04s · gold: ['embedder']
- answer: - embed  
- embed  
- embedder.py  
- embed  
- embed  
- embedder.py  
- embed  
- embed  
- embedder.py  
- embed  
- embed  
- embedder.py  
- embed  
- embed  
- embedder.py  
- embed  
- embed  
- embedder.py  
- embed  
- embed  
- embedder.py  
- embed  
- embed  
- embedd
### q2.ssrl — where is embed
- score: recall 1.0 precision 0.25 f1 0.4
- tokens 158/49 · 4.984s · gold: ['embedder']
- answer: - {"node": "func::embedder::embed", "loc": "embedder.py:88"}  
- {"node": "func::indexer::embed", "loc": "indexer.py:414"}
### q2.layer — where is embed
- score: recall 0.0 precision 0.0 f1 0.0
- tokens 0/0 · 0.001s · gold: ['embedder']
- answer: Function `embed` defined at indexer.py:414 (confidence 1.0).
### q3.baseline — which modules import db
- score: recall 0.0 precision 0.0 f1 0.0
- tokens 890/500 · 42.229s · gold: ['indexer', 'quality', 'retriever', 'scripts']
- answer: -Chunk
-DocEmbedder
-Node
-Node
-Section
-WallyInfo
-WatchHandler
-Stats
-__init__
-__init__
-__init__
-__init__
-__init__
-__main__
-__post_init__
-__api_query
-__backfill_embeddings
-__build_index
-__candidates
-__candidates_or_fallback
-__chunk_key
-__chunk_member
-__chunks_un
### q3.ssrl — which modules import db
- score: recall 1.0 precision 0.333 f1 0.5
- tokens 309/84 · 6.252s · gold: ['indexer', 'quality', 'retriever', 'scripts']
- answer: - module::indexer
- module::chunker
- module::chunker
- module::config
- module::db
- module::embedder
- module::ingest
- module::textutil
- module::quality
- module::retriever
- module::expand
- module::expand
- module::textutil
- module::trust
- module::scripts
### q3.layer — which modules import db
- score: recall 0.0 precision 0.0 f1 0.0
- tokens 0/0 · 0.001s · gold: ['indexer', 'quality', 'retriever', 'scripts']
- answer: Module `db.py`: 0 class(es), 8 top-level function(s), 6 import(s).
Module docstring: doc_rag/db.py — Camada SQLite do índice RAG (doc_rag.db).

Schema:
    meta      — metadados globais (versão, último build, contagens)
    sources   — páginas indexadas (1 linha por arquivo .md d
### q4.baseline — list the entry points
- score: recall 0.172 precision 0.052 f1 0.079
- tokens 890/500 · 42.25s · gold: ['main', 'iter_page_chunks', 'strip_markdown_links', 'search_for_context', 'on_modified', 'update_test_file', 'details', 'text', 'title', 'child', 'display', 'layout', 'get_meta_int', 'purge', 'available', 'dim', 'encode', 'assess_requirement', 'expand_query', 'query_groups', 'ensure_llms_full', 'read_file', 'class_exists', 'clear_cache', 'search_properties', 'index_scripts', 'remove_project_scripts', 'devforum_quality_boost', 'reddit_quality_boost']
- answer: - Chunk
- DocEmbedder
- Node
- Node
- Section
- WallyInfo
- WatchHandler
- _Stats
- __init__
- __init__
- __init__
- __init__
- __init__.py
- __main__.py
- __post_init__
- _api_query
- _backfill_embeddings
- _build_index
- _candidates
- _candidates_or_fallback
- _chunk_key
- _chu
### q4.ssrl — list the entry points
- score: recall 1.0 precision 0.725 f1 0.841
- tokens 429/312 · 17.549s · gold: ['main', 'iter_page_chunks', 'strip_markdown_links', 'search_for_context', 'on_modified', 'update_test_file', 'details', 'text', 'title', 'child', 'display', 'layout', 'get_meta_int', 'purge', 'available', 'dim', 'encode', 'assess_requirement', 'expand_query', 'query_groups', 'ensure_llms_full', 'read_file', 'class_exists', 'clear_cache', 'search_properties', 'index_scripts', 'remove_project_scripts', 'devforum_quality_boost', 'reddit_quality_boost']
- answer: - func::benchmark::main  
- func::chunker::iter_page_chunks  
- func::chunker::strip_markdown_links  
- func::context::search_for_context  
- func::data.frameworks.rbxutil.build_tests::on_modified  
- func::data.frameworks.rbxutil.build_tests::update_test_file  
- func::data.fram
### q4.layer — list the entry points
- score: recall 0.483 precision 1.0 f1 0.651
- tokens 0/0 · 0.001s · gold: ['main', 'iter_page_chunks', 'strip_markdown_links', 'search_for_context', 'on_modified', 'update_test_file', 'details', 'text', 'title', 'child', 'display', 'layout', 'get_meta_int', 'purge', 'available', 'dim', 'encode', 'assess_requirement', 'expand_query', 'query_groups', 'ensure_llms_full', 'read_file', 'class_exists', 'clear_cache', 'search_properties', 'index_scripts', 'remove_project_scripts', 'devforum_quality_boost', 'reddit_quality_boost']
- answer: Entry points (no callers in repo): main, strip_markdown_links, iter_page_chunks, search_for_context, update_test_file, on_modified, text, title, details, child, layout, display, get_meta_int, purge, available.
### q5.baseline — what does the flow from search do
- score: recall 0.667 precision 0.087 f1 0.154
- tokens 893/500 · 42.183s · gold: ['connect', 'get_meta', 'init_db', 'get_embedder', '_api_query', '_candidates_or_fallback', '_cosine_scores', '_index_exists', '_minmax', 'search', 'clean_snippet', 'authority']
- answer: - __init__.py  
- __main__.py  
- _api_query  
- _backfill_embeddings  
- _build_index  
- _candidates  
- _candidates_or_fallback  
- _chunk_key  
- _chunk_member  
- _chunks_unchanged  
- _class_file  
- _classes_dir  
- _cmd_bench  
- _cmd_build  
- _cmd_context  
- _cmd_embed
### q5.ssrl — what does the flow from search do
- score: recall 1.0 precision 0.316 f1 0.48
- tokens 849/380 · 25.354s · gold: ['connect', 'get_meta', 'init_db', 'get_embedder', '_api_query', '_candidates_or_fallback', '_cosine_scores', '_index_exists', '_minmax', 'search', 'clean_snippet', 'authority']
- answer: - {"flow": "flow::func::context::search_for_context", "steps": ["func::db::connect", "func::db::get_meta", "func::db::init_db", "func::embedder::get_embedder", "func::retriever::_api_query", "func::retriever::_candidates_or_fallback", "func::retriever::_cosine_scores", "func::ret
### q5.layer — what does the flow from search do
- score: recall 0.0 precision 0.0 f1 0.0
- tokens 0/0 · 0.001s · gold: ['connect', 'get_meta', 'init_db', 'get_embedder', '_api_query', '_candidates_or_fallback', '_cosine_scores', '_index_exists', '_minmax', 'search', 'clean_snippet', 'authority']
- answer: 10 Flow hypotheses (calibrated confidence):
  - flow::func::benchmark::main conf=0.88 — strong hypothesis
  - flow::func::chunker::iter_page_chunks conf=0.88 — strong hypothesis
  - flow::func::context::search_for_context conf=0.88 — strong hypothesis
  - flow::func::data.framewo
### q6.baseline — which files does indexer depend on
- score: recall 0.0 precision 0.0 f1 0.0
- tokens 892/500 · 41.862s · gold: ['chunker', 'config', 'db', 'embedder', 'ingest', 'textutil']
- answer: - __init__.py
- __main__.py
- __init__
- __init__
- __init__
- __init__
- __init__
- __init__
- __init__
- __init__
- __init__
- __init__
- __init__
- __init__
- __init__
- __init__
- __init__
- __init__
- __init__
- __init__
- __init__
- __init__
- __init__
- __init__
- __init__
### q6.ssrl — which files does indexer depend on
- score: recall 1.0 precision 0.462 f1 0.632
- tokens 699/72 · 6.207s · gold: ['chunker', 'config', 'db', 'embedder', 'ingest', 'textutil']
- answer: - module::benchmark
- module::chunker
- module::cli
- module::config
- module::db
- module::embedder
- module::expand
- module::indexer
- module::ingest
- module::quality
- module::retriever
- module::textutil
- module::trust
### q6.layer — which files does indexer depend on
- score: recall 0.333 precision 0.286 f1 0.308
- tokens 0/0 · 0.001s · gold: ['chunker', 'config', 'db', 'embedder', 'ingest', 'textutil']
- answer: Module `indexer.py`: 0 class(es), 17 top-level function(s), 18 import(s).
Module docstring: doc_rag/indexer.py — Build/refresh do índice RAG.

Pipeline por página:
    ingest (creator-docs) → sha check → chunk_markdown → embed → upsert SQLite

Se o embedder não estiver disponível
