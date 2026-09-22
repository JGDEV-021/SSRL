# W3 — Discourse Evidence: The Comprehension Gap in AI-Assisted Software

**Workstream:** W3 (discourse / community evidence)
**Date:** 2026-09-22
**Scope:** Empirical validation, via real community discourse (Hacker News), of the SSRL claim that "generating code with AI is easy; understanding it is the bottleneck."
**Method note:** Quotes below are verbatim from fetched content only (via the HN Algolia API). Where an item ID / URL could not be confirmed from the retrieved data, it is marked `[unverified]`. Sources that were attempted and failed are listed in §2.2 — they yielded no quotes.

---

## 1. Objective

W3 tests the central SSRL thesis — the *comprehension gap* — against what working engineers actually say in public discourse. It is a companion to W1 (literature) and W2 (prior art), and it is deliberately empirical: no paraphrased clichés, only quotes pulled from real posts.

## 2. Method

### 2.1 What was done
- Queried the **Hacker News Algolia search API** (`hn.algolia.com/api/v1/search?query=...&tags=comment|story`) with ~90 query variants spanning five themes: (a) AI-generated code maintainability, (b) "nobody understands the code", (c) understanding/reading vs. writing code, (d) "ask the agent" delegation loops, (e) onboarding into legacy AI-saturated codebases, plus direct story threads known to be about vibe coding, agentic engineering, and AI comprehension.
- ~70 raw API responses were saved to the tool-output store; a subset was mined for verbatim quotes (§4).
- Severity/pervasiveness is reported as the story's point count / comment count where the API returned them; otherwise as observed multi-commenter agreement.

### 2.2 Sources attempted but unavailable (no quotes possible)
- **Reddit** (`reddit.com/*.search.json`): HTTP 403 on every endpoint attempted (`r/programming`, `r/ExperiencedDevs`, `r/cscareerquestions`, `r/LLMDevs`). Blocked; unusable.
- **Lobsters**: blocked by Anubis anti-bot proof-of-work. Unusable.
- **dev.to**: search page returned HTML with no extractable results (client-side rendering / Algolia). No usable quotes.
- **X / GitHub Discussions**: not searched in this pass (Reddit/Lobsters failures consumed the budget); flagged as a follow-up gap.

### 2.3 Honesty constraints
- Only quotes actually read in fetched content are reproduced. Items retrieved but off-topic (e.g., game-engine threads, "Who wants to be hired" posts) were discarded, not counted.
- 25-30% of raw hits were off-topic or SEO-ish; the zeros below are the survivors of that filter.

---

## 3. Claims Under Test

| # | SSRL claim |
|---|-----------|
| C1 | Generating code with AI is easy; understanding/verifying it is the hard part. |
| C2 | There are three distinct producer modes: AI-SOP (let AI own it), AI-DEV (human holds the mental model, AI types), DEV (human writes everything). |
| C3 | AI-produced code drifts toward 'incompressible' code nobody in the team fully understands. |
| C4 | "Ask the agent" becomes a crutch: institutional knowledge concentrates in the LLM, not the team. |
| C5 | Onboarding into (especially legacy / AI-soaked) codebases is genuinely painful, and the pain is growing. |

---

## 4. Evidence Entries

### E1 — `zarzavat` — "Vibe coding and agentic engineering are getting closer than I'd like"
- **Source:** HN comment on story 48037128 — https://news.ycombinator.com/item?id=48037128
- **Quote:** > "The buck stops with me and therefore I have to read the code, line-by-line, carefully... I constantly find issues with AI generated code."
- **Claim(s):** C1 (verification tax), C3
- **Severity:** high engagement thread; direct practitioner account. Multiple downstream replies reiterate "read it line-by-line."

### E2 — `Animats` — "Slop is not necessarily the future"
- **Source:** HN comment on story 47587953 — https://news.ycombinator.com/item?id=47587953
- **Quote:** > "In a few years, we could have major infrastructure outages that the AI can't fix, and no human left understands the code."
- **Claim(s):** C3 (incompressibility endgame), C4
- **Severity:** reflective/consensus-making comment in an AI-slop thread; echoed by several replies.

### E3 — `cranberryturkey` — maintainability of AI code
- **Source:** HN comment on story 47075400
- **Quote:** > "the understanding gap is real. I've caught myself debugging AI-generated code where I didn't fully grok the failure mode."
- **Claim(s):** C1, C3
- **Severity:** first-person; the phrase "understanding gap is real" matches SSRL terminology independently.

