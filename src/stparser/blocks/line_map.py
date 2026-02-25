# st_slicer/blocks/line_map.py

from __future__ import annotations
from typing import List, Set

from ..ast.nodes import (
    Stmt, IfStmt, CaseStmt, ForStmt, WhileStmt, RepeatStmt,
    Assignment, CallStmt,
)
from .st_text import clean_st_line
from .structure_common import (
    scan_matching_end_if,
    scan_matching_end_case,
    scan_matching_end_for,
    scan_matching_end_while,
    scan_matching_end_repeat,
)
from .structure_if_case_loop import scan_if_header_end


def _scan_stmt_end(line_start: int, code_lines: List[str]) -> int:
    """
    扫描“普通语句”（赋值/函数调用等）的结束行：
      - 以分号 ';' 作为语句结束标志（ST 常规）
      - 兼容多行表达式：跟踪括号深度，直到括号闭合且遇到 ';'
    这可以修复：
      radius := ESQR((...)+
                     (...)+
                     (...));
    只切到第一行导致缺右括号/后半段的问题。
    """
    n = len(code_lines)
    if line_start < 1 or line_start > n:
        return line_start

    paren = 0
    for ln in range(line_start, n + 1):
        t = clean_st_line(code_lines[ln - 1])
        if not t.strip():
            continue

        # 括号深度（保守：直接数 '(' ')'）
        paren += t.count("(")
        paren -= t.count(")")

        if ";" in t and paren <= 0:
            return ln

    return line_start


def stmts_to_line_numbers(stmts: List[Stmt], code_lines: List[str]) -> List[int]:
    """
    把语句集合映射为源码行号集合，并按行号排序。

    针对控制结构：
      - IfStmt：加入 IF 头多行直到 THEN；加入匹配 END_IF
      - CaseStmt/ForStmt/WhileStmt/RepeatStmt：加入头与匹配 END_*

    针对普通语句（Assignment/CallStmt 等）：
      - 加入起始行，并向下补齐到语句分号结束行（多行语句修复）
    """
    sliced_lines: Set[int] = set()
    n = len(code_lines)

    for st in stmts:
        line_no = getattr(st.loc, "line", None)
        if line_no is None or not (1 <= line_no <= n):
            continue

        if isinstance(st, IfStmt):
            header_end = scan_if_header_end(line_no, code_lines)
            for ln in range(line_no, min(header_end, n) + 1):
                sliced_lines.add(ln)

            end_if_ln = scan_matching_end_if(line_no, code_lines)
            if 1 <= end_if_ln <= n:
                sliced_lines.add(end_if_ln)

        elif isinstance(st, CaseStmt):
            sliced_lines.add(line_no)
            end_ln = scan_matching_end_case(line_no, code_lines)
            if 1 <= end_ln <= n:
                sliced_lines.add(end_ln)

        elif isinstance(st, ForStmt):
            sliced_lines.add(line_no)
            end_ln = scan_matching_end_for(line_no, code_lines)
            if 1 <= end_ln <= n:
                sliced_lines.add(end_ln)

        elif isinstance(st, WhileStmt):
            sliced_lines.add(line_no)
            end_ln = scan_matching_end_while(line_no, code_lines)
            if 1 <= end_ln <= n:
                sliced_lines.add(end_ln)

        elif isinstance(st, RepeatStmt):
            sliced_lines.add(line_no)
            end_ln = scan_matching_end_repeat(line_no, code_lines)
            if 1 <= end_ln <= n:
                sliced_lines.add(end_ln)

        else:
            # 普通语句：补齐到分号结束（修复多行赋值/调用）
            end_ln = _scan_stmt_end(line_no, code_lines)
            for ln in range(line_no, min(end_ln, n) + 1):
                sliced_lines.add(ln)

    return sorted(sliced_lines)
