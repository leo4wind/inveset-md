"""读取《金融投资知识体系.json》，按名称查找名词卡片。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from finance_lab.core.paths import KNOWLEDGE_JSON


@dataclass(frozen=True)
class TermCard:
    """知识体系里的一个名词节点（人类可读摘要）。"""

    id: str
    name: str
    definition: str
    formula: str
    layer: str
    domain: str
    explanation: str

    def summary(self) -> str:
        lines = [
            f"[{self.id}] {self.name}",
            f"层级: {self.layer} · 领域: {self.domain}",
            f"定义: {self.definition}",
        ]
        if self.formula:
            lines.append(f"公式: {self.formula}")
        return "\n".join(lines)


def load_knowledge(path: Path | None = None) -> dict:
    """加载完整知识体系 JSON。"""
    json_path = path or KNOWLEDGE_JSON
    with json_path.open(encoding="utf-8") as f:
        return json.load(f)


def find_term(name: str, path: Path | None = None) -> TermCard:
    """按名称精确或包含匹配一个名词。例如 find_term("夏普比率")。"""
    data = load_knowledge(path)
    nodes = data.get("nodes", [])

    exact = [n for n in nodes if n.get("name") == name]
    if not exact:
        exact = [n for n in nodes if name in (n.get("name") or "")]

    if not exact:
        raise KeyError(f"知识体系中未找到名词: {name!r}")

    node = exact[0]
    return TermCard(
        id=str(node.get("id", "")),
        name=str(node.get("name", "")),
        definition=str(node.get("definition", "")),
        formula=str(node.get("formula") or ""),
        layer=str(node.get("layer", "")),
        domain=str(node.get("domain", "")),
        explanation=str(node.get("explanation", "")),
    )
