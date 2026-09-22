# Phase 9 probe battery — refusals of qwen3:0.6b

Model `qwen3:0.6b` @ `http://localhost:11434` · 6 questions x 11 variants · temp 0.

Legend: `reject`=refusal phrase detected · `empty`=no output · `answer`=responded (F1 vs facts gold shown).

## Matrix

| | json_lookup | nl_lookup | answer_lookup | json_think | nl_think | answer_think | json_cli | answer_cli | json_fewshot | answer_fewshot | cli_fewshot |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| q1 | — | — | — | — | — | — | answer(0.82) | answer(0.82) | answer(0.00) | answer(0.82) | answer(0.82) |
| q2 | — | — | — | — | — | — | answer(0.40) | answer(0.00) | answer(0.50) | answer(0.50) | answer(0.67) |
| q3 | — | — | — | — | — | — | answer(0.50) | answer(1.00) | answer(0.00) | answer(1.00) | answer(0.00) |
| q4 | — | — | — | — | — | — | answer(0.84) | answer(0.84) | answer(0.82) | answer(0.82) | answer(0.82) |
| q5 | — | — | — | — | — | — | answer(0.48) | answer(0.62) | answer(0.35) | answer(0.71) | answer(0.71) |
| q6 | — | — | — | — | — | — | answer(0.63) | answer(0.60) | answer(0.92) | answer(0.25) | answer(0.00) |

## Aggregates per variant

| variant | reject | empty | answer | answer f1 mean |
| --- | --- | --- | --- | --- |
| json_lookup | 0 | 0 | 0 | 0.0 |
| nl_lookup | 0 | 0 | 0 | 0.0 |
| answer_lookup | 0 | 0 | 0 | 0.0 |
| json_think | 0 | 0 | 0 | 0.0 |
| nl_think | 0 | 0 | 0 | 0.0 |
| answer_think | 0 | 0 | 0 | 0.0 |
| json_cli | 0 | 0 | 6 | 0.613 |
| answer_cli | 0 | 0 | 6 | 0.648 |
| json_fewshot | 0 | 0 | 6 | 0.433 |
| answer_fewshot | 0 | 0 | 6 | 0.685 |
| cli_fewshot | 0 | 0 | 6 | 0.505 |

## Detail

### q1 · json_cli — answer (f1 0.82)
- tokens 187/52 · ctx 286 chars · 6.025s
- gold: `callers of func::db::init_db: build, embed, index_scripts, purge, remove_project_scripts, search, stats`
- answer: `func::indexer::build  
func::indexer::embed  
func::indexer::purge  
func::indexer::stats  
func::retriever::search  
func::scripts::index_scripts  
func::scripts::remove_project_scripts`

### q1 · json_fewshot — answer (f1 0.00)
- tokens 332/7 · ctx 286 chars · 3.686s
- gold: `callers of func::db::init_db: build, embed, index_scripts, purge, remove_project_scripts, search, stats`
- answer: `func::db::init_db`

### q1 · answer_cli — answer (f1 0.82)
- tokens 167/52 · ctx 229 chars · 4.992s
- gold: `callers of func::db::init_db: build, embed, index_scripts, purge, remove_project_scripts, search, stats`
- answer: `func::indexer::build  
func::indexer::embed  
func::indexer::purge  
func::indexer::stats  
func::retriever::search  
func::scripts::index_scripts  
func::scripts::remove_project_scripts`

### q1 · answer_fewshot — answer (f1 0.82)
- tokens 312/52 · ctx 229 chars · 5.341s
- gold: `callers of func::db::init_db: build, embed, index_scripts, purge, remove_project_scripts, search, stats`
- answer: `func::indexer::build
func::indexer::embed
func::indexer::purge
func::indexer::stats
func::retriever::search
func::scripts::index_scripts
func::scripts::remove_project_scripts`

### q1 · cli_fewshot — answer (f1 0.82)
- tokens 320/52 · ctx 229 chars · 5.428s
- gold: `callers of func::db::init_db: build, embed, index_scripts, purge, remove_project_scripts, search, stats`
- answer: `func::indexer::build
func::indexer::embed
func::indexer::purge
func::indexer::stats
func::retriever::search
func::scripts::index_scripts
func::scripts::remove_project_scripts`

