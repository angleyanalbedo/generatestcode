# st_slicer/blocks/st_text.py

from __future__ import annotations
import re

# --- 轻量级：去掉 ST 注释，便于识别关键字 ---
_BLOCK_COMMENT_RE = re.compile(r"\(\*.*?\*\)", re.DOTALL)
_LINE_COMMENT_RE = re.compile(r"//.*?$", re.MULTILINE)

# 清理：去掉行内 (*...*) 注释，去掉 // 后内容
_BLOCK_INLINE = re.compile(r"\(\*.*?\*\)")
_LINE_COMMENT = re.compile(r"//.*$")

def strip_st_comments(s: str) -> str:
    s = _BLOCK_COMMENT_RE.sub("", s)
    s = _LINE_COMMENT_RE.sub("", s)
    return s

def clean_st_line(line: str) -> str:
    """清理：去掉 // 与行内 (*...*)，便于关键字/分号/括号识别。"""
    line = _LINE_COMMENT.sub("", line)
    line = _BLOCK_INLINE.sub("", line)
    return line

def norm_line(code_line: str) -> str:
    """去注释、去空白、统一大写，便于关键字识别。"""
    t = strip_st_comments(code_line).strip()
    return t.upper()

# 头部正则（词边界）
RE_IF_HEAD     = re.compile(r"^\s*IF\b", re.IGNORECASE)
RE_ELSIF_HEAD  = re.compile(r"^\s*ELSIF\b", re.IGNORECASE)
RE_ELSE_HEAD   = re.compile(r"^\s*ELSE\b", re.IGNORECASE)

RE_FOR_HEAD    = re.compile(r"^\s*FOR\b", re.IGNORECASE)
RE_CASE_HEAD   = re.compile(r"^\s*CASE\b", re.IGNORECASE)
RE_WHILE_HEAD  = re.compile(r"^\s*WHILE\b", re.IGNORECASE)
RE_REPEAT_HEAD = re.compile(r"^\s*REPEAT\b", re.IGNORECASE)

RE_ELSIF = re.compile(r"\bELSIF\b", re.IGNORECASE)
RE_THEN = re.compile(r"\bTHEN\b", re.IGNORECASE)

# END_* 正则
RE_END_IF     = re.compile(r"\bEND_IF\b", re.IGNORECASE)
RE_END_FOR    = re.compile(r"\bEND_FOR\b", re.IGNORECASE)
RE_END_CASE   = re.compile(r"\bEND_CASE\b", re.IGNORECASE)
RE_END_WHILE  = re.compile(r"\bEND_WHILE\b", re.IGNORECASE)
RE_END_REPEAT = re.compile(r"\bEND_REPEAT\b", re.IGNORECASE)

# CASE 分支 label：包含 ":" 且不包含 ":="（赋值）
RE_COLON  = re.compile(r":(?!\=)")
RE_ASSIGN = re.compile(r":=")

# ELSE 分支头（CASE 里也可能出现 ELSE/ELSE:）
RE_ELSE_LINE = re.compile(r"^\s*ELSE\b", re.IGNORECASE)

def is_if_start(u: str) -> bool:
    """判断 IF 头开始（排除 ELSIF）。"""
    t = u.strip().upper()
    if not t.startswith("IF "):
        return False
    if t.startswith("ELSIF "):
        return False
    return True

def is_elsif(u: str) -> bool:
    return u.strip().upper().startswith("ELSIF ")

def is_else(u: str) -> bool:
    t = u.strip().upper()
    return t == "ELSE" or t.startswith("ELSE ")

def is_end_if(u: str) -> bool:
    return u.strip().upper().startswith("END_IF")

def is_case_label_line(text: str) -> bool:
    if RE_ASSIGN.search(text):
        return False
    return RE_COLON.search(text) is not None

def is_substantive_line(line: str) -> bool:
    """判断一行是否为“实质内容”（非空、非纯注释）。"""
    t = strip_st_comments(line).strip()
    return t != ""

def update_ctrl_depth(text: str, depth: int, *, clamp_negative: bool = True) -> int:
    """
    控制结构深度更新：用于 split/merge 时避免切断 IF/CASE/FOR/WHILE/REPEAT。
    """
    u = clean_st_line(text).upper()

    # END_* 先减
    depth -= len(RE_END_IF.findall(u))
    depth -= len(RE_END_FOR.findall(u))
    depth -= len(RE_END_CASE.findall(u))
    depth -= len(RE_END_WHILE.findall(u))
    depth -= len(RE_END_REPEAT.findall(u))

    # 头部后加（IF 排除 ELSIF）
    tmp = RE_ELSIF.sub("", u)
    if RE_IF_HEAD.search(tmp):
        depth += 1
    if RE_FOR_HEAD.search(u):
        depth += 1
    if RE_CASE_HEAD.search(u):
        depth += 1
    if RE_WHILE_HEAD.search(u):
        depth += 1
    if RE_REPEAT_HEAD.search(u):
        depth += 1

    if clamp_negative and depth < 0:
        depth = 0
    return depth
