from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Any, Tuple


@dataclass(eq=False)
class SourceLocation:
    file: str
    line: int
    column: int = 0


# ===== Expressions =====

class Expr:
    loc: SourceLocation


@dataclass(eq=False)
class VarRef(Expr):
    name: str
    loc: SourceLocation


@dataclass(eq=False)
class ArrayAccess(Expr):
    base: Expr           # 通常是 VarRef 或 FieldAccess
    index: Expr          # 下标表达式，可是常量/变量/算式
    loc: SourceLocation


@dataclass(eq=False)
class FieldAccess(Expr):
    base: Expr           # 通常是 VarRef 或 ArrayAccess
    field: str           # 字段名，比如 "Pos" / "Status"
    loc: SourceLocation


@dataclass(eq=False)
class Literal(Expr):
    value: Any
    type: str
    loc: SourceLocation


@dataclass(eq=False)
class BinOp(Expr):
    op: str
    left: Expr
    right: Expr
    loc: SourceLocation

#新增：函数/FB 调用表达式
@dataclass(eq=False)
class CallExpr(Expr):
    func: str              # 函数/FB 名字，例如 "Motion_Delta_S"
    args: List[Expr]       # 实际参数表达式列表
    loc: SourceLocation


# ===== Statements =====

class Stmt:
    loc: SourceLocation


@dataclass(eq=False)
class Assignment(Stmt):
    target: Expr
    value: Expr
    loc: SourceLocation


@dataclass(eq=False)
class IfStmt(Stmt):
    cond: Expr
    then_body: List[Stmt]
    elif_branches: List[Tuple[Expr, List[Stmt]]] = field(default_factory=list)
    else_body: List[Stmt] = field(default_factory=list)
    loc: SourceLocation = None


@dataclass(eq=False)
class ForStmt(Stmt):
    var: str
    start: Expr
    end: Expr
    step: Optional[Expr]
    body: List[Stmt]
    loc: SourceLocation


@dataclass(eq=False)
class CallStmt(Stmt):
    fb_name: str
    args: List[Expr]
    loc: SourceLocation

@dataclass(eq=False)
class WhileStmt(Stmt):
    cond: Expr
    body: List[Stmt]
    loc: SourceLocation


@dataclass(eq=False)
class RepeatStmt(Stmt):
    body: List[Stmt]
    until: Expr
    loc: SourceLocation


@dataclass(eq=False)
class CaseCond:
    """
    CASE 分支条件：直接保留语法原文（支持 1 / 1..5 / cast / IDENTIFIER 等）
    """
    text: str
    loc: SourceLocation


@dataclass(eq=False)
class CaseEntry:
    """
    CASE 的一个分支：
      conds:   多个 case_condition（逗号分隔）
      body:    COLON 后的 statement_list
    """
    conds: List[CaseCond]
    body: List[Stmt]
    loc: SourceLocation


@dataclass(eq=False)
class CaseStmt(Stmt):
    """
    CASE cond OF
       ...
    END_CASE
    """
    cond: Expr
    entries: List[CaseEntry]
    else_body: List[Stmt] = field(default_factory=list)
    loc: SourceLocation = None

# ===== POU / Program units =====

@dataclass(eq=False)
class VarDecl:
    name: str
    type: str
    storage: str  # VAR / VAR_INPUT / ...
    init_expr: Optional[Expr]
    loc: SourceLocation


@dataclass(eq=False)
class ProgramDecl:
    name: str
    vars: List[VarDecl]
    body: List[Stmt]
    loc: SourceLocation


@dataclass(eq=False)
class FBDecl:
    name: str
    vars: List[VarDecl]
    body: List[Stmt]
    loc: SourceLocation