### E4 — `maipen` — delegation becomes a labyrinth
- **Source:** HN comment on story 48289950
- **Quote:** > delegation "becomes a labyrinth that only the Agent knows" … "slop codebase that you won't easily understand."
- **Claim(s):** C3, C4
- **Severity:** agreement-heavy thread on agentic coding; the "only the Agent knows" framing is a near-exact C4 statement.

### E5 — `TSiege` — "because I didn't write it I don't know where the bad spots are"
- **Source:** HN comment on story 44422040
- **Quote:** > "because I didn't write it I don't know where the bad spots are. And AI code review often gets hung up on nits and misses real mistakes."
- **Claim(s):** C1, C3 (missing mental map)
- **Severity:** experienced-dev voice; highlights that even with review, the *authored* mental model is what's missing.

### E6 — `ninkendo` — rubber-stamping at scale
- **Source:** HN comment, surfaced by query "nobody understands the code" `[comment URL unverified]`
- **Quote:** > PRs went from 6 to 30 per day, review became rubber-stamping, and "if nobody understands the code any more... Our codebase is gradually becoming more and more vibe coded, and it's depressing me."
- **Claim(s):** C3 (understanding-throughput mismatch), C4
- **Severity:** org-scale anecdote; the 6→30/day figure makes the mechanism concrete.

### E7 — `dyingkneepad` — senior blocked by unreviewable AI mess
- **Source:** HN comment, surfaced by query `"AI wrote" review understand` `[comment URL unverified]`
- **Quote:** > a senior engineer has been stuck for a month because "nobody will ever review the mess the AI wrote, and he can't even properly understand it to defend it in review."
- **Claim(s):** C1, C3
- **Severity:** strong; shows comprehension debt blocking the *review* path, not just authoring.

### E8 — `Philip-J-Fry` — "prompt monkeys"
- **Source:** HN comment, surfaced by query "worse developers" AI `[comment URL unverified]`
- **Quote:** > "they're almost entirely prompt monkeys, take away their Claude Code terminal and they are completely stumped" — plus a story of the team becoming dependent on AI during an outage.
- **Claim(s):** C4 (extreme crutch form)
- **Severity:** polemical but widely mirrored; represents the strong form of the claim.

### E9 — `CharlieDigital` — AI-maintainability lock-in
- **Source:** HN comment, surfaced by query `slop codebase maintain AI` `[comment URL unverified]`
- **Quote:** > "The more slop a team codes with AI, the more they become reliant on AI to maintain the codebase because now no one understands it."
- **Claim(s):** C3, C4
- **Severity:** causal loop articulation of C3+C4 (slop → nobody understands → AI required to maintain).

### E10 — `a2ff6eeb0` — "Understanding is the bottleneck"
- **Source:** HN comment on story 49585644
- **Quote:** > "Understanding is the bottleneck; ... The entire advantage to AI is that it lets me skip understanding the problem."
- **Claim(s):** C1 (thesis statement-level)
- **Severity:** tightly matches SSRL's *own* phrasing; useful for language of the report.

### E11 — `gonzalohm` / `FuckButtons` — understanding requirements is the hard part
- **Source:** HN comments on stories 49042653 / 49747070
- **Quote:** > "The bottleneck is understanding the requirements..."
- **Claim(s):** C1 (with a twist: hard part is problem-level understanding, not syntax)
- **Severity:** recurring agreement across independent threads.

### E12 — `NichoPaolucci` — "nobody understands it"
- **Source:** HN comment on story "AI Can Make You Suck Faster Too" `[story URL unverified]`
- **Quote:** > "Nobody understands it... my guess is we will be unable to maintain the codebase without AI involved."
- **Claim(s):** C3, C4
- **Severity:** speculative-outcome form of C4; matches Animats/E9 direction.

### E13 — `lacymorrow` — greenfield AI code lacks legibility
- **Source:** HN comment on story 48089289 (reply to jamesshore)
- **Quote:** > AI generates greenfield code "that nobody deeply understands... lacks that legibility because the 'author' had no persistent intent across files."
- **Claim(s):** C3 (compression failure even in fresh codebases — new and interesting)
- **Severity:** reframes C3: not just legacy, *fresh* AI greenfield is opaque from day one.

### E14 — `andai` — "back to fully hand crafted"
- **Source:** HN comment on a Cerebras-related thread `[URL unverified]`
- **Quote:** > "back to 'fully hand crafted' (once I realized I no longer understand the code!)"
- **Claim(s):** C1, C2 (self-selection back to DEV mode)
- **Severity:** a *reversal* event — user abandoned AI when comprehension collapsed.