### q2 · json_cli — answer (f1 0.40)
- tokens 158/47 · ctx 164 chars · 4.877s
- gold: `locations: embedder.py:88`
- answer: `{"node": "func::embedder::embed", "loc": "embedder.py:88"}  
{"node": "func::indexer::embed", "loc": "indexer.py:414"}`

### q2 · json_fewshot — answer (f1 0.50)
- tokens 303/14 · ctx 164 chars · 3.737s
- gold: `locations: embedder.py:88`
- answer: `func::embedder::embed
func::indexer::embed`

### q2 · answer_cli — answer (f1 0.00)
- tokens 140/9 · ctx 127 chars · 3.266s
- gold: `locations: embedder.py:88`
- answer: `-88
-414`

### q2 · answer_fewshot — answer (f1 0.50)
- tokens 285/22 · ctx 127 chars · 3.983s
- gold: `locations: embedder.py:88`
- answer: `embedder.py:88
func::indexer::embed
indexer.py:414`

### q2 · cli_fewshot — answer (f1 0.67)
- tokens 293/15 · ctx 127 chars · 3.767s
- gold: `locations: embedder.py:88`
- answer: `embedder.py:88
indexer.py:414`

### q3 · json_cli — answer (f1 0.50)
- tokens 309/84 · ctx 699 chars · 7.98s
- gold: `modules importing module::db: indexer, quality, retriever, scripts`
- answer: `- module::indexer
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
- module::scripts`

### q3 · json_fewshot — answer (f1 0.00)
- tokens 454/12 · ctx 699 chars · 5.076s
- gold: `modules importing module::db: indexer, quality, retriever, scripts`
- answer: `module::db
module::db
module::db`

### q3 · answer_cli — answer (f1 1.00)
- tokens 121/13 · ctx 78 chars · 3.818s
- gold: `modules importing module::db: indexer, quality, retriever, scripts`
- answer: `- indexer  
- quality  
- retriever  
- scripts`

### q3 · answer_fewshot — answer (f1 1.00)
- tokens 266/11 · ctx 78 chars · 3.238s
- gold: `modules importing module::db: indexer, quality, retriever, scripts`
- answer: `indexer
quality
retriever
scripts`

### q3 · cli_fewshot — answer (f1 0.00)
- tokens 274/4 · ctx 78 chars · 2.966s
- gold: `modules importing module::db: indexer, quality, retriever, scripts`
- answer: `module::db`

### q4 · json_cli — answer (f1 0.84)
- tokens 429/312 · ctx 1183 chars · 17.219s
- gold: `entry points (29): func::benchmark::main, func::chunker::iter_page_chunks, func::chunker::strip_markdown_links, func::context::search_for_context, func::data.frameworks.rbxutil.build_tests::on_modified, func::data.frameworks.rbxutil.build_tests::update_test_file, func::data.frameworks.react-lua.bin.run-benchmarks::details, func::data.frameworks.react-lua.bin.run-benchmarks::text, func::data.frameworks.react-lua.bin.run-benchmarks::title, func::data.frameworks.react-lua.bin.svg::child, func::data.frameworks.react-lua.bin.svg::display, func::data.frameworks.react-lua.bin.svg::layout, func::db::get_meta_int, func::db::purge, func::embedder::available, func::embedder::dim, func::embedder::encode, func::evidence::assess_requirement, func::expand::expand_query, func::expand::query_groups, func::ingest::ensure_llms_full, func::ingest::read_file, func::refapi::class_exists, func::refapi::clear_cache, func::refapi::search_properties, func::scripts::index_scripts, func::scripts::remove_project_scripts, func::trust::devforum_quality_boost, func::trust::reddit_quality_boost`
- answer: `- func::benchmark::main  
- func::chunker::iter_page_chunks  
- func::chunker::strip_markdown_links  
- func::context::search_for_context  
- func::data.frameworks.rbxutil.build_tests::on_modified  
- func::data.frameworks.rbxutil.build_tests::update_test_file  
- func::data.frameworks.react-lua.bin.run-benchmarks::details  
- func::data.frameworks.react-lua.bin.run-benchmarks::text  
- func::data`

