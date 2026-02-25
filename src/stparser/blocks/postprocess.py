# st_slicer/blocks/postprocess.py

from __future__ import annotations
from typing import List, Set, Tuple, Optional

from .types import FunctionalBlock
from .st_text import (
    strip_st_comments,
    is_if_start,
    clean_st_line,
    is_case_label_line,
    RE_CASE_HEAD,
    RE_ELSE_LINE,
    RE_FOR_HEAD,
    RE_WHILE_HEAD,
    RE_REPEAT_HEAD,
)
from .structure_common import (
    scan_matching_end_if,
    scan_matching_end_case,
    scan_matching_end_for,
    scan_matching_end_while,
    scan_matching_end_repeat,
)
from .st_text import update_ctrl_depth

from ..ast.nodes import (
    Expr, Stmt,
    VarRef, ArrayAccess, FieldAccess,
    Literal, BinOp, CallExpr,
    Assignment, IfStmt, ForStmt, CallStmt, WhileStmt, RepeatStmt,
    CaseStmt, CaseEntry, CaseCond,
)

def collect_vars_in_expr(
    expr: Optional[Expr],
    vars_used: Set[str],
    funcs_used: Optional[Set[str]] = None,
) -> None:
    if expr is None:
        return

    if isinstance(expr, VarRef):
        vars_used.add(expr.name)

    elif isinstance(expr, ArrayAccess):
        collect_vars_in_expr(expr.base, vars_used, funcs_used)
        collect_vars_in_expr(expr.index, vars_used, funcs_used)

    elif isinstance(expr, FieldAccess):
        collect_vars_in_expr(expr.base, vars_used, funcs_used)

    elif isinstance(expr, BinOp):
        collect_vars_in_expr(expr.left, vars_used, funcs_used)
        collect_vars_in_expr(expr.right, vars_used, funcs_used)

    elif isinstance(expr, CallExpr):
        # func 名按“函数名”统计，不当变量
        if funcs_used is not None:
            funcs_used.add(expr.func)
        for a in expr.args:
            collect_vars_in_expr(a, vars_used, funcs_used)

    elif isinstance(expr, Literal):
        return

    else:
        # 未来扩展 Expr 子类时再补
        return


def collect_vars_in_stmt(
    stmt: Stmt,
    vars_used: Set[str],
    funcs_used: Optional[Set[str]] = None,
) -> None:
    if isinstance(stmt, Assignment):
        collect_vars_in_expr(stmt.target, vars_used, funcs_used)
        collect_vars_in_expr(stmt.value, vars_used, funcs_used)

    elif isinstance(stmt, IfStmt):
        collect_vars_in_expr(stmt.cond, vars_used, funcs_used)
        for s in stmt.then_body:
            collect_vars_in_stmt(s, vars_used, funcs_used)
        for cond, body in stmt.elif_branches:
            collect_vars_in_expr(cond, vars_used, funcs_used)
            for s in body:
                collect_vars_in_stmt(s, vars_used, funcs_used)
        for s in stmt.else_body:
            collect_vars_in_stmt(s, vars_used, funcs_used)

    elif isinstance(stmt, ForStmt):
        # 循环变量要声明
        vars_used.add(stmt.var)
        collect_vars_in_expr(stmt.start, vars_used, funcs_used)
        collect_vars_in_expr(stmt.end, vars_used, funcs_used)
        collect_vars_in_expr(stmt.step, vars_used, funcs_used)
        for s in stmt.body:
            collect_vars_in_stmt(s, vars_used, funcs_used)

    elif isinstance(stmt, WhileStmt):
        collect_vars_in_expr(stmt.cond, vars_used, funcs_used)
        for s in stmt.body:
            collect_vars_in_stmt(s, vars_used, funcs_used)

    elif isinstance(stmt, RepeatStmt):
        # 先 body，再 until
        for s in stmt.body:
            collect_vars_in_stmt(s, vars_used, funcs_used)
        collect_vars_in_expr(stmt.until, vars_used, funcs_used)

    elif isinstance(stmt, CaseStmt):
        # 关键修复：你的 CaseStmt 用 cond，不是 expr
        collect_vars_in_expr(stmt.cond, vars_used, funcs_used)

        # entries -> entry.body
        for entry in stmt.entries:
            for s in entry.body:
                collect_vars_in_stmt(s, vars_used, funcs_used)

        # else_body
        for s in stmt.else_body:
            collect_vars_in_stmt(s, vars_used, funcs_used)

    elif isinstance(stmt, CallStmt):
        # fb_name 不是变量名，不放 vars_used；参数表达式需要遍历
        for a in stmt.args:
            collect_vars_in_expr(a, vars_used, funcs_used)

    else:
        return


def collect_vars_in_block(stmts: List[Stmt]) -> Set[str]:
    vars_used: Set[str] = set()
    for s in stmts:
        collect_vars_in_stmt(s, vars_used)
    return vars_used

def is_meaningful_block(block: FunctionalBlock, code_lines: List[str]) -> bool:
    lines = [
        code_lines[ln - 1]
        for ln in sorted(block.line_numbers)
        if 1 <= ln <= len(code_lines)
    ]

    depth = 0
    went_negative = False
    for t in lines:
        depth = update_ctrl_depth(t, depth, clamp_negative=False)
        if depth < 0:
            went_negative = True

    balanced = (depth == 0) and (not went_negative)
    min_len_ok = (len(lines) >= 10)
    return balanced and min_len_ok


