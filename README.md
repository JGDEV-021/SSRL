# SSRL — Semantic Software Representation Layer

> **The semantic layer between software and understanding.**

[![Status](https://img.shields.io/badge/status-research%20%2F%20pre--implementation-orange)]()
[![Version](https://img.shields.io/badge/version-1.0-blue)]()
[![License](https://img.shields.io/badge/license-TBD-lightgrey)]()

We solved code generation.

**SSRL asks the next question: how do we preserve understanding?**

---

## TL;DR

SSRL (Semantic Software Representation Layer) é uma camada semântica construída sobre código-fonte que transforma software em um **grafo de conhecimento consultável, versionado e auditável**.

**Objetivo:**
- Preservar conhecimento arquitetural
- Melhorar compreensão de sistemas grandes
- Permitir raciocínio por IA com rastreabilidade
- Reduzir dependência de conhecimento tribal

**Input:** Código-fonte
**Output:** Grafo semântico versionado e auditável, com confiança explícita em cada hipótese

```
Code
 │
 ▼
AST / CFG / Call Graph
 │
 ▼
Software Graph
 │
 ▼
Semantic Enrichment
 │
 ▼
Knowledge Layer
 │
 ▼
Humans + AI Agents
```

---

## O problema em uma frase

```
Custo de Produção de Código  <<  Custo de Compreensão de Código
```

LLMs geram software mais rápido do que qualquer equipe consegue compreendê-lo, auditá-lo ou confiar nele. O SSRL é a camada de abstração proposta para resolver isso — não mais documentação manual, não mais código, mas uma representação semântica derivada e contínua.

```
Era Tradicional              Era da IA

Code                         Code
 ↓                            ↓
Human                        SSRL
                               ↓
                              Human
                               ↓
                              Agent
```

Veja a especificação completa, motivação detalhada e fundamentação teórica no **[paper de pesquisa](paper/SSRL-v0.1.md)**.

---

## Exemplo real

Antes (código sem contexto):

```python
def purchase_item(player, item):
    inventory.add(player, item)
    currency.deduct(player, item.price)
    ledger.record(player, item)
```

Depois (nó SSRL gerado a partir desse código):

```json
{
  "id": "PurchaseService",
  "type": "Function",
  "hypotheses": [
    { "concept": "Commerce", "confidence": 0.95 },
    { "concept": "Billing", "confidence": 0.81 }
  ],
  "dependencies": ["InventoryService", "CurrencyService", "LedgerService"],
  "risk": ["Financial"]
}
```

Uma única função deixa de ser apenas texto e passa a ser um **nó consultável**, com conceito de negócio, dependências e risco explícitos — rastreável até a linha de código que o originou.

---

## Como funciona (resumo)

1. **Parse code** — extração estrutural determinística (AST, CFG, call graph)
2. **Build structural graph** — unificação dos fatos em um grafo único
3. **Generate semantic hypotheses** — inferência probabilística de conceitos
4. **Calculate confidence** — consenso ponderado entre fontes de evidência
5. **Store semantic knowledge** — consolidação versionada
6. **Query** — humanos e agentes consultam o grafo, não o código bruto

Detalhamento completo de cada etapa em [`docs/architecture.md`](docs/architecture.md).

---

## Quando você precisa do SSRL

Se a resposta para qualquer uma destas perguntas hoje é **"pergunta para o agente"** ou **"ninguém sabe, vamos ler o código"**, existe uma lacuna de representação de conhecimento que o SSRL foi desenhado para preencher:

- Esse fluxo faz sentido?
- Que sistema depende disso?
- Isso quebra conformidade?
- Isso afeta faturamento?
- Isso cria risco de segurança?
- Isso está alinhado com a arquitetura?

## Query examples

```
FIND services
WHERE concept = "Billing"
```

```
What systems are affected if UserService fails?

↓

Billing
Inventory
Notifications
```

---

## Comparação com soluções existentes

| Sistema | Entende estrutura | Entende semântica | Versionado | Auditável |
|---|---|---|---|---|
| CodeQL / Semgrep | ✓ | ✗ | ✗ | Parcial |
| Sourcegraph / OpenGrok | ✓ | ✗ | ✗ | ✗ |
| Neo4j / Knowledge Graphs tradicionais | Parcial | ✗ | Parcial | ✗ |
| RAG para código | Parcial | Parcial | ✗ | ✗ |
| MCPs / Cursor / Claude Code / Codex | Parcial | Parcial | ✗ | ✗ |
| **SSRL** | ✓ | ✓ | ✓ | ✓ |

Análise detalhada de cada comparação em [`docs/related-work.md`](docs/related-work.md).

## Why SSRL is not just another Software Knowledge Graph

A objeção mais óbvia que um pesquisador faria é: *"isso é só um Knowledge Graph para código."*

Não é, por três razões estruturais:

1. **Separação explícita entre fato e hipótese.** Knowledge Graphs tradicionais tratam tudo como verdade estabelecida. O SSRL trata fatos estruturais (determinísticos) e hipóteses semânticas (probabilísticas) como categorias epistemológicas diferentes, nunca misturadas sem rótulo.
2. **Confiança como cidadã de primeira classe.** Toda hipótese carrega confiança, origem, método de extração e evidência. Não existe afirmação semântica "nua" no grafo.
3. **Regeneração incremental como requisito de design, não otimização posterior.** O grafo é projetado desde o início para sincronizar continuamente com um código-fonte em mudança constante — não para ser construído uma vez e ficar obsoleto, como a maioria dos KGs de código existentes.

Um Knowledge Graph responde "o que existe". O SSRL responde "o que existe, o que isso provavelmente significa, com que confiança, e por quê" — e nunca confunde as duas coisas.

---

## Non-goals

SSRL will not:

- Replace source code
- Replace static analyzers (CodeQL, Semgrep, etc.)
- Guarantee semantic correctness
- Eliminate human review
- Become a programming language

---

## Research Questions

- **RQ1:** Can semantic knowledge improve software comprehension?
- **RQ2:** Can confidence scoring reduce hallucinations in AI-assisted code reasoning?
- **RQ3:** Can SSRL reduce onboarding time for new engineers?

Hipóteses, metodologia de avaliação e métricas detalhadas em [`paper/SSRL-v0.1.md`](paper/SSRL-v0.1.md#metodologia-de-avaliação).

---

## Estrutura do repositório

```
SSRL/
├── README.md
├── LICENSE
├── docs/
│   ├── architecture.md
│   ├── graph-schema.md
│   ├── related-work.md
│   └── roadmap.md
├── paper/
│   └── SSRL-v0.1.md
├── prototype/
└── research/
```

---

## Roadmap

Veja o roadmap completo em [`roadmap.md`](roadmap.md).

---

## Contributing

Ainda não há código para contribuir — este é um projeto em estágio de pesquisa. Áreas onde discussão e crítica são bem-vindas:

- Static Analysis
- Knowledge Graphs
- Program Analysis
- Graph Databases
- LLM Evaluation

---

## Related Work

- CodeQL
- Program Dependence Graphs
- Knowledge Graphs
- RAG Systems
- GraphRAG
- Semantic Code Search
- Software Knowledge Graphs

Lista completa com contexto em [`docs/related-work.md`](docs/related-work.md).

---

## Leia mais

- 📄 **[Paper completo (SSRL v0.1)](paper/SSRL-v0.1.md)** — especificação arquitetural completa, princípios de design, modelo de confiança, ameaças à validade
- 🏗️ **[Arquitetura física](docs/architecture.md)** — pipeline técnico (parser → graph builder → vector layer → semantic engine → storage → query engine)
- 🧬 **[Schema do grafo](docs/graph-schema.md)** — definição formal e JSON schema dos nós e arestas
- 🗺️ **[Roadmap](roadmap.md)** — de paper de pesquisa a protótipo end-to-end

---

*SSRL não é uma linguagem de programação, nem um compilador, nem documentação. É uma tentativa de estabelecer uma camada de compreensão semântica acima dos sistemas de software — porque o próximo gargalo da engenharia não é gerar código, é entendê-lo.*
