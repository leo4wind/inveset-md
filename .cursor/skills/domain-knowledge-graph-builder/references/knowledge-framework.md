# Knowledge Framework Reference

## Table of Contents
- [Four-Layer Knowledge Stratification](#four-layer-knowledge-stratification)
- [Layer Classification Criteria](#layer-classification-criteria)
- [Classification Decision Rules](#classification-decision-rules)
- [Validation Rules](#validation-rules)
- [Inter-Layer Linkage](#inter-layer-linkage)
- [Term Card Template](#term-card-template)

---

## Four-Layer Knowledge Stratification

### Layer 1: 基础理论层 (Foundation Theory Layer)

Bottom-layer principles that underpin the entire domain.

**Includes:**
- Foundational concepts and definitions
- Theoretical models and frameworks
- Core algorithms and mathematical methods
- Universal methodologies and paradigms
- Domain ontology and taxonomy

**Examples (medical data governance):** 数据模型理论, 本体论, 元数据理论, 数据生命周期模型

### Layer 2: 核心业务能力层 (Core Business Capability Layer)

Domain-specific core business modules, processes, and key technical capabilities.

**Includes:**
- Core business modules and functional units
- Key business processes and workflows
- Core technical capabilities
- Essential data processing pipelines
- Core service components (SOA perspective)

**Examples (medical data governance):** 元数据管理, 数据标准管理, 数据质量管理, 主数据管理, 数据安全管理, 数据血缘追踪

### Layer 3: 扩展应用层 (Extension Application Layer)

Implementation scenarios, industry practices, tools, and cross-domain applications.

**Includes:**
- Implementation scenarios and use cases
- Industry best practices
- Tools and platforms
- Solutions and architectures
- Cross-domain fusion applications

**Examples (medical data治理):** 临床数据互通, 医疗AI数据准备, DRG数据应用, 数据中台, 跨院数据共享

### Layer 4: 治理管控层 (Governance & Control Layer)

Standards, compliance, risk management, and operational governance.

**Includes:**
- Standards and specifications
- Compliance and regulatory requirements
- Risk control mechanisms
- Quality assurance systems
- Operational governance and audit

**Examples (medical data治理):** HIPAA合规, 数据安全等级保护, 医疗数据分类分级标准, 数据治理成熟度评估, 隐私保护法规

---

## Layer Classification Criteria

When classifying a term, evaluate against these criteria in order:

1. **Is it a universal principle/theory/model?** -> Layer 1
2. **Is it a core domain business/technical capability?** -> Layer 2
3. **Is it a specific implementation/scenario/tool?** -> Layer 3
4. **Is it a standard/compliance/governance mechanism?** -> Layer 4
5. **If ambiguous**, assign based on primary function and set lower confidence score

---

## Classification Decision Rules

```
IF term is a fundamental concept/algorithm/theory
    -> Layer 1 (基础理论层), confidence >= 0.8
ELSE IF term is a core domain capability/process/technology
    -> Layer 2 (核心业务能力层), confidence >= 0.8
ELSE IF term is a scenario/practice/tool/solution
    -> Layer 3 (扩展应用层), confidence >= 0.7
ELSE IF term is a standard/regulation/policy/governance
    -> Layer 4 (治理管控层), confidence >= 0.8
ELSE
    -> Assign to closest layer, confidence <= 0.5, mark as "pending confirmation"
```

---

## Validation Rules

1. **Confidence threshold**: Nodes with confidence < 0.6 must be marked as "待确认" (pending confirmation)
2. **Layer balance**: Each layer should have at least 2 knowledge points; if any layer has 0, flag as potential gap
3. **Granularity consistency**: Knowledge points within the same layer should be at similar abstraction levels
4. **No orphans**: Every knowledge point must have at least one relationship to another point in the system

---

## Inter-Layer Linkage

Supplement these cross-layer relationship types to connect the framework:

| From Layer | To Layer | Relationship Type | Example |
|------------|----------|-------------------|---------|
| Layer 1 | Layer 2 | 理论支撑 (theory underpins) | 元数据理论 -> 元数据管理 |
| Layer 2 | Layer 3 | 能力应用 (capability applied to) | 数据质量管理 -> DRG数据应用 |
| Layer 2 | Layer 4 | 能力约束 (capability constrained by) | 数据安全管理 -> HIPAA合规 |
| Layer 3 | Layer 4 | 实践遵从 (practice complies with) | 跨院数据共享 -> 隐私保护法规 |
| Layer 1 | Layer 4 | 理论指导 (theory guides) | 数据生命周期模型 -> 数据治理成熟度评估 |

---

## Term Card Template

Each term should be documented as a structured card:

```markdown
### [Term Name]
- **标准定义**: [One-sentence authoritative definition]
- **核心内涵**: [2-3 sentences explaining the essence]
- **上位概念**: [Parent concept]
- **所属层级**: [Layer 1/2/3/4] (confidence: 0.X)
- **所属知识域**: [Domain cluster]
- **前置依赖**: [List of prerequisite knowledge points]
- **关联术语**: [Related terms with relationship type]
- **典型应用场景**: [1-3 scenarios]
- **学习难度**: [入门/基础/进阶/高级]
```