def ast_to_dict(node: Any) -> Any:
    """
    将 dataclass 节点递归转换为同时兼容 DependencyAnalyzer 和 STUnparser 的字典。
    """
    if node is None:
        return None

    # 处理列表（如 body, args, var_blocks）
    if isinstance(node, list):
        return [ast_to_dict(item) for item in node]

    # 如果不是 dataclass，直接返回（如字符串、数字）
    if not hasattr(node, "__dataclass_fields__"):
        return node

    result = {}

    # 1. 自动映射 SourceLocation (loc)
    if hasattr(node, "loc") and node.loc:
        result["loc"] = {"line": node.loc.line, "column": node.loc.column}

    # 2. 根据类名进行分支处理（对齐旧版 key）
    cls_name = node.__class__.__name__

    # --- POU 定义 ---
    if isinstance(node, (ProgramDecl, FBDecl)):
        result["unit_type"] = "PROGRAM" if isinstance(node, ProgramDecl) else "FUNCTION_BLOCK"
        result["name"] = node.name
        result["var_blocks"] = ast_to_dict(node.vars)  # 对齐 STUnparser 的 var_blocks
        result["body"] = ast_to_dict(node.body)

    # --- 变量声明 ---
    elif isinstance(node, VarDecl):
        result["name"] = node.name
        result["type"] = node.type
        result["storage"] = node.storage
        result["init_value"] = ast_to_dict(node.init_expr)

    # --- 赋值语句 ---
    elif isinstance(node, Assignment):
        result["stmt_type"] = "assign"
        result["type"] = "assignment"  # 对齐 DependencyAnalyzer
        result["target"] = ast_to_dict(node.target)
        val = ast_to_dict(node.value)
        result["value"] = val  # 对齐 STUnparser
        result["expr"] = val  # 对齐 DependencyAnalyzer

    # --- IF 语句 ---
    elif isinstance(node, IfStmt):
        result["stmt_type"] = "if"
        result["type"] = "if_statement"
        cond = ast_to_dict(node.cond)
        result["cond"] = cond  # 对齐 STUnparser
        result["condition"] = cond  # 对齐 DependencyAnalyzer

        then_b = ast_to_dict(node.then_body)
        result["then_body"] = then_b  # 对齐 STUnparser
        result["then_branch"] = then_b  # 对齐 DependencyAnalyzer

        # 处理 ELSIF
        result["elif_branches"] = [
            {"cond": ast_to_dict(b[0]), "then_body": ast_to_dict(b[1])}
            for b in node.elif_branches
        ]

        else_b = ast_to_dict(node.else_body)
        result["else_body"] = else_b
        result["else_branch"] = else_b

    # --- 循环语句 ---
    elif isinstance(node, ForStmt):
        result["stmt_type"] = "for"
        result["type"] = "for_loop"
        result["var"] = node.var
        result["start"] = ast_to_dict(node.start)
        result["from"] = result["start"]
        result["end"] = ast_to_dict(node.end)
        result["to"] = result["end"]
        result["step"] = ast_to_dict(node.step)
        result["body"] = ast_to_dict(node.body)

    # --- 调用 (Statement & Expression) ---
    elif isinstance(node, (CallStmt, CallExpr)):
        name = node.fb_name if isinstance(node, CallStmt) else node.func
        args = ast_to_dict(node.args)
        result["stmt_type"] = "call"
        result["expr_type"] = "call"
        result["type"] = "func_call"
        result["func_name"] = name
        result["args"] = args  # 对齐 STUnparser
        result["arg_list"] = args  # 对齐 DependencyAnalyzer

    # --- 表达式底层 ---
    elif isinstance(node, VarRef):
        result["expr_type"] = "var"
        result["type"] = "variable"
        result["name"] = node.name

    elif isinstance(node, Literal):
        result["expr_type"] = "literal"
        result["type"] = "constant"
        result["value"] = node.value

    elif isinstance(node, BinOp):
        result["expr_type"] = "binop"
        result["type"] = "binary_op"
        result["op"] = node.op
        result["left"] = ast_to_dict(node.left)
        result["right"] = ast_to_dict(node.right)

    # --- 复合变量处理 (Array/Field) ---
    elif isinstance(node, (ArrayAccess, FieldAccess)):
        # 旧版通常将这些平铺为字符串，为了兼容，我们提供一个文本表达
        result["expr_type"] = "var"
        result["type"] = "variable"
        result["name"] = _flatten_access(node)

    return result


def _flatten_access(node) -> str:
    """内部辅助：将复杂的 ArrayAccess 转回字符串文本以兼容旧版分析"""
    if isinstance(node, VarRef):
        return node.name
    if isinstance(node, ArrayAccess):
        return f"{_flatten_access(node.base)}[{_flatten_access(node.index)}]"
    if isinstance(node, FieldAccess):
        return f"{_flatten_access(node.base)}.{node.field}"
    return str(node)