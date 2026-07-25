---
name: domain-knowledge-graph-builder
description: >-
  Build a structured domain knowledge system from a target domain and a set of domain-specific terms.
  Automatically performs term parsing, knowledge layering, networked knowledge graph construction,
  and outputs visualizable, multi-dimensional queryable knowledge structures.
  Use when the user: (1) specifies a domain + a batch of terms and asks to build a knowledge
  system/framework/graph, (2) requests a visual networked knowledge-point relationship diagram,
  (3) needs a queryable domain knowledge structure supporting lookup by term, layer, or scenario,
  (4) wants to build a layered knowledge framework or plan a learning roadmap for a specific domain.
  Triggers include phrases like "构建知识体系", "知识图谱", "知识框架", "领域建模", "学习路线",
  "build knowledge graph", "domain knowledge structure", "knowledge system".
---

# Domain Knowledge Graph Builder

## Overview

Transform a target domain and a set of domain-specific terms into a structured, visualizable,
and queryable knowledge system. The system aligns with a "three-layer knowledge model +
four-layer knowledge stratification framework", integrating domain modeling, SOA componentization,
and ontology modeling principles.

**Core deliverables: 1 framework + 4 visualizations + 1 query entry**

## Input Specification

### Required
1. **Domain name**: e.g., "医疗数据治理", "量化交易", "临床研究"
2. **Term list**: >=3 domain terms/concepts/methods. If fewer than 5, auto-supplement core terms via web search to reach 8-15 baseline.

### Optional
- Custom knowledge dimensions (for knowledge matrix)
- Key business scenarios (for scenario-based knowledge assembly)
- Layering rule preferences
- Visualization format preference (default: Mermaid; alternative: structured JSON)

## Complete Workflow

Execute these 7 phases sequentially. See [references/knowledge-framework.md](references/knowledge-framework.md)
for detailed framework rules, [references/graph-design.md](references/graph-design.md) for graph
specifications, and [references/query-and-visualization.md](references/query-and-visualization.md)
for query layer and Mermaid patterns.

### Phase 1: Input Validation & Term Preprocessing

1. Receive domain name and term list; deduplicate and normalize (unify full names/abbreviations, merge synonyms)
2. If term count < 5, call `WebSearch` to supplement domain core terms, expanding to 8-15 baseline
3. Output standardized term list; confirm domain boundary with user

### Phase 2: Term Batch Parsing & Knowledge Extraction

For each term, search for authoritative definitions and extract structured info into a **term card**:

| Field | Description |
|-------|-------------|
| 标准定义 | Standard definition and core meaning |
| 上位概念 | Parent concept and classification |
| 前置依赖 | Prerequisite knowledge points |
| 关联术语 | Related terms (peer, subordinate, causal, compositional, evolutionary) |
| 应用场景 | Typical application scenarios |
| 层级置信度 | Confidence score for knowledge layer assignment (0-1) |

### Phase 3: Four-Layer Knowledge Framework Construction

Classify all terms into 4 layers to form the domain knowledge skeleton. See
[references/knowledge-framework.md](references/knowledge-framework.md) for detailed rules.

1. **基础理论层**: Foundational principles, concepts, theoretical models, core algorithms, methodologies
2. **核心业务能力层**: Core business modules, processes, key technologies, capability units
3. **扩展应用层**: Implementation scenarios, industry practices, tools/platforms, cross-domain applications
4. **治理管控层**: Standards, compliance, risk control, quality systems, governance mechanisms

Validation rules: mark low-confidence nodes as "pending confirmation"; supplement inter-layer
linkage relationships; ensure balanced granularity across layers.

### Phase 4: Three-Layer Progressive Knowledge System

#### 4.1 Top Layer - Domain Trunk
- Cluster first-level knowledge domains from the four-layer framework
- Generate a center-symmetric bilateral tree (mindmap) with balanced left/right branches
- Output inter-domain dependencies, collaborations, and integration logic

