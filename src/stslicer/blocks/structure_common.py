# st_slicer/blocks/structure_common.py

from __future__ import annotations
import re
from typing import List, Optional

from .st_text import (
    clean_st_line,
    RE_ELSIF,
    RE_IF_HEAD, RE_END_IF,
    RE_FOR_HEAD, RE_END_FOR,
    RE_CASE_HEAD, RE_END_CASE,
    RE_WHILE_HEAD, RE_END_WHILE,
    RE_REPEAT_HEAD, RE_END_REPEAT,
)

def scan_matching_end_generic(
    line_start: int,
    code_lines: List[str],
    head_re: re.Pattern,
    end_re: re.Pattern,
) -> Optional[int]:
    """
    从 line_start(1-based) 开始向下扫描，找到与 head_re 对应的 end_re。
    支持同类嵌套（IF in IF, FOR in FOR 等）。
    """
    n = len(code_lines)
    if line_start < 1 or line_start > n:
        return None

    depth = 0
    for ln in range(line_start, n + 1):
        raw = code_lines[ln - 1]
        txt = clean_st_line(raw).strip()
        if not txt:
            continue
        u = txt.upper()

        # 头部（IF 要排除 ELSIF）
        tmp = RE_ELSIF.sub("", u) if head_re is RE_IF_HEAD else u
        if head_re.search(tmp):
            depth += 1

        # 尾部
        if end_re.search(u):
            depth -= len(end_re.findall(u))
            if depth == 0:
                return ln

    return None

def scan_matching_end_if(line_start: int, code_lines: List[str]) -> int:
    end_ln = scan_matching_end_generic(line_start, code_lines, RE_IF_HEAD, RE_END_IF)
    return end_ln if end_ln is not None else line_start

def scan_matching_end_for(line_start: int, code_lines: List[str]) -> int:
    end_ln = scan_matching_end_generic(line_start, code_lines, RE_FOR_HEAD, RE_END_FOR)
    return end_ln if end_ln is not None else line_start

def scan_matching_end_case(line_start: int, code_lines: List[str]) -> int:
    end_ln = scan_matching_end_generic(line_start, code_lines, RE_CASE_HEAD, RE_END_CASE)
    return end_ln if end_ln is not None else line_start

def scan_matching_end_while(line_start: int, code_lines: List[str]) -> int:
    end_ln = scan_matching_end_generic(line_start, code_lines, RE_WHILE_HEAD, RE_END_WHILE)
    return end_ln if end_ln is not None else line_start

def scan_matching_end_repeat(line_start: int, code_lines: List[str]) -> int:
    end_ln = scan_matching_end_generic(line_start, code_lines, RE_REPEAT_HEAD, RE_END_REPEAT)
    return end_ln if end_ln is not None else line_start