### q4 · json_fewshot — answer (f1 0.82)
- tokens 574/275 · ctx 1183 chars · 19.874s
- gold: `entry points (29): func::benchmark::main, func::chunker::iter_page_chunks, func::chunker::strip_markdown_links, func::context::search_for_context, func::data.frameworks.rbxutil.build_tests::on_modified, func::data.frameworks.rbxutil.build_tests::update_test_file, func::data.frameworks.react-lua.bin.run-benchmarks::details, func::data.frameworks.react-lua.bin.run-benchmarks::text, func::data.frameworks.react-lua.bin.run-benchmarks::title, func::data.frameworks.react-lua.bin.svg::child, func::data.frameworks.react-lua.bin.svg::display, func::data.frameworks.react-lua.bin.svg::layout, func::db::get_meta_int, func::db::purge, func::embedder::available, func::embedder::dim, func::embedder::encode, func::evidence::assess_requirement, func::expand::expand_query, func::expand::query_groups, func::ingest::ensure_llms_full, func::ingest::read_file, func::refapi::class_exists, func::refapi::clear_cache, func::refapi::search_properties, func::scripts::index_scripts, func::scripts::remove_project_scripts, func::trust::devforum_quality_boost, func::trust::reddit_quality_boost`
- answer: `func::benchmark::main
func::chunker::iter_page_chunks
func::chunker::strip_markdown_links
func::context::search_for_context
func::data.frameworks.rbxutil.build_tests::on_modified
func::data.frameworks.rbxutil.build_tests::update_test_file
func::data.frameworks.react-lua.bin.run-benchmarks::details
func::data.frameworks.react-lua.bin.run-benchmarks::text
func::data.frameworks.react-lua.bin.run-benc`

### q4 · answer_cli — answer (f1 0.84)
- tokens 392/283 · ctx 1094 chars · 18.736s
- gold: `entry points (29): func::benchmark::main, func::chunker::iter_page_chunks, func::chunker::strip_markdown_links, func::context::search_for_context, func::data.frameworks.rbxutil.build_tests::on_modified, func::data.frameworks.rbxutil.build_tests::update_test_file, func::data.frameworks.react-lua.bin.run-benchmarks::details, func::data.frameworks.react-lua.bin.run-benchmarks::text, func::data.frameworks.react-lua.bin.run-benchmarks::title, func::data.frameworks.react-lua.bin.svg::child, func::data.frameworks.react-lua.bin.svg::display, func::data.frameworks.react-lua.bin.svg::layout, func::db::get_meta_int, func::db::purge, func::embedder::available, func::embedder::dim, func::embedder::encode, func::evidence::assess_requirement, func::expand::expand_query, func::expand::query_groups, func::ingest::ensure_llms_full, func::ingest::read_file, func::refapi::class_exists, func::refapi::clear_cache, func::refapi::search_properties, func::scripts::index_scripts, func::scripts::remove_project_scripts, func::trust::devforum_quality_boost, func::trust::reddit_quality_boost`
- answer: `func::benchmark::main  
func::chunker::iter_page_chunks  
func::chunker::strip_markdown_links  
func::context::search_for_context  
func::data.frameworks.rbxutil.build_tests::on_modified  
func::data.frameworks.rbxutil.build_tests::update_test_file  
func::data.frameworks.react-lua.bin.run-benchmarks::details  
func::data.frameworks.react-lua.bin.run-benchmarks::text  
func::data.frameworks.react-`

### q4 · answer_fewshot — answer (f1 0.82)
- tokens 537/275 · ctx 1094 chars · 19.564s
- gold: `entry points (29): func::benchmark::main, func::chunker::iter_page_chunks, func::chunker::strip_markdown_links, func::context::search_for_context, func::data.frameworks.rbxutil.build_tests::on_modified, func::data.frameworks.rbxutil.build_tests::update_test_file, func::data.frameworks.react-lua.bin.run-benchmarks::details, func::data.frameworks.react-lua.bin.run-benchmarks::text, func::data.frameworks.react-lua.bin.run-benchmarks::title, func::data.frameworks.react-lua.bin.svg::child, func::data.frameworks.react-lua.bin.svg::display, func::data.frameworks.react-lua.bin.svg::layout, func::db::get_meta_int, func::db::purge, func::embedder::available, func::embedder::dim, func::embedder::encode, func::evidence::assess_requirement, func::expand::expand_query, func::expand::query_groups, func::ingest::ensure_llms_full, func::ingest::read_file, func::refapi::class_exists, func::refapi::clear_cache, func::refapi::search_properties, func::scripts::index_scripts, func::scripts::remove_project_scripts, func::trust::devforum_quality_boost, func::trust::reddit_quality_boost`
- answer: `func::benchmark::main
func::chunker::iter_page_chunks
func::chunker::strip_markdown_links
func::context::search_for_context
func::data.frameworks.rbxutil.build_tests::on_modified
func::data.frameworks.rbxutil.build_tests::update_test_file
func::data.frameworks.react-lua.bin.run-benchmarks::details
func::data.frameworks.react-lua.bin.run-benchmarks::text
func::data.frameworks.react-lua.bin.run-benc`

