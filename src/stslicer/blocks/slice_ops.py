# st_slicer/blocks/slice_ops.py

from __future__ import annotations
from typing import Any, Dict, List, Optional, Set, Tuple

from ..slicer import backward_slice

from ..ast.nodes import Stmt, IfStmt, ForStmt, CaseStmt, WhileStmt, RepeatStmt


def compute_slice_nodes(prog_pdg, start_node_id: int) -> Set[int]:
    """对给定起始节点做一次后向切片。"""
    return backward_slice(prog_pdg, [start_node_id])


def cluster_slices(
    all_slices: List[Tuple[SlicingCriterion, Set[int]]],
    overlap_threshold: float = 0.5,
) -> List[dict]:
    """
    输入: all_slices = [(criterion, node_set), ...]
    输出: clusters = [{"nodes": set[int], "criteria": [criterion, ...]}, ...]
    """
    clusters: List[dict] = []

    for crit, node_set in all_slices:
        placed = False
        for cluster in clusters:
            cluster_nodes: Set[int] = cluster["nodes"]
            inter = len(cluster_nodes & node_set)
            denom = min(len(cluster_nodes), len(node_set))
            if denom == 0:
                continue
            overlap = inter / denom
            if overlap >= overlap_threshold:
                cluster["nodes"] |= node_set
                cluster["criteria"].append(crit)
                placed = True
                break

        if not placed:
            clusters.append({"nodes": set(node_set), "criteria": [crit]})

    return clusters


def close_with_control_structures(
    stmt_set: Set[Stmt],
    parent_map: Dict[Stmt, Optional[Stmt]],
) -> Set[Stmt]:
    """
    结构闭包：如果集合里有子语句，则把其控制结构祖先（If/For/Case/While/Repeat）补进去。
    """
    closed: Set[Stmt] = set(stmt_set)
    worklist: List[Stmt] = list(stmt_set)

    while worklist:
        st = worklist.pop()
        p = parent_map.get(st)
        while p is not None:
            if isinstance(p, (IfStmt, ForStmt, CaseStmt, WhileStmt, RepeatStmt)) and p not in closed:
                closed.add(p)
                worklist.append(p)
            p = parent_map.get(p)

    return closed


def nodes_to_sorted_ast_stmts(
    cluster_nodes: Set[int],
    ir2ast_stmt: List[Stmt],
    parent_map: Dict[Stmt, Optional[Stmt]],
) -> List[Stmt]:
    """节点集合 -> AST 语句集合 -> 控制结构闭包 -> 按源码位置排序。"""
    stmt_set: Set[Stmt] = set()
    for nid in cluster_nodes:
        if 0 <= nid < len(ir2ast_stmt):
            ast_stmt = ir2ast_stmt[nid]
            if ast_stmt is not None:
                stmt_set.add(ast_stmt)

    stmt_set = close_with_control_structures(stmt_set, parent_map)

    stmts = sorted(
        stmt_set,
        key=lambda s: (getattr(s.loc, "line", 0), getattr(s.loc, "column", 0)),
    )
    return stmts


def build_parent_map_from_ir2ast(ir2ast_stmt: List[Stmt]) -> Dict[Stmt, Optional[Stmt]]:
    """
    基于 ir2ast_stmt 粗略构造 parent_map: child_stmt -> parent_stmt。
    只关心出现在 ir2ast_stmt 中的 Stmt 对象。
    """
    uniq_stmts: Set[Stmt] = {st for st in ir2ast_stmt if st is not None}
    parent: Dict[Stmt, Optional[Stmt]] = {}

    def visit(stmt: Stmt, parent_stmt: Optional[Stmt]) -> None:
        if stmt not in uniq_stmts:
            return

        if stmt not in parent or (parent[stmt] is None and parent_stmt is not None):
            parent[stmt] = parent_stmt

        if isinstance(stmt, IfStmt):
            for child in stmt.then_body:
                visit(child, stmt)
            for _cond, body in stmt.elif_branches:
                for child in body:
                    visit(child, stmt)
            for child in stmt.else_body:
                visit(child, stmt)

        elif isinstance(stmt, ForStmt):
            for child in stmt.body:
                visit(child, stmt)

        elif isinstance(stmt, CaseStmt):
            for entry in stmt.entries:
                for child in entry.body:
                    visit(child, stmt)
            for child in stmt.else_body:
                visit(child, stmt)

        elif isinstance(stmt, WhileStmt):
            for child in stmt.body:
                visit(child, stmt)

        elif isinstance(stmt, RepeatStmt):
            for child in stmt.body:
                visit(child, stmt)

    for st in uniq_stmts:
        visit(st, None)

    return parent