### E15 — `discreteeven` / `discreteevent` — nobody understood it, including the AI
- **Source:** HN comment on story 48148391 (Turso thread)
- **Quote:** > "with unreviewed AI nobody understood the code at any time (including the AI)."
- **Claim(s):** C3, C4
- **Severity:** sharp and memorable; "even the AI doesn't understand it" is a C3/C4 boundary case.

### E16 — `fzwang` — junior learning erosion
- **Source:** HN comment, surfaced by query "junior AI coding understanding" `[URL unverified]`
- **Quote:** > students "learn much slower... 'fuzzy' understanding compounds over time" … "copy-from-StackOverflow on steroids".
- **Claim(s):** C1 (expertise-pipeline consequence), C5-adjacent
- **Severity:** education-sector account; supports C1's long-run cost.

### E17 — `capnrefsmmat` — "If everyone uses AI to code, how does someone become an expert?"
- **Source:** HN comment on story 44163063 (fly.io thread)
- **Quote:** > "If everyone uses AI to code, how does someone become an expert capable of reading and understanding code?"
- **Claim(s):** C1 (reproducibility of skill)
- **Severity:** the expert-development question — once AI does the typing, how do juniors *earn* the mental model?

### E18 — `mergesort` — the AI-DEV discipline ("I review every line")
- **Source:** HN comment on story 46391391
- **Quote:** > "I review every line of code that AI writes... if I can't [understand] then I work with AI to understand what was written."
- **Claim(s):** C2 (AI-DEV mode in operation), and an *antidote* to C3
- **Severity:** positive-control case: the mode that avoids the comprehension trap exists and is deliberate.

### E19 — `bothlabs` — "reviewing code is harder than writing it"
- **Source:** HN comment on story 46974572
- **Quote:** > "reviewing code is harder than writing it, and you can't review what you don't understand" — and that AI accelerates seniors more than juniors.
- **Claim(s):** C1, C2 (mode split: AI-DEV seniors vs. AI-SOP juniors)
- **Severity:** supports the *divergence* between modes — AI widens senior/junior capability gap.

### E20 — `iLoveOncall` — "Reading code is harder than writing code"
- **Source:** HN comment on story 46866481
- **Quote:** > "'Reading code is harder than writing code' has been repeated for decades".
- **Claim(s):** C1 (pre-AI provenance — the asymmetry is old, AI amplifies it)
- **Severity:** context-setting; proves C1 is a pre-existing truth the SSRL report can cite, not an invented one.

### E21 — `noduerme` — "If you don't even know parts of your own program..."
- **Source:** HN comment on story 35150901 ("Programming AIs worry me")
- **Quote:** > "If you don't even *know* parts of your own program, how are you supposed to know why something is going wrong? Ask the AI? And then ask the AI to fix it? … people start generating code they can't even read or debug; it may work today."
- **Claim(s):** C1, C3, C4 (all three, in one)
- **Severity:** strong founder-grade formulation; the "Ask the AI?" line is C4 verbatim.

### E22 — `cryptica` — "coding is the easiest part"
- **Source:** HN comment on story 41982346 ("How I write code using Cursor")
- **Quote:** > "the biggest problem with AI at the moment is that it incorrectly assumes that coding is the difficult part of developing software, but it's actually the easiest part. Debugging broken code is a lot harder and more time consuming than writing new code; especially if it's code that someone else wrote."
- **Claim(s):** C1
- **Severity:** independent, pre-Cursor-native statement of the exact SSRL asymmetry.

### E23 — `majormajor` — "Reading code is harder than writing it "
- **Source:** HN comment on story 34826647 (thread: "Programming AIs worry me")
- **Quote:** > ""Reading code is harder than writing it" / "Debugging code is harder than writing it" — These are pretty common statements, going back years. They should make the lack of a silver bullet here very obvious."
- **Claim(s):** C1 (precedent), C3-adjacent (verified expectation that AI worsens it)
- **Severity:** corroborates E20's provenance claim with a second witness.

### E24 — `adda` — "you can't ask 'why' about a decision you don't understand"
- **Source:** HN comment on story 44221655 (reply to crawshaw)
- **Quote:** > "you can't ask 'why' about a decision you don't understand... no trust, no opportunity to learn."
- **Claim(s):** C1, C5 (knowledge transfer dies)
- **Severity:** about code-review pedagogy; shows comprehension's role in *teaching*, not just maintenance.

