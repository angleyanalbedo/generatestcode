# st_slicer/blocks/types.py

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Set, Any, Dict, Optional


from ..ast.nodes import Stmt

@dataclass
class FunctionalBlock:
    """
    一个功能块的抽象：由若干切片准则 + 节点集合 + AST 语句 + 源码行号组成。
    """
    criteria: List[SlicingCriterion] = field(default_factory=list)
    node_ids: Set[int] = field(default_factory=set)
    stmts: List[Stmt] = field(default_factory=list)
    line_numbers: List[int] = field(default_factory=list)

@dataclass(frozen=True)
class SlicingCriterion:
    node_id: int
    kind: str
    variable: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)