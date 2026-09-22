# CodeQL — Prior Art Note

> Research date: 2026-09-22 · Sources: github/codeql-cli-binaries LICENSE.md; docs.github.com CodeQL docs; Visual Studio Marketplace; scancode LicenseDB.

## What it is
GitHub's **semantic code analysis engine**: turns source into a **CodeQL database** (relational representation of code — a "code-database"; AST + dataflow + type info), then lets users run **QL queries** (logical, SQL-like) over it to find classes of bugs/security issues, especially path queries (data flow from source to sink). The VS Code extension adds IntelliSense, running packs, model packs.

## How it works (relevance to SSRL's fact model)
- A CodeQL database is exactly a **deterministic extraction of code facts** — but its extraction goal is *control/dataflow for security*, not meaning. Precisely the "facts, no semantics" boundary SSRL draws.
- **Path queries** make the "evidence chain" concrete: a result is a *flow path* through the code, not just a location — a natural model for SSRL "confidence = well evidenced by a traceable chain" (RQ-3). CodeQL query packs are pre-compiled and reproducible ("identical results every time until you upgrade") — a good pattern for SSRL's deterministic fact queries.
- Model packs extend analysis to third-party frameworks by explicit modeling — an interesting analog for SSRL's external/hypothesis injection.

## Licensing (critical for SSRL)
- **Not OSI open source.** "GitHub CodeQL Terms and Conditions", per-user license.
- Allowed: **academic research**; demonstration; testing OSI-queries; on **open-source codebases** hosted/maintained **on GitHub.com** (incl. CI/CD).
- **Not allowed without GitHub Advanced Security license**: generating databases for automated analysis/CI/CD, or analyzing **non-open-source codebases**. No reverse-engineering, no hosted-service offering ("provide as a hosted solution for others" is prohibited), no redistribution.
- VS Code extension is MIT; the CLI/engine it runs is under the GitHub CodeQL Terms.

## Relevance to SSRL
- CodeQL is **not embeddable** in a product serving private codebases → confirms SSRL must be its own permissively-licensed fact layer (as architecture docs assume).
- Usable **under the academic-research clause** as a *validation source* (cross-check SSRL-derived facts on open repos) during research phases.
- Its QL path-query / flow-evidence model is a strong design precedent for SSRL's evidence/confidence provenance and deterministic query reproducibility.

## Constraints for W4 probes
- CLI not usable on Alpine (musl) Linux; requires glibc. Fine for W4 on Windows/macOS.
- On non-GitHub OSS or any private repo, research use is fine only per academic-research clause — prefer the OSS-on-GitHub path for legality.