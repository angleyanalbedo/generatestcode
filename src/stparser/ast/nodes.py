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
