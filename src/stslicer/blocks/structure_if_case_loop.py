# st_slicer/blocks/structure_if_case_loop.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, List, Optional, Set, Tuple

from .st_text import (
    clean_st_line,
    norm_line,
    is_if_start,
    is_elsif,
    is_else,
    is_end_if,
    is_case_label_line,
    RE_THEN,
    RE_ELSIF_HEAD,
    RE_ELSE_HEAD,
    RE_CASE_HEAD,
    RE_END_CASE,
    RE_ELSE_LINE,
)
from .structure_common import (
    scan_matching_end_if,
    scan_matching_end_case,
)

def scan_if_header_end(line_start: int, code_lines: List[str]) -> int:
    """
    从 IF/ELSIF 起始行向下扫描，直到遇到包含 THEN 的行，返回该行号。
    使用 clean_st_line 去注释，避免注释 THEN 误触发。
    """
    n = len(code_lines)
    ln = line_start
    while ln <= n:
        raw = code_lines[ln - 1]
        text = clean_st_line(raw)
        if RE_THEN.search(text):
            return ln
        ln += 1
    return line_start

@dataclass
class _IfFrame:
    if_line: int
    current_branch_head: int
    branches: List[Tuple[int, int, int]]  # (branch_head, body_start, body_end)

def patch_if_structure(
    sliced_lines: Iterable[int],
    code_lines: List[str],
    *,
    ensure_end_if: bool = True,
) -> Set[int]:
    """
    结构补全 IF：
      - 若某 IF 分支 body 内命中任意行，则补该分支头行（IF/ELSIF/ELSE）
      - 可选：若 IF 任意 body 被触及，则补 END_IF
    """
    n = len(code_lines)
    patched: Set[int] = set(int(x) for x in sliced_lines if 1 <= int(x) <= n)

    stack: List[_IfFrame] = []

    for ln in range(1, n + 1):
        t = norm_line(code_lines[ln - 1])
        if not t:
            continue

        # 1) IF 入栈（排除 ELSIF）
        if is_if_start(t) and not is_elsif(t):
            stack.append(_IfFrame(if_line=ln, current_branch_head=ln, branches=[]))
            continue

        # 2) 分支切换：ELSIF / ELSE
        if is_elsif(t) or is_else(t):
            if not stack:
                continue
            frame = stack[-1]

            prev_head = frame.current_branch_head
            prev_head_end = scan_if_header_end(prev_head, code_lines)
            body_start = prev_head_end + 1
            body_end = ln - 1
            frame.branches.append((frame.current_branch_head, body_start, body_end))

            frame.current_branch_head = ln
            continue

        # 3) IF 结束
        if is_end_if(t):
            if not stack:
                continue
            frame = stack.pop()

            prev_head = frame.current_branch_head
            prev_head_end = scan_if_header_end(prev_head, code_lines)
            body_start = prev_head_end + 1
            body_end = ln - 1
            frame.branches.append((frame.current_branch_head, body_start, body_end))

            if_touched = False

            # 分支触及 → 补分支头
            for branch_head, b_start, b_end in frame.branches:
                if b_start <= b_end:
                    touched_branch = any((b_start <= L <= b_end) for L in patched)
                    if touched_branch:
                        patched.add(branch_head)
                        if_touched = True

            if ensure_end_if and if_touched:
                patched.add(ln)

            continue

    return patched

def _scan_case_start(ln: int, code_lines: List[str]) -> int:
    """从 ln 向上找最近的 CASE 头。"""
    for i in range(ln, 0, -1):
        t = clean_st_line(code_lines[i - 1]).strip()
        if RE_CASE_HEAD.search(t):
            return i
    return ln

def patch_case_structure(
    line_numbers: Iterable[int],
    code_lines: List[str],
    ensure_end_case: bool = True,
    include_branch_headers: bool = True,
) -> Set[int]:
    """
    结构补全 CASE：
      - 命中 CASE 区域内部 → 补 CASE 头尾
      - 命中 body 行但缺 label → 回溯补最近 label/ELSE
      - 源码本身空 CASE（无任何 label/ELSE）→ 删头尾
    """
    n = len(code_lines)
    lines: Set[int] = set(int(ln) for ln in line_numbers if 1 <= int(ln) <= n)
    if not lines:
        return lines

    case_regions: Set[Tuple[int, int]] = set()

    for ln in sorted(lines):
        txt = clean_st_line(code_lines[ln - 1]).strip()
        u = txt.upper()

        if RE_CASE_HEAD.search(u):
            cs = ln
            ce = scan_matching_end_case(cs, code_lines)
            if 1 <= cs <= ce <= n:
                case_regions.add((cs, ce))
            continue

        if RE_END_CASE.search(u):
            cs = _scan_case_start(ln, code_lines)
            if cs != ln:
                case_regions.add((cs, ln))
            continue

        if is_case_label_line(txt) or RE_ELSE_LINE.search(txt):
            cs = _scan_case_start(ln, code_lines)
            if cs != ln and RE_CASE_HEAD.search(clean_st_line(code_lines[cs - 1]).strip()):
                ce = scan_matching_end_case(cs, code_lines)
                if 1 <= cs <= ce <= n:
                    case_regions.add((cs, ce))

    if not case_regions:
        return lines

    for (cs, ce) in sorted(case_regions):
        inner_hits = sorted([x for x in lines if cs < x < ce])
        if not inner_hits:
            continue

        # 源码层面：检查 CASE 内是否有任何 label/ELSE
        has_any_label = False
        for k in range(cs + 1, ce):
            t = clean_st_line(code_lines[k - 1]).strip()
            if is_case_label_line(t) or RE_ELSE_LINE.search(t):
                has_any_label = True
                break

        # 空 CASE：删头尾
        if not has_any_label:
            lines.discard(cs)
            lines.discard(ce)
            continue

        lines.add(cs)
        if ensure_end_case:
            lines.add(ce)

        if include_branch_headers:
            for hit in inner_hits:
                hit_txt = clean_st_line(code_lines[hit - 1]).strip()
                if is_case_label_line(hit_txt) or RE_ELSE_LINE.search(hit_txt) or RE_CASE_HEAD.search(hit_txt):
                    continue

                # 向上回溯最近 label/ELSE
                for up in range(hit - 1, cs, -1):
                    up_txt = clean_st_line(code_lines[up - 1]).strip()
                    if is_case_label_line(up_txt) or RE_ELSE_LINE.search(up_txt):
                        lines.add(up)
                        break

    return lines
