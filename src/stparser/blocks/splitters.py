# st_slicer/blocks/splitters.py

from __future__ import annotations
from typing import Dict, List, Optional, Set, Tuple

import re

from ..ast.nodes import Stmt
from .types import FunctionalBlock
from .slice_ops import nodes_to_sorted_ast_stmts
from .line_map import stmts_to_line_numbers
from .structure_if_case_loop import patch_if_structure, patch_case_structure
from .st_text import update_ctrl_depth


def _build_block_from_lines(
    parent_block: FunctionalBlock,
    seg_lines: List[int],
    ir2ast_stmt: List[Stmt],
    code_lines: List[str],
    parent_map: Dict[Stmt, Optional[Stmt]],
) -> FunctionalBlock:
    seg_line_set = set(seg_lines)

    sub_node_ids: Set[int] = set()
    for nid in parent_block.node_ids:
        if 0 <= nid < len(ir2ast_stmt):
            st = ir2ast_stmt[nid]
            if st is None:
                continue
            ln = getattr(st.loc, "line", None)
            if ln is not None and ln in seg_line_set:
                sub_node_ids.add(nid)

    sub_stmts = nodes_to_sorted_ast_stmts(sub_node_ids, ir2ast_stmt, parent_map)

    base_lines = stmts_to_line_numbers(sub_stmts, code_lines)
    fixed = patch_if_structure(base_lines, code_lines, ensure_end_if=True)
    fixed = patch_case_structure(fixed, code_lines, ensure_end_case=True, include_branch_headers=True)
    sub_lines = sorted(fixed)

    return FunctionalBlock(
        criteria=list(parent_block.criteria),
        node_ids=sub_node_ids,
        stmts=sub_stmts,
        line_numbers=sub_lines,
    )


def _split_block_by_size(
    block: FunctionalBlock,
    ir2ast_stmt: List[Stmt],
    code_lines: List[str],
    min_lines: int,
    max_lines: int,
    parent_map: Dict[Stmt, Optional[Stmt]],
) -> List[FunctionalBlock]:
    lines = sorted(block.line_numbers)
    if len(lines) <= max_lines:
        return [block]

    segments: List[List[int]] = []
    current: List[int] = []
    ctrl_depth = 0

    for ln in lines:
        if not current:
            current = [ln]
        else:
            if ln != current[-1] + 1 and len(current) >= min_lines and ctrl_depth == 0:
                segments.append(current)
                current = [ln]
            else:
                current.append(ln)

        if 1 <= ln <= len(code_lines):
            ctrl_depth = update_ctrl_depth(code_lines[ln - 1], ctrl_depth, clamp_negative=True)

        if len(current) >= max_lines and ctrl_depth == 0:
            segments.append(current)
            current = []

    if current:
        segments.append(current)

    merged: List[List[int]] = []
    for seg in segments:
        if not merged:
            merged.append(seg)
            continue
        if len(seg) < min_lines:
            merged[-1].extend(seg)
        else:
            merged.append(seg)

    sub_blocks: List[FunctionalBlock] = []
    for seg in merged:
        seg = sorted(set(seg))
        if len(seg) < max(1, min_lines // 2):
            continue
        sub_blocks.append(_build_block_from_lines(block, seg, ir2ast_stmt, code_lines, parent_map))

    return sub_blocks or [block]


def _split_block_by_stage(
    block: FunctionalBlock,
    ir2ast_stmt: List[Stmt],
    code_lines: List[str],
    parent_map: Dict[Stmt, Optional[Stmt]],
    min_lines: int,
    stage_var_names: Tuple[str, ...],
) -> List[FunctionalBlock]:
    lines = sorted(block.line_numbers)
    if not lines:
        return [block]

    def is_stage_marker(line_text: str) -> bool:
        lt = line_text.strip()
        if not lt:
            return False
        upper = lt.upper()

        for name in stage_var_names:
            uname = name.upper()
            pat = rf"\bIF\b.*\b{uname}\b\s*=\s*[\w\.]+"
            if re.search(pat, upper):
                return True
        return False

    segments: List[List[int]] = []
    current: List[int] = []
    saw_marker = False

    for ln in lines:
        text = code_lines[ln - 1] if 0 < ln <= len(code_lines) else ""
        if is_stage_marker(text):
            saw_marker = True
            if current:
                segments.append(current)
            current = [ln]
        else:
            if not current:
                current = [ln]
            else:
                current.append(ln)

    if current:
        segments.append(current)

    if not saw_marker:
        return [block]

    merged: List[List[int]] = []
    for seg in segments:
        if not merged:
            merged.append(seg)
            continue
        if len(seg) < min_lines:
            merged[-1].extend(seg)
        else:
            merged.append(seg)

    sub_blocks: List[FunctionalBlock] = []
    for seg in merged:
        seg = sorted(set(seg))
        if len(seg) < max(1, min_lines // 2):
            continue
        sub_blocks.append(_build_block_from_lines(block, seg, ir2ast_stmt, code_lines, parent_map))

    return sub_blocks or [block]


def split_blocks_by_stage(
    blocks: List[FunctionalBlock],
    ir2ast_stmt: List[Stmt],
    code_lines: List[str],
    parent_map: Dict[Stmt, Optional[Stmt]],
    min_lines: int = 5,
    stage_var_names: Tuple[str, ...] = ("stage", "Stage"),
) -> List[FunctionalBlock]:
    new_blocks: List[FunctionalBlock] = []
    for block in blocks:
        new_blocks.extend(
            _split_block_by_stage(
                block,
                ir2ast_stmt=ir2ast_stmt,
                code_lines=code_lines,
                parent_map=parent_map,
                min_lines=min_lines,
                stage_var_names=stage_var_names,
            )
        )
    return new_blocks


def normalize_block_sizes(
    blocks: List[FunctionalBlock],
    ir2ast_stmt: List[Stmt],
    code_lines: List[str],
    min_lines: int,
    max_lines: int,
    parent_map: Dict[Stmt, Optional[Stmt]],
) -> List[FunctionalBlock]:
    normalized: List[FunctionalBlock] = []
    for block in blocks:
        if len(block.line_numbers) > max_lines:
            normalized.extend(_split_block_by_size(block, ir2ast_stmt, code_lines, min_lines, max_lines, parent_map))
        else:
            normalized.append(block)
    return normalized


def normalize_and_split_blocks(
    blocks: List[FunctionalBlock],
    ir2ast_stmt: List[Stmt],
    code_lines: List[str],
    min_lines: int,
    max_lines: int,
    parent_map: Dict[Stmt, Optional[Stmt]],
) -> List[FunctionalBlock]:
    stage_blocks = split_blocks_by_stage(
        blocks,
        ir2ast_stmt=ir2ast_stmt,
        code_lines=code_lines,
        parent_map=parent_map,
        min_lines=min_lines,
        stage_var_names=("stage", "Stage", "state", "State"),
    )

    return normalize_block_sizes(
        stage_blocks,
        ir2ast_stmt=ir2ast_stmt,
        code_lines=code_lines,
        min_lines=min_lines,
        max_lines=max_lines,
        parent_map=parent_map,
    )