#### 4.2 Middle Layer - Knowledge Matrix
- Extract 2 core dimensions (default: knowledge layer x business scenario); support custom dimensions
- Map all knowledge points to matrix cells; calculate cell knowledge density
- Mark empty cells as "knowledge blind spots" with gap-filling suggestions

#### 4.3 Bottom Layer - Networked Knowledge Graph (Core Capability)
See [references/graph-design.md](references/graph-design.md) for full specifications.

- **Nodes**: All minimum knowledge units with attributes (layer, domain, definition summary, difficulty)
- **Edges**: 5 relationship types - subordinate, dependency, association, composition, evolution
- **Layout**: Group-cluster by knowledge domain; directed arrows for strong dependencies
- Output both Mermaid graph and structured JSON data

### Phase 5: Learning Path DAG Generation

- Derive learning order via topological sort based on prerequisite dependencies
- Generate layered DAG: entry -> foundation -> intermediate -> advanced
- Support single-node prerequisite path tracing and extension path recommendation

### Phase 6: Visualization Output Packaging

Output all structures in directly renderable formats:

| Structure | Format |
|-----------|--------|
| Tree / trunk diagram | Mermaid mindmap or tree |
| Knowledge matrix | Markdown table + density annotation |
| Networked knowledge graph | Mermaid graph (clustered) + structured JSON |
| Learning path | Mermaid flowchart LR (layered DAG) |

See [references/query-and-visualization.md](references/query-and-visualization.md) for Mermaid templates.

### Phase 7: Query Layer & Interactive Entry

Package all structured data into a query engine. See
[references/query-and-visualization.md](references/query-and-visualization.md) for details.

Support 5 query types (all results sync with graph node highlighting):
1. **Node query**: Single term -> full definition, layer/domain, prerequisites, extensions, related nodes, highlighted position
2. **Layer/domain query**: Specified layer or domain -> all knowledge points, tree structure, local subgraph
3. **Scenario assembly query**: Business scenario -> required knowledge components, assembly order, dependency chain, scenario subgraph
4. **Learning path query**: Target knowledge -> complete path from zero, prerequisite list, staged nodes, DAG
5. **Blind spot & dimension query**: Dimension combination or "blind spots" -> knowledge point list, gap list, gap-filling suggestions

## Output Deliverables

After completing all phases, present in this order:
1. Four-layer knowledge framework overview
2. Top-level domain trunk mindmap
3. Core knowledge matrix (layer x scenario)
4. Networked knowledge graph (clustered + edge annotations)
5. Learning path DAG (entry to advanced)
6. Interactive prompt: guide user to query specific nodes, view domain subgraphs, check learning paths, or request scenario assembly

## Exception Handling

| Scenario | Action |
|----------|--------|
| Term parsing fails | Mark as "pending supplement"; do not force into system; flag in blind spots |
| Insufficient terms | Auto-supplement domain core terms; inform user they can add custom terms |
| Relationship undetermined | Do not force edges for weak associations; avoid incorrect knowledge links |
| Niche domain | Degrade to basic layering + trunk structure; explain data limitations |

## Iteration Rules

1. Support adding new terms -> auto-merge into existing system and update graph
2. Support correcting layers, relationships, dimensions -> regenerate all views
3. Support importing documents/papers/standards -> auto-extract terms to expand the system

## Standard Interaction Flow

**Step 1 - Trigger**: User provides domain + term list
> User: 构建知识体系，领域：医疗数据治理，名词：元数据、数据标准、数据质量、主数据、数据安全、数据血缘

**Step 2 - Build complete**: Output all 6 deliverables, then guide interaction

**Step 3 - Query & visualize**:
> User: 查询数据质量的关联知识点，高亮显示在网状图里
> Output: Term detail card + related node list + highlighted graph

> User: 完成临床数据互通场景需要哪些知识
> Output: Scenario component list + assembly workflow + scenario subgraph