def _remove_empty_ifs_in_block(block: FunctionalBlock, code_lines: List[str]) -> None:
    if not block.line_numbers:
        return

    ln_set = set(block.line_numbers)
    to_remove: Set[int] = set()
    n = len(code_lines)

    for ln in sorted(block.line_numbers):
        if not (1 <= ln <= n):
            continue

        raw = code_lines[ln - 1]
        stripped = strip_st_comments(raw).strip()
        upper = stripped.upper()

        if not is_if_start(upper):
            continue

        end_ln = scan_matching_end_if(ln, code_lines)
        if not (1 <= end_ln <= n):
            continue

        has_content = False
        for inner_ln in ln_set:
            if ln < inner_ln < end_ln:
                inner_raw = code_lines[inner_ln - 1]
                inner_text = strip_st_comments(inner_raw).strip()
                if inner_text != "":
                    has_content = True
                    break

        if not has_content:
            to_remove.add(ln)
            if end_ln in ln_set:
                to_remove.add(end_ln)

    if to_remove:
        block.line_numbers = sorted(x for x in block.line_numbers if x not in to_remove)


def remove_empty_ifs_in_blocks(blocks: List[FunctionalBlock], code_lines: List[str]) -> List[FunctionalBlock]:
    for b in blocks:
        _remove_empty_ifs_in_block(b, code_lines)
    return blocks


def _remove_empty_loops_in_block(block: FunctionalBlock, code_lines: List[str]) -> None:
    if not block.line_numbers:
        return

    ln_set = set(block.line_numbers)
    n = len(code_lines)
    to_remove: Set[int] = set()

    def has_content_between(a: int, b: int) -> bool:
        for inner_ln in ln_set:
            if a < inner_ln < b:
                inner_raw = code_lines[inner_ln - 1]
                inner_text = strip_st_comments(inner_raw).strip()
                if inner_text != "":
                    return True
        return False

    for ln in sorted(block.line_numbers):
        if not (1 <= ln <= n):
            continue

        t = strip_st_comments(code_lines[ln - 1]).strip()
        u = t.upper()

        if RE_FOR_HEAD.search(u):
            end_ln = scan_matching_end_for(ln, code_lines)
            if 1 <= end_ln <= n and not has_content_between(ln, end_ln):
                to_remove.add(ln)
                if end_ln in ln_set:
                    to_remove.add(end_ln)

        if RE_WHILE_HEAD.search(u):
            end_ln = scan_matching_end_while(ln, code_lines)
            if 1 <= end_ln <= n and not has_content_between(ln, end_ln):
                to_remove.add(ln)
                if end_ln in ln_set:
                    to_remove.add(end_ln)

        if RE_REPEAT_HEAD.search(u):
            end_ln = scan_matching_end_repeat(ln, code_lines)
            if 1 <= end_ln <= n and not has_content_between(ln, end_ln):
                to_remove.add(ln)
                if end_ln in ln_set:
                    to_remove.add(end_ln)

    if to_remove:
        block.line_numbers = sorted(x for x in block.line_numbers if x not in to_remove)


def remove_empty_loops_in_blocks(blocks: List[FunctionalBlock], code_lines: List[str]) -> List[FunctionalBlock]:
    for b in blocks:
        _remove_empty_loops_in_block(b, code_lines)
    return blocks


def remove_empty_cases_in_blocks(blocks: List[FunctionalBlock], code_lines: List[str]) -> List[FunctionalBlock]:
    n = len(code_lines)

    def is_empty_case(cs: int, ce: int) -> bool:
        for ln in range(cs + 1, ce):
            t = clean_st_line(code_lines[ln - 1]).strip()
            if is_case_label_line(t) or RE_ELSE_LINE.search(t):
                return False
        return True

    new_blocks: List[FunctionalBlock] = []
    for b in blocks:
        lnset = set(x for x in b.line_numbers if 1 <= x <= n)
        case_pairs: List[Tuple[int, int]] = []

        for ln in list(lnset):
            if RE_CASE_HEAD.search(clean_st_line(code_lines[ln - 1]).upper()):
                cs = ln
                ce = scan_matching_end_case(cs, code_lines)
                if ce in lnset:
                    case_pairs.append((cs, ce))

        for (cs, ce) in case_pairs:
            if is_empty_case(cs, ce):
                lnset.discard(cs)
                lnset.discard(ce)

        b.line_numbers = sorted(lnset)
        new_blocks.append(b)

    return new_blocks


def dedup_blocks_by_code(blocks: List[FunctionalBlock], code_lines: List[str]) -> List[FunctionalBlock]:
    seen: Set[str] = set()
    uniq: List[FunctionalBlock] = []
    n = len(code_lines)

    for b in blocks:
        if not b.line_numbers:
            continue
        body = []
        for ln in sorted(set(b.line_numbers)):
            if 1 <= ln <= n:
                body.append(code_lines[ln - 1].rstrip())
        key = "\n".join(body)
        if key in seen:
            continue
        seen.add(key)
        uniq.append(b)

    return uniq
