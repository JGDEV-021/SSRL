# SSRL — Semantic Software Representation Layer

> **A camada semântica que preserva o entendimento do software na era em que ele pode ser gerado mais rápido do que pode ser compreendido.**

[![Status](https://img.shields.io/badge/status-research%20%2F%20pre--implementation-orange)]()
[![Version](https://img.shields.io/badge/version-V0.1-blue)]()
[![License](https://img.shields.io/badge/license-MIT-lightgrey)]()

---

## Sumário

- [Por que SSRL existe](#por-que-ssrl-existe)
- [A pergunta central](#a-pergunta-central)
- [As perguntas operacionais que só o SSRL responde](#as-perguntas-operacionais-que-só-o-ssrl-responde)
- [O que é o SSRL](#o-que-é-o-ssrl)
- [O que o SSRL não é](#o-que-o-ssrl-não-é)
- [Princípios de design](#princípios-de-design)
- [Arquitetura do sistema](#arquitetura-do-sistema)
  - [Camada 1 — Código-fonte](#camada-1--código-fonte)
  - [Camada 2 — Extração estrutural](#camada-2--extração-estrutural)
  - [Camada 3 — Construção do grafo de software](#camada-3--construção-do-grafo-de-software)
  - [Camada 4 — Enriquecimento semântico](#camada-4--enriquecimento-semântico)
  - [Camada 5 — Consolidação de conhecimento](#camada-5--consolidação-de-conhecimento)
  - [Camada 6 — Interface de consulta e raciocínio](#camada-6--interface-de-consulta-e-raciocínio)
- [Modelo de confiança](#modelo-de-confiança)
- [Regeneração incremental](#regeneração-incremental)
- [Versionamento semântico do conhecimento](#versionamento-semântico-do-conhecimento)
- [Software adversarial e ambíguo](#software-adversarial-e-ambíguo)
- [Aplicações em segurança](#aplicações-em-segurança)
- [Aplicação direta aos cenários de governança e arquitetura](#aplicação-direta-aos-cenários-de-governança-e-arquitetura)
- [Metodologia de avaliação](#metodologia-de-avaliação)
- [Ameaças à validade](#ameaças-à-validade)
- [Direções futuras](#direções-futuras)
- [Conclusão](#conclusão)

---

## Por que SSRL existe

Durante décadas, a engenharia de software operou sob uma premissa silenciosa:

```
Custo de Produção de Código  >>  Custo de Compreensão de Código
```

Escrever software era caro. Entendê-lo, relativamente, era barato — porque quem escrevia o código geralmente era quem precisava entendê-lo, e a velocidade de geração era limitada pela velocidade humana de digitação, raciocínio e revisão.

Modelos de linguagem de grande escala (LLMs) inverteram essa equação:

```
Custo de Produção de Código  <<  Custo de Compreensão de Código
```

Hoje é possível gerar milhares de linhas de código, múltiplos serviços, integrações e fluxos de negócio em minutos. O que não escalou na mesma proporção foi a capacidade — humana ou de máquina — de **compreender, auditar, manter e confiar** no que foi gerado.

O problema deixou de ser "como produzir software" e passou a ser:

> **Como preservamos o conhecimento produzido numa era em que o software pode ser gerado mais rápido do que pode ser compreendido?**

SSRL é uma proposta de resposta a essa pergunta — não através de mais documentação manual (que fica obsoleta), nem de mais código (que aumenta o problema), mas através de uma **camada de representação semântica derivada, contínua e auditável** que existe entre o código-fonte e os sistemas (humanos ou de IA) que precisam raciocinar sobre ele.

---

## A pergunta central

> *Se a IA pode gerar software mais rápido do que humanos conseguem compreendê-lo, qual é a próxima camada de abstração necessária para preservar e entender o conhecimento contido nesse software?*

Toda a arquitetura, os princípios e as decisões de design descritas neste documento são, em última instância, tentativas de responder a essa pergunta de forma prática e implementável.

---

## As perguntas operacionais que só o SSRL responde

Existe uma forma simples de testar se um problema organizacional precisa do SSRL. Pegue as perguntas que arquitetos, engenheiros de segurança, compliance e times de produto fazem todos os dias:

- Esse fluxo faz sentido?
- Que sistema depende disso?
- Isso quebra conformidade?
- Isso afeta faturamento?
- Isso cria risco de segurança?
- Isso está alinhado com a arquitetura?

Se a resposta honesta para qualquer uma dessas perguntas hoje é **"pergunta para o time"**, **"pergunta para quem escreveu isso"** ou, mais revelador ainda, **"pergunta para o agente"** — ou seja, ninguém tem certeza, só uma IA generativa consegue inferir algo a partir do código, e mesmo assim sem rastreabilidade — então existe uma lacuna de representação de conhecimento. É exatamente essa lacuna que o SSRL foi desenhado para preencher.

O SSRL não substitui a pessoa ou o agente que responde. Ele estrutura **a base de evidências, confiança e proveniência** sobre a qual qualquer resposta — humana ou de IA — deveria ser construída. Em vez de uma resposta opaca ("o agente disse que está tudo bem"), o SSRL produz uma resposta rastreável: *qual nó do grafo*, *qual hipótese semântica*, *com qual confiança*, *baseada em quais evidências*.

| Pergunta organizacional | Sem SSRL | Com SSRL |
|---|---|---|
| Esse fluxo faz sentido? | Releitura manual de código/documentação desatualizada | Consulta ao grafo: nós, arestas `Calls`/`Triggers`/`DependsOn` e hipóteses de conceito associadas |
| Que sistema depende disso? | Busca textual por nome de função/serviço | Travessia determinística do grafo de dependências (`DependsOn`, `Consumes`, `CommunicatesWith`) |
| Isso quebra conformidade? | Auditoria manual, sujeita a lacunas | Consulta a hipóteses semânticas rotuladas (ex.: "Payment Processing", "PII Handling") com confiança e evidência explícitas |
| Isso afeta faturamento? | Conhecimento tribal de quem "sabe como o billing funciona" | Subgrafo de conceito "Billing/Invoices/Subscriptions" com proveniência rastreável |
| Isso cria risco de segurança? | Achados isolados de ferramentas como CodeQL/Semgrep, sem contexto de negócio | Achado de segurança contextualizado semanticamente (ver [Seção 11](#aplicações-em-segurança)) |
| Isso está alinhado com a arquitetura? | Diagrama de arquitetura desatualizado, mantido manualmente | Grafo estrutural sempre derivado do código atual (Princípio P1) |

---

## O que é o SSRL

**Semantic Software Representation Layer (SSRL)** é um **grafo de conhecimento semântico**, derivado e agnóstico de linguagem, que combina:

1. **Análise de programa determinística** — fatos extraídos diretamente do código-fonte (ASTs, grafos de chamada, dependências), sem qualquer interpretação.
2. **Enriquecimento semântico probabilístico** — hipóteses de significado geradas a partir de padrões de nomenclatura, documentação, histórico de commits e inferência por LLM, sempre acompanhadas de confiança explícita e evidência rastreável.

O resultado é uma representação unificada de **estrutura, comportamento, arquitetura e significado** que pode ser consultada continuamente — tanto por humanos quanto por sistemas de IA — sem exigir releitura completa do código-fonte a cada pergunta.

SSRL não tenta substituir o código-fonte, nem afirma compreensão semântica perfeita. Seu objetivo é **reduzir o custo de compreensão**, não eliminá-lo.

---

## O que o SSRL não é

Para evitar ambiguidade de escopo, o SSRL explicitamente **não é**:

- Uma linguagem de programação.
- Um compilador.
- Um substituto para documentação técnica.
- Um grafo de conhecimento de software isolado, sem camada de confiança.
- Um substituto para ferramentas de análise estática como CodeQL ou Semgrep (o SSRL as complementa, fornecendo contexto semântico em torno dos achados).
- Uma fonte de verdade absoluta — toda hipótese semântica é probabilística e revisável.

---

## Princípios de design

O SSRL é guiado por seis princípios fundamentais (P1–P6):

### P1. Código é a fonte da verdade
O grafo nunca é editado manualmente. Ele é **sempre derivado** do código-fonte. Isso garante que o SSRL nunca diverge silenciosamente da realidade do sistema.

### P2. Fatos estruturais e hipóteses semânticas são coisas diferentes
- **Fato** (determinístico): `InventoryService importa DataService`.
- **Hipótese** (probabilística): `InventoryService gerencia persistência de jogador`.

Essa separação é o que permite ao SSRL ser confiável: fatos não precisam de confiança, hipóteses sempre precisam.

### P3. Confiança deve ser explícita
Toda asserção semântica carrega:
- **Confidence** (score de confiança)
- **Origin** (origem da inferência)
- **Extraction Method** (método de extração)
- **Evidence** (evidências que sustentam a hipótese)

Nenhuma afirmação semântica é tratada como verdade absoluta.

### P4. Regeneração incremental
Uma modificação no código não exige reconstrução completa do grafo. Apenas as regiões afetadas devem ser reprocessadas.

### P5. Explicabilidade
Toda conclusão semântica deve fornecer rastreabilidade total — qualquer hipótese pode ser decomposta nas evidências (nome de módulo, nomes de função, entidades referenciadas, documentação relacionada, similaridade semântica) que a sustentam.

### P6. Override humano
Humanos podem anotar o grafo, mas **anotações humanas são armazenadas separadamente** das semânticas extraídas automaticamente — evitando contaminar a análise automatizada com viés ou erro humano, enquanto ainda permite curadoria.

---

## Arquitetura do sistema

O SSRL é composto por seis camadas sequenciais:

```
Camada 1: Código-fonte
        ↓
Camada 2: Extração Estrutural
        ↓
Camada 3: Construção do Grafo de Software
        ↓
Camada 4: Enriquecimento Semântico
        ↓
Camada 5: Consolidação de Conhecimento
        ↓
Camada 6: Interface de Consulta e Raciocínio
```

### Camada 1 — Código-fonte
O ponto de partida e a única fonte de verdade. Tudo no SSRL é, em última instância, derivado daqui.

### Camada 2 — Extração estrutural
**100% determinística. Sem uso de LLMs.**

Responsável por extrair fatos verificáveis a partir do código:

- AST (Abstract Syntax Tree)
- CFG (Control Flow Graph)
- Call Graph
- Dependency Graph
- Import Graph
- Symbol Table

O objetivo desta camada é puramente factual — nenhuma interpretação de significado ocorre aqui.

### Camada 3 — Construção do grafo de software
Todos os artefatos estruturais da Camada 2 são unificados em um único grafo, com tipos de nó e aresta padronizados.

**Tipos de nó:**

| Tipo | Descrição |
|---|---|
| Module | Módulo de código |
| Function | Função ou método |
| Class | Classe ou tipo |
| Entity | Entidade de domínio |
| Resource | Recurso do sistema |
| Database | Banco de dados |
| API Endpoint | Endpoint de API |
| Event | Evento de sistema |
| Service | Serviço |
| Configuration | Configuração |

**Tipos de aresta:**

| Aresta | Descrição |
|---|---|
| Calls | Chamada de função/método |
| Imports | Importação de módulo |
| Reads | Leitura de dado/recurso |
| Writes | Escrita de dado/recurso |
| Creates | Criação de entidade/recurso |
| Consumes | Consumo de evento/mensagem |
| Produces | Produção de evento/mensagem |
| Triggers | Disparo de ação/evento |
| DependsOn | Dependência |
| CommunicatesWith | Comunicação entre serviços |

Todas as arestas nesta camada são **determinísticas** — extraídas diretamente da estrutura do código, sem inferência probabilística.

### Camada 4 — Enriquecimento semântico
Aqui entra a interpretação probabilística. Esta camada combina:

- Vizinhança no grafo
- Padrões de nomenclatura
- Comentários
- Documentação
- Mensagens de commit
- Contexto de uso

E produz **hipóteses de conceito** — múltiplas interpretações podem coexistir para o mesmo nó. Exemplo:

```
Node: InventoryService

Hypotheses:
  Inventory Management     → 0.92
  Equipment System         → 0.54
  Player Persistence       → 0.41
```

Note que múltiplas hipóteses com confiança diferente coexistem deliberadamente — o SSRL não força uma única interpretação quando a evidência é ambígua.

### Camada 5 — Consolidação de conhecimento
Unifica fatos estruturais, hipóteses semânticas, anotações humanas e histórico de versões em uma representação coerente e consultável.

### Camada 6 — Interface de consulta e raciocínio
A camada onde humanos e agentes de IA efetivamente interagem com o SSRL — fazendo perguntas como as listadas na seção [Perguntas operacionais](#as-perguntas-operacionais-que-só-o-ssrl-responde) e recebendo respostas rastreáveis até a evidência original.

---

## Modelo de confiança

Um score de confiança no SSRL **não representa a probabilidade de a hipótese ser verdadeira**. Em vez disso:

> Confiança representa o grau de **concordância entre fontes de evidência independentes**.

Fontes de sinal consideradas:

- Análise de nomenclatura
- Topologia do grafo
- Documentação
- Histórico de commits
- Inferência por LLM

A confiança é computada por **consenso ponderado** entre essas fontes. Mecanismos futuros de calibração podem incluir:

- Modelos de ensemble
- Amostragem de autoconsistência (self-consistency sampling)
- Validação por recuperação (retrieval validation)
- Calibração por feedback humano

O mecanismo exato de calibração permanece um **problema de pesquisa aberto** — o SSRL v3 define o modelo conceitual, não a implementação final do algoritmo de consenso.

---

## Regeneração incremental

Um dos maiores desafios práticos do SSRL é o custo de sincronização entre código e grafo.

**Abordagem ingênua (rejeitada):**

```
Mudança no Código → Reconstrução Total do Grafo → Reanálise Semântica Total
```

Essa abordagem não escala para repositórios grandes ou times com alta frequência de commits.

**Abordagem proposta pelo SSRL:**

```
Detecção de Mudança
        ↓
Análise de Impacto
        ↓
Descoberta de Subgrafo Afetado
        ↓
Reanálise Seletiva
```

Apenas as regiões do grafo realmente impactadas por uma mudança são regeneradas. A otimização exata das fronteiras de invalidação (quanto do grafo "ao redor" de uma mudança precisa ser reprocessado) é uma área de pesquisa futura.

---

## Versionamento semântico do conhecimento

Como o conhecimento sobre o sistema evolui ao longo do tempo (não apenas o código, mas também as **interpretações** sobre o código), cada nó do grafo carrega:

- **Semantic ID** — identificador estável do conceito
- **Version** — versão da representação
- **Timestamp** — momento da extração/atualização
- **Source Commit** — commit de origem
- **Confidence History** — histórico de evolução da confiança

Isso habilita capacidades como:

- Rastreamento de evolução arquitetural
- Diferenciação semântica (semantic diffing) entre versões
- Reconstrução histórica de intenção de design

---

## Software adversarial e ambíguo

O SSRL parte da premissa realista de que nem todo software é bem-comportado. Código real pode ser:

- Mal documentado
- Mal nomeado
- Obfuscado
- Malicioso

Exemplos de código ambíguo:

```python
def doTask():
    x = ...
    y = ...
    tmp = ...
```

Nesses casos, o comportamento esperado do SSRL é:

- **Confiança diminui** proporcionalmente à ambiguidade.
- **Incerteza semântica aumenta** e é representada explicitamente no grafo.

> **Princípio central:** Incerteza é preferível a certeza incorreta.

Isso é particularmente relevante em contextos de segurança e auditoria, onde uma hipótese semântica falsamente confiante pode ser mais perigosa do que a ausência de hipótese.

---

## Aplicações em segurança

O SSRL **não substitui** ferramentas de análise estática de segurança como CodeQL ou Semgrep. Em vez disso, ele adiciona **contexto semântico de negócio** em torno dos achados técnicos dessas ferramentas.

**Exemplo comparativo:**

Ferramenta tradicional de análise estática:
```
SQL Injection Found
```

SSRL (mesmo achado, com contexto):
```
SQL Injection Found

Affected Concept:      Payment Processing
Business Criticality:  High
Related Services:      Billing, Subscriptions, Invoices
```

Essa contextualização transforma um alerta técnico genérico em informação priorizável para times de segurança e engenharia — respondendo diretamente a perguntas como *"isso cria risco de segurança?"* e *"isso afeta faturamento?"* com rastreabilidade até a origem.

---

## Aplicação direta aos cenários de governança e arquitetura

Retomando a tabela de perguntas organizacionais apresentada anteriormente, o SSRL foi desenhado precisamente para os momentos em que a resposta institucional default seria "pergunta para o agente" — ou seja, situações em que:

1. Não existe documentação atualizada confiável.
2. A única fonte de verdade prática é o código-fonte, ilegível em escala humana.
3. Decisões de arquitetura, segurança, compliance ou faturamento dependem de inferência ad-hoc, sem rastreabilidade nem histórico de confiança.

O SSRL substitui esse vácuo por uma resposta estruturada: **fato determinístico + hipótese semântica + confiança + evidência + proveniência histórica**. Isso não elimina a necessidade de julgamento humano (ou de agentes de IA) — mas estrutura a base sobre a qual esse julgamento é exercido, tornando-o auditável, reproduzível e incrementalmente atualizável.

---

## Metodologia de avaliação

A validação do SSRL como conceito de pesquisa deve incluir, no mínimo, quatro dimensões:

### 1. Acurácia estrutural
Comparação da correção do grafo contra uma verdade derivada do compilador (ground truth determinística).

### 2. Concordância semântica
Comparação entre anotações humanas e hipóteses geradas pelo SSRL, medindo grau de alinhamento.

### 3. Estudos de compreensão
Tarefas como:
- Localizar a origem de um bug
- Identificar uma dependência arquitetural
- Entender o fluxo de uma funcionalidade

Métricas: tempo, acurácia, confiança reportada.

### 4. Estudos de onboarding
Comparação entre:
- Desenvolvedores usando apenas código-fonte
- Desenvolvedores usando SSRL

Métricas: tempo até compreensão, taxa de conclusão de tarefas, recall arquitetural.

---

## Ameaças à validade

O SSRL reconhece explicitamente seus próprios riscos como projeto de pesquisa:

| Ameaça | Descrição |
|---|---|
| **Alucinações de LLM** | Interpretações semânticas incorretas geradas na Camada 4 |
| **Viés de dataset** | Dados de treinamento influenciam a extração semântica |
| **Subjetividade de anotação humana** | Especialistas podem divergir entre si |
| **Drift arquitetural** | Qualidade do grafo pode degradar se a regeneração falhar |
| **Restrições de escala** | Repositórios grandes podem causar explosão combinatória do grafo |

---

## Direções futuras

Extensões potenciais identificadas para versões futuras do SSRL:

- **Linguagem de Consulta Semântica** (Semantic Query Language)
- **Motores de Busca Arquitetural** (Architectural Search Engines)
- **Ferramentas de Desenvolvimento Nativas para Agentes** (Agent-Native Development Tools)
- **Pull Requests Semânticos** (Semantic Pull Requests)
- **Git Semântico** (Semantic Git)
- **Compreensão de Projetos Multi-linguagem** (Cross-Language Project Understanding)
- **Navegação Autônoma de Software** (Autonomous Software Navigation)

---

## Conclusão

O SSRL não é uma linguagem de programação, nem um compilador, nem documentação, nem apenas mais um grafo de conhecimento de software isolado.

O SSRL é uma tentativa de estabelecer uma **camada de compreensão semântica** acima dos sistemas de software — uma camada que combina o rigor de fatos determinísticos com a utilidade de hipóteses semânticas explicitamente incertas, sempre rastreáveis até sua evidência de origem.

O objetivo não é compreensão perfeita. **O objetivo é compreensão útil.**

À medida que o volume de software gerado por IA continua crescendo, representações que expõem estrutura, comportamento, relacionamentos, incerteza e significado conceitual tendem a se tornar cada vez mais necessárias — não como luxo arquitetural, mas como pré-condição para confiança, governança e auditabilidade em escala.

> O sucesso do SSRL não deve ser medido por compreender completamente o software.
> Deve ser medido por humanos e sistemas de IA compreenderem o software **significativamente melhor com ele do que sem ele**.

---

## Status do projeto

Este repositório documenta a **especificação arquitetural e agenda de pesquisa (v3.0)** do SSRL. Trata-se de um projeto em estágio de pesquisa — os mecanismos de calibração de confiança, otimização de regeneração incremental e a Semantic Query Language ainda são problemas abertos, não implementações finalizadas.

Contribuições, críticas e propostas de validação empírica são bem-vindas enquanto o projeto evolui de especificação para protótipo.