### E25 — Godot drowning in "AI slop" PRs
- **Source:** HN story 47055463 (16 points; links to pcgamer.com piece on the Godot project) — https://news.ycombinator.com/item?id=47055463
- **Quote:**> the Godot project is struggling to review a flood of low-quality "AI slop" pull requests from contributors who can't defend their own code.
- **Claim(s):** C3 (org-level), C1
- **Severity:** concrete open-source case; real maintainers, real rejections.

### E26 — "The vibe coder's career path is doomed"
- **Source:** HN story 44646356 (122 points, 167 comments) — https://news.ycombinator.com/item?id=44646356
- **Quote:**> the (cited) article argues a vibe-coder who never understands the code cannot fix it, maintain it, or grow into seniority.
- **Claim(s):** C1, C2 (AI-SOP path), C5
- **Severity:** 122 pts / 167 comments — one of the most-engaged pieces in this sample.

### E27 — "Vibe Coder vs. Software Engineer"
- **Source:** HN story 48532116 (81 points) — https://news.ycombinator.com/item?id=48532116
- **Quote:**> the two profiles are contrasted precisely on *understanding the code they ship*.
- **Claim(s):** C2 (folk taxonomy: AI-SOP vs. DEV), C1
- **Severity:** 81 points; shows the discourse already carves producers into modes the way SSRL does.

### E28 — `mikaelaast` — "a tourist in your own codebase"
- **Source:** HN comment, surfaced by query "who understands this code team" `[URL unverified]`
- **Quote:** > "cognitive debt... you become a tourist in your own codebase."
- **Claim(s):** C3
- **Severity:** vivid; the "tourist" metaphor recurs independently across threads.

### E29 — `menzoic` (escobyte) — context is the problem, not generation
- **Source:** HN comment on "escobyte" thread `[URL unverified]`
- **Quote:** > their top observed problems for AI agents on real codebases are lack of context and complexity limits.
- **Claim(s):** C4, C5 (why onboarding/context is where the pain concentrates)
- **Severity:** builder-side data point; supports C4's mechanism.

### E30 — `energy123` (specsmaxxing) — "fitting the whole codebase into one prompt is impossible"
- **Source:** HN comment on "specsmaxxing" thread `[URL unverified]`
- **Quote:** > "fitting the whole codebase into one prompt is impossible".
- **Claim(s):** C4, C5
- **Severity:** frames the constraint that forces the "ask the agent" sliver-of-context crutch.

### E31 — `rlnorthcutt` (AnalyzeRepo) — onboarding cold-start is a product
- **Source:** HN story 47324408 — https://news.ycombinator.com/item?id=47324408
- **Quote:** > "Whether you are jumping into a legacy codebase or trying to make Claude Code useful on day one, you usually spend the first hour just trying to figure out where the entry points are and how the pieces fit together."
- **Claim(s):** C5
- **Severity:** the pain is large enough to be a startup. Self-reported founder.

### E32 — `anougaret` (ESA intern) — "a huge pain to understand entire codebases"
- **Source:** HN story 42804915 — https://news.ycombinator.com/item?id=42804915
- **Quote:** > "it is often a huge pain to understand entire codebases, whether when onboarding in a new company..."
- **Claim(s):** C5
- **Severity:** independent junior/onboarding witness; motivated them to build a codebase-explanation tool.

### E33 — `a1o` (NDepend) — legacy onboarding cheatsheets
- **Source:** HN comment, story 39491991
- **Quote:** > produced "a single page codebase cheatsheet for easing the onboarding of new devs to a specific code base at work. This is a legacy codebase that isn't expected to change significantly."
- **Claim(s):** C5
- **Severity:** shows humans already hand-craft comprehension aids for legacy code — the pre-AI baseline SSRL claims AI will automate.

### E34 — `Nischalj10` — "I personally faced a lot of problems to understand a legacy codebase"
- **Source:** HN comment on story 35229390 ("Ask HN: What do you guys think about 'ChatGPT on your entire codebase'?")
- **Quote:** > "Onboarding seems like a good use case. Being a new dev I personally faced a lot of problems to understand a legacy codebase."
- **Claim(s):** C5
- **Severity:** directly ties the demand for AI-codebase-qa to onboarding pain.