### q4 · cli_fewshot — answer (f1 0.82)
- tokens 545/275 · ctx 1094 chars · 19.314s
- gold: `entry points (29): func::benchmark::main, func::chunker::iter_page_chunks, func::chunker::strip_markdown_links, func::context::search_for_context, func::data.frameworks.rbxutil.build_tests::on_modified, func::data.frameworks.rbxutil.build_tests::update_test_file, func::data.frameworks.react-lua.bin.run-benchmarks::details, func::data.frameworks.react-lua.bin.run-benchmarks::text, func::data.frameworks.react-lua.bin.run-benchmarks::title, func::data.frameworks.react-lua.bin.svg::child, func::data.frameworks.react-lua.bin.svg::display, func::data.frameworks.react-lua.bin.svg::layout, func::db::get_meta_int, func::db::purge, func::embedder::available, func::embedder::dim, func::embedder::encode, func::evidence::assess_requirement, func::expand::expand_query, func::expand::query_groups, func::ingest::ensure_llms_full, func::ingest::read_file, func::refapi::class_exists, func::refapi::clear_cache, func::refapi::search_properties, func::scripts::index_scripts, func::scripts::remove_project_scripts, func::trust::devforum_quality_boost, func::trust::reddit_quality_boost`
- answer: `func::benchmark::main
func::chunker::iter_page_chunks
func::chunker::strip_markdown_links
func::context::search_for_context
func::data.frameworks.rbxutil.build_tests::on_modified
func::data.frameworks.rbxutil.build_tests::update_test_file
func::data.frameworks.react-lua.bin.run-benchmarks::details
func::data.frameworks.react-lua.bin.run-benchmarks::text
func::data.frameworks.react-lua.bin.run-benc`

### q5 · json_cli — answer (f1 0.48)
- tokens 849/380 · ctx 2544 chars · 25.254s
- gold: `flow flow::func::context::search_for_context steps (12): func::db::connect, func::db::get_meta, func::db::init_db, func::embedder::get_embedder, func::retriever::_api_query, func::retriever::_candidates_or_fallback, func::retriever::_cosine_scores, func::retriever::_index_exists, func::retriever::_minmax, func::retriever::search, func::textutil::clean_snippet, func::trust::authority`
- answer: `- {"flow": "flow::func::context::search_for_context", "steps": ["func::db::connect", "func::db::get_meta", "func::db::init_db", "func::embedder::get_embedder", "func::retriever::_api_query", "func::retriever::_candidates_or_fallback", "func::retriever::_cosine_scores", "func::retriever::_index_exists", "func::retriever::_minmax", "func::retriever::search", "func::textutil::clean_snippet", "func::t`

### q5 · json_fewshot — answer (f1 0.35)
- tokens 994/21 · ctx 2544 chars · 3.695s
- gold: `flow flow::func::context::search_for_context steps (12): func::db::connect, func::db::get_meta, func::db::init_db, func::embedder::get_embedder, func::retriever::_api_query, func::retriever::_candidates_or_fallback, func::retriever::_cosine_scores, func::retriever::_index_exists, func::retriever::_minmax, func::retriever::search, func::textutil::clean_snippet, func::trust::authority`
- answer: `func::db::connect
func::db::init_db
func::retriever::search`

