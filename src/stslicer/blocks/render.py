# st_slicer/blocks/render.py

from __future__ import annotations
import re
from typing import List, Optional, Set

from .types import FunctionalBlock
from .st_text import (
    clean_st_line,
    is_substantive_line,
    RE_IF_HEAD,
    RE_ELSIF_HEAD,
    RE_ELSE_HEAD,
    RE_THEN,
)
from .structure_common import scan_matching_end_if
from .structure_if_case_loop import scan_if_header_end


def _extract_if_condition_text(if_start: int, code_lines: List[str]) -> tuple[str, int, str]:
    """
    返回: (cond_str, header_end_line, indent_str)
    """
    header_end = scan_if_header_end(if_start, code_lines)
    header_lines = code_lines[if_start - 1: header_end]

    first_line = header_lines[0] if header_lines else ""
    indent = re.match(r"^\s*", first_line).group(0) if first_line else ""

    merged = " ".join(clean_st_line(x).strip() for x in header_lines if clean_st_line(x).strip())
    u = merged.strip()

    u = re.sub(r"^\s*IF\b", "", u, flags=re.IGNORECASE).strip()
    m = list(RE_THEN.finditer(u))
    if m:
        last = m[-1]
        u = u[: last.start()].strip()

    return u, header_end, indent


def render_block_text(
    block: FunctionalBlock,
    code_lines: List[str],
    *,
    normalize_else_only_if: bool = False,
) -> str:
    """
    根据 block.line_numbers 渲染文本。
    若 normalize_else_only_if=True，则将 THEN 为空、ELSE 非空的 IF
    改写为 IF NOT(cond) THEN ... END_IF。
    """
    n = len(code_lines)
    lnset: Set[int] = set(ln for ln in block.line_numbers if 1 <= ln <= n)
    if not lnset:
        return ""

    out_lines: List[str] = []
    lns = sorted(lnset)
    i = 0

    while i < len(lns):
        ln = lns[i]
        raw = code_lines[ln - 1]

        if not normalize_else_only_if:
            out_lines.append(raw.rstrip("\n"))
            i += 1
            continue

        t0 = clean_st_line(raw).strip()
        if not RE_IF_HEAD.search(t0) or RE_ELSIF_HEAD.search(t0):
            out_lines.append(raw.rstrip("\n"))
            i += 1
            continue

        end_if = scan_matching_end_if(ln, code_lines)
        if end_if <= ln or end_if not in lnset:
            out_lines.append(raw.rstrip("\n"))
            i += 1
            continue

        cond, header_end, indent = _extract_if_condition_text(ln, code_lines)
        if header_end < ln or header_end > n:
            out_lines.append(raw.rstrip("\n"))
            i += 1
            continue

        else_ln: Optional[int] = None
        has_elsif = False
        for k in range(header_end + 1, end_if):
            line_k = clean_st_line(code_lines[k - 1]).strip()
            if RE_ELSIF_HEAD.search(line_k):
                has_elsif = True
                break
            if RE_ELSE_HEAD.search(line_k):
                else_ln = k
                break

        if has_elsif or else_ln is None:
            out_lines.append(raw.rstrip("\n"))
            i += 1
            continue

        then_has = any(
            (k in lnset and is_substantive_line(code_lines[k - 1]))
            for k in range(header_end + 1, else_ln)
        )
        else_has = any(
            (k in lnset and is_substantive_line(code_lines[k - 1]))
            for k in range(else_ln + 1, end_if)
        )

        if then_has or not else_has or not cond:
            out_lines.append(raw.rstrip("\n"))
            i += 1
            continue

        new_head = f"{indent}IF NOT({cond}) THEN"
        out_lines.append(new_head)

        for k in range(else_ln + 1, end_if):
            if k in lnset:
                out_lines.append(code_lines[k - 1].rstrip("\n"))

        out_lines.append(code_lines[end_if - 1].rstrip("\n"))

        while i < len(lns) and lns[i] <= end_if:
            i += 1

    return "\n".join(out_lines).rstrip() + "\n"