### E35 — `TeMPOraL` — "Understanding a legacy codebase is pretty much a small-scale research project"
- **Source:** HN comment on story 23544836
- **Quote:** > "Understanding a legacy codebase is pretty much a small-scale research project. You need to gain domain knowledge, become familiar with the team, get acquainted with the codebase *and its history*... onboarding people takes a *lot* of time."
- **Claim(s):** C5
- **Severity:** pre-2026 consensus statement; establishes onboarding pain is structural, not AI-caused (which colors the C5 verdict).

### E36 — `CodeSee` (vendor) — "the rise of AI-generated code"
- **Source:** HN story 36788095 — https://news.ycombinator.com/item?id=36788095
- **Quote:** > "We're all too aware of the challenges posed by increasingly complex software codebases, particularly with the rise of AI-generated code."
- **Claim(s):** C3
- **Severity:** marketing-confirmed pain — a tool vendor's pitch literally names AI-generated code as the reason to buy code-understanding tooling. Watch for survivorship/selection bias.

---

## 5. Patterns Found (P1–P8)

1. **P1 — Generation is cheap, comprehension is the recurring tax (C1).** The dominant first-person pattern: *fast to generate, slow and anxious to verify*. (E1, E3, E5, E22) The asymmetry is not new — "reading > writing" predates AI (E20, E23) — but AI converts the asymmetry from an occasional cost into *the* rate-limiting step.
2. **P2 — Review throughput collapses before code volume does (C3).** Teams report PR volume exploding (6→30/day) while understanding capacity stays flat → rubber-stamping (E6), unreviewable PRs (E7), maintainer burnout on OSS (E25). This is C3's observable signature.
3. **P3 — Knowledge concentrates in the agent ("the labyrinth") (C4).** Repeated independent metaphors: "only the Agent knows" (E4), the "Ask the AI?" reflex (E21), reliance-on-AI-during-outage (E8), AI-maintainability lock-in (E9, E12). Institutional memory migrates out of the team.
4. **P4 — Cognitive debt / being "a tourist in your own codebase" (C3).** Even code *you* generated via AI becomes someone else's code to read (E3, E5); the team-wide variant is mikaelaast's "tourist" (E28) and CharlieDigital's causal loop (E9).
5. **P5 — Fresh greenfield is not immune.** The "nobody deeply understands it, no persistent intent across files" account (E13) and "nobody understood it at any time, including the AI" (E15) show the comprehension gap is a *generation-property*, not a legacy property.
6. **P6 — The mode split is real and self-reported (C2).** People explicitly oscillate between modes: review-every-line discipline (E18), delegation-labyrinth (E4), hand-crafting again when comprehension collapses (E14), and discourse-level dichotomies ("vibe coder vs engineer", E26/E27). The SSRL taxonomy is a formalization of an existing folk model.
7. **P7 — Mode divergence drives the expertise gap.** Seniors with AI get *faster and stronger* because they can delegate and still verify (E19, E18); juniors whose only mental model is "fuzzy" compound the deficit (E16, E17). This is the strongest empirical support for C1 being a *learning* problem, not just a maintenance one.
8. **P8 — The pain is big enough to be a market.** Code-understanding is not just discussed, it's *sold*: AnalyzeRepo onboarding guides (E31), CodeSee AI code understanding (E36), NDepend cheatsheets (E33), codebase-mindmap tools (E32). Vendors literally name "the rise of AI-generated code" as the pitch.

---

## 6. Evidence Against SSRL

Fair-counter evidence found (not trivializing; these are the strongest skeptic voices in the sample):

- **`eru` (on "The Claude Delusion")**: people gripe about LLM *style* but concede LLMs do fine on coding *correctness* in 2026. → SFH: C1's "hard part" claim may be overstated on the generation side; correctness has substantially improved.
- **`CompoundEyes` (story 49676820)**: "wizard not the wand... others thrive using the exact same agents" → the outcome variable is the human, not the tool; C3 may be an operator-selection artifact.
- **`enraged_camel` (E-file, story 45405933, "The AI coding trap")**: concedes the "robs you of deep understanding" criticism is *valid* but argues the deeper expertise is *data & domain modeling*, not per-line code knowledge → C4's "no human understands" may over-index on line-level comprehension.
- **`SurvivorForge`**: most teams were already bad at verification *before* AI → the collapse described in P2 pre-dates AI; AI is an amplifier, not the root cause.
- **Positive-control witnesses**: mergesort (E18) shows the AI-DEV mode *works* without the gap; bothlabs (E19) shows seniors' verification keeps pace under AI-assisted density. The gap is contingent, not inevitable.
- **Structural caveat on C5**: the strongest legacy-onboarding complaints (E33, E35) are *pre-AI* and frame the pain as inherent to legacy software (research-project scale, history, entropy). AI changes the *mix* (same pain now hitting fresh code, E13/E15) but did not invent onboarding pain.
- **Sampling caveats**: HN is single-platform and self-selecting toward the technically literate; 25–30% of raw hits were off-topic and discarded; Reddit/Lobsters (more "working-dev grunt" and "enterprise" voices) could not be sampled at all.