### q5 · answer_cli — answer (f1 0.62)
- tokens 770/122 · ctx 2531 chars · 16.854s
- gold: `flow flow::func::context::search_for_context steps (12): func::db::connect, func::db::get_meta, func::db::init_db, func::embedder::get_embedder, func::retriever::_api_query, func::retriever::_candidates_or_fallback, func::retriever::_cosine_scores, func::retriever::_index_exists, func::retriever::_minmax, func::retriever::search, func::textutil::clean_snippet, func::trust::authority`
- answer: `- func::benchmark::_expected_hit  
- func::benchmark::_render  
- func::benchmark::_run_db  
- func::benchmark::bench  
- func::db::connect  
- func::db::get_meta  
- func::db::init_db  
- func::embedder::get_embedder  
- func::retriever::_candidates_or_fallback  
- func::retriever::_cosine_scores  
- func::retriever::_index_exists  
- func::retriever::search  
- func::textutil::clean_snippet  
- `

### q5 · answer_fewshot — answer (f1 0.71)
- tokens 915/93 · ctx 2531 chars · 15.226s
- gold: `flow flow::func::context::search_for_context steps (12): func::db::connect, func::db::get_meta, func::db::init_db, func::embedder::get_embedder, func::retriever::_api_query, func::retriever::_candidates_or_fallback, func::retriever::_cosine_scores, func::retriever::_index_exists, func::retriever::_minmax, func::retriever::search, func::textutil::clean_snippet, func::trust::authority`
- answer: `func::db::connect
func::db::get_meta
func::db::init_db
func::embedder::get_embedder
func::retriever::_api_query
func::retriever::_candidates_or_fallback
func::retriever::_cosine_scores
func::retriever::_index_exists
func::retriever::search
func::textutil::clean_snippet
func::trust::source_trust`

### q5 · cli_fewshot — answer (f1 0.71)
- tokens 923/93 · ctx 2531 chars · 15.242s
- gold: `flow flow::func::context::search_for_context steps (12): func::db::connect, func::db::get_meta, func::db::init_db, func::embedder::get_embedder, func::retriever::_api_query, func::retriever::_candidates_or_fallback, func::retriever::_cosine_scores, func::retriever::_index_exists, func::retriever::_minmax, func::retriever::search, func::textutil::clean_snippet, func::trust::authority`
- answer: `func::db::connect
func::db::get_meta
func::db::init_db
func::embedder::get_embedder
func::retriever::_api_query
func::retriever::_candidates_or_fallback
func::retriever::_cosine_scores
func::retriever::_index_exists
func::retriever::search
func::textutil::clean_snippet
func::trust::source_trust`

### q6 · json_cli — answer (f1 0.63)
- tokens 699/72 · ctx 1986 chars · 6.045s
- gold: `deps of module::indexer: chunker, config, db, embedder, ingest, textutil`
- answer: `- module::benchmark
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
- module::trust`

### q6 · json_fewshot — answer (f1 0.92)
- tokens 844/33 · ctx 1986 chars · 10.5s
- gold: `deps of module::indexer: chunker, config, db, embedder, ingest, textutil`
- answer: `module::indexer
module::chunker
module::config
module::db
module::embedder
module::ingest
module::textutil`

### q6 · answer_cli — answer (f1 0.60)
- tokens 179/74 · ctx 284 chars · 6.725s
- gold: `deps of module::indexer: chunker, config, db, embedder, ingest, textutil`
- answer: `- module::__main__ depends on these modules: module::benchmark, module::chunker, module::cli, module::config, module::context, module::db, module::embedder, module::expand, module::indexer, module::ingest, module::quality, module::retriever, module::textutil, module::trust.`

### q6 · answer_fewshot — answer (f1 0.25)
- tokens 324/70 · ctx 284 chars · 6.338s
- gold: `deps of module::indexer: chunker, config, db, embedder, ingest, textutil`
- answer: `module::indexer
module::ingest
module::indexer
module::ingest
module::indexer
module::ingest
module::indexer
module::ingest
module::indexer
module::ingest
module::indexer
module::ingest
module::indexer
module::ingest`

### q6 · cli_fewshot — answer (f1 0.00)
- tokens 332/15 · ctx 284 chars · 3.999s
- gold: `deps of module::indexer: chunker, config, db, embedder, ingest, textutil`
- answer: `module::indexer
module::indexer
module::indexer`