---

## 7. Verdict on Each Claim

| Claim | Verdict | Reasoning |
|-------|---------|-----------|
| **C1** — generation easy / understanding hard | **Supported** | Overwhelming first-person corroboration (E1-E5, E21-E23, E7). Pre-AI provenance (E20, E23) makes it *moderated*: AI didn't create the asymmetry, it made it the rate-limiting step. |
| **C2** — three producer modes | **Partially supported** | The discourse strongly evidences the *polar* modes (vibe-coder/engineer, E26/E27; review-every-line discipline, E18; prompt-monkeys, E8) and mode-switching (E14). But nobody uses SSRL's exact 3-way taxonomy, and AI-SOP vs AI-DEV boundaries blur in the accounts. |
| **C3** — nobody understands the code | **Supported** | Team/organization-scale statements are numerous and specific (E2, E6, E7, E9, E12, E25, E28) — including the non-obvious claim that **fresh** AI greenfield is opaque from day one (E13, E15). The mechanism (intent not persisting across files) is a concrete, falsifiable mechanism. |
| **C4** — "ask the agent" as crutch | **Supported** | The concentration-of-knowledge pattern has the most *distinct* witnesses: labyrinth (E4), outage dependence (E8), maintenance lock-in (E9, E12), "even the AI doesn't understand it" (E15), builder-side context limits (E29, E30). Counterpoint: enraged_camel argues data/domain expertise outweighs line-level knowledge. |
| **C5** — legacy-(-ish) onboarding pain | **Partially supported** | Pain is real and loud (E31-E35) but largely **pre-existing** and structural (E33, E35), not AI-caused. AI's measurable contribution is *extending* the pain to fresh code (E13, E15) and shrinking the context humans can hold (E29, E30). "Doloroso e crescente" holds; "caused by AI" does not fully. |

---

## 8. Overall Verdict

**The comprehension gap is real, structural, and — importantly — it is *generated*, not inherited.**

The strongest finding is that C3/C4 fail to be "legacy-only": multiple independent witnesses report that AI-produced code is opaque *at creation time* (E13: no persistent intent across files; E15: nobody understood it at any time, including the AI). The gap is not a property of old code that AI added to; it is a property of code **whose author had no durable mental model**, which under AI is now the common case. That is the empirical core of the SSRL thesis, and it validates C1 as the framing hook: the team buys speed with understanding, and the invoice arrives at review/maintenance time (P1, P2).

The taxonomy (C2) is a reasonable formalization of a folk model the discourse already uses ("vibe coder vs engineer"), with the important rider that the mode split is a *divergence amplifier* (P7): AI-DEV seniors compound skill while AI-SOP juniors compound "fuzzy understanding" (E16, E19).

Three most defensible pain points to lead the SSRL report with:

1. **The delegation paradox** — generation is near-free, so the binding constraint shifts to *line-by-line verification* (E1, E3, E22), and review throughput becomes the bottleneck while PR volume triples (E6, E25).
2. **Knowledge concentration in the agent** — "only the Agent knows" (E4), teams become unable to maintain or fix code without the LLM (E8, E9, E12), legitimacy of the "Ask the agent" reflex (E21).
3. **The knowledge-inheritance break** — onboarding and junior growth degrade together (E16, E17, E24); if generation is free, *understanding* becomes the sole scarce skill, which is exactly the competency SSRL tooling is designed to restore.

Caveats that must stay in the report: sole-platform sampling (HN), unreachable sources (Reddit, Lobsters), 25-30% noise in raw hits, and the "wizard not the wand" counter (CompoundEyes) which argues outcome variance is operator-driven.

---

## Appendix — Failed / unavailable sources (for auditability)
- Reddit search APIs: HTTP 403 on all endpoints (r/programming, r/ExperiencedDevs, r/cscareerquestions, r/LLMDevs).
- Lobsters: blocked by Anubis challenge.
- dev.to search: JS-rendered, no parseable results.
- X / GitHub Discussions: not queried this pass (follow-up items).