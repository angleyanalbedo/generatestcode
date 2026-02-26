# ir/ir_builder.py
from __future__ import annotations

from typing import List, Optional, Tuple, Dict
from ..ast import nodes as astn
from ..ast.nodes import (
    SourceLocation,
    Stmt,
    Expr,
    Assignment,
    IfStmt,
    ForStmt,
    CallStmt,
    CaseStmt,
    WhileStmt,
    RepeatStmt,
    VarRef,
    Literal,
    BinOp,
    ArrayAccess,
    FieldAccess,
    CallExpr, 
)
from .ir_nodes import (
    IRInstr,
    IRLocation,
    IRAssign,
    IRBinOp,
    IRCall,
    IRBranchCond,
    IRLabel,
    IRGoto,
)


class IRBuilder:
    def __init__(self, pou_name: str):
        self.pou_name = pou_name

        # 统一用 instrs 这个名字
        self.instrs: List[IRInstr] = []

        # IR index -> AST 语句
        self.ir2ast_stmt: List[Optional[Stmt]] = []

        # AST 语句 -> IR indices
        #self.ast2ir_indices: Dict[Stmt, List[int]] = {}

        self.temp_id: int = 0
        self.label_id: int = 0

    # 统一的 emit 出口
    def emit(self, instr: IRInstr, ast_stmt: Optional[Stmt] = None) -> int:
        idx = len(self.instrs)
        # 可选：把 ast_stmt 挂在 instr 上，便于调试
        setattr(instr, "ast_stmt", ast_stmt)

        self.instrs.append(instr)
        self.ir2ast_stmt.append(ast_stmt)

        # if ast_stmt is not None:
        #     self.ast2ir_indices.setdefault(ast_stmt, []).append(idx)

        return idx

    def new_temp(self) -> str:
        self.temp_id += 1
        return f"t{self.temp_id}"

    def new_label(self, prefix: str) -> str:
        self.label_id += 1
        return f"{prefix}_{self.label_id}"

    def _loc(self, ast_node) -> IRLocation:
        loc: SourceLocation = ast_node.loc
        return IRLocation(
            pou=self.pou_name,
            file=loc.file,
            line=loc.line,
        )

    # ========= 表达式 =========

    def lower_expr(self, expr: Expr) -> str:
        if isinstance(expr, VarRef):
            return expr.name

        if isinstance(expr, Literal):
            t = self.new_temp()
            self.emit(
                IRAssign(
                    target=t,
                    src=str(expr.value),
                    loc=self._loc(expr),
                ),
                ast_stmt=None,   # 表达式级 IR，不绑定到语句
            )
            return t

        if isinstance(expr, BinOp):
            left = self.lower_expr(expr.left)
            right = self.lower_expr(expr.right)
            t = self.new_temp()
            self.emit(
                IRBinOp(
                    dest=t,
                    op=expr.op,
                    left=left,
                    right=right,
                    loc=self._loc(expr),
                ),
                ast_stmt=None,
            )
            return t

        if isinstance(expr, CallExpr):
            # 1) 对每个实参做 lower_expr
            arg_temps = [self.lower_expr(arg) for arg in expr.args]

            # 2) 没有参数：用常量 0 占位
            if not arg_temps:
                t = self.new_temp()
                self.emit(
                    IRAssign(
                        target=t,
                        src="0",
                        loc=self._loc(expr),
                    ),
                    ast_stmt=None,
                )
                return t

            # 3) 只有一个参数，直接返回
            if len(arg_temps) == 1:
                return arg_temps[0]

            # 4) 多个参数：arg0 + arg1 + arg2 + ...
            result = arg_temps[0]
            for arg_temp in arg_temps[1:]:
                t = self.new_temp()
                self.emit(
                    IRBinOp(
                        dest=t,
                        op="+",
                        left=result,
                        right=arg_temp,
                        loc=self._loc(expr),
                    ),
                    ast_stmt=None,
                )
                result = t

            return result

        raise NotImplementedError(f"lower_expr not implemented for {type(expr)}")


    def _lower_lvalue(self, expr: Expr) -> str:
        if isinstance(expr, VarRef):
            return expr.name
        raise NotImplementedError(f"lvalue not supported for {type(expr)}")

    # ========= 语句入口 =========

    def lower_stmt(self, stmt: Stmt):
        if isinstance(stmt, Assignment):
            self._lower_assignment(stmt)
        elif isinstance(stmt, IfStmt):
            self._lower_if(stmt)
        elif isinstance(stmt, ForStmt):
            self._lower_for(stmt)
        elif isinstance(stmt, WhileStmt):
            self._lower_while(stmt)
        elif isinstance(stmt, RepeatStmt):
            self._lower_repeat(stmt)
        elif isinstance(stmt, CaseStmt):
            self._lower_case(stmt)
        elif isinstance(stmt, CallStmt):
            self._lower_call(stmt)
        else:
            pass

    # ========= 各类语句 =========

    def _lower_assignment(self, stmt: Assignment):
        rhs = self.lower_expr(stmt.value)
        target = self._lower_lvalue(stmt.target)
        self.emit(
            IRAssign(
                target=target,
                src=rhs,
                loc=self._loc(stmt),
            ),
            ast_stmt=stmt,   # 关键：绑定到这条 Assignment 语句
        )

    def _lower_call(self, stmt: CallStmt):
        arg_vars: List[str] = [self.lower_expr(a) for a in stmt.args]
        self.emit(
            IRCall(
                dest=None,
                callee=stmt.fb_name,
                args=arg_vars,
                loc=self._loc(stmt),
            ),
            ast_stmt=stmt,
        )

    def _lower_if(self, stmt: IfStmt):
        branches: List[Tuple[Expr, List[Stmt]]] = []
        branches.append((stmt.cond, stmt.then_body))
        elif_list: List[Tuple[Expr, List[Stmt]]] = getattr(stmt, "elif_branches", [])
        branches.extend(elif_list)

        has_else = bool(stmt.else_body)
        label_end = self.new_label("endif")
        label_else: Optional[str] = self.new_label("else") if has_else else None

        for idx, (cond_expr, then_body) in enumerate(branches):
            is_last = (idx == len(branches) - 1)
            cond_var = self.lower_expr(cond_expr)
            label_then = self.new_label(f"then_{idx}")

            if is_last:
                label_false = label_else if has_else and label_else is not None else label_end
            else:
                label_false = self.new_label(f"if_next_{idx}")

            self.emit(
                IRBranchCond(
                    cond=cond_var,
                    true_label=label_then,
                    false_label=label_false,
                    loc=self._loc(cond_expr),
                ),
                ast_stmt=stmt,
            )

            self.emit(
                IRLabel(
                    name=label_then,
                    loc=self._loc(stmt),
                ),
                ast_stmt=stmt,
            )
            for s in then_body:
                self.lower_stmt(s)
            self.emit(
                IRGoto(
                    target_label=label_end,
                    loc=self._loc(stmt),
                ),
                ast_stmt=stmt,
            )

            if not is_last:
                self.emit(
                    IRLabel(
                        name=label_false,
                        loc=self._loc(stmt),
                    ),
                    ast_stmt=stmt,
                )

        if has_else and label_else is not None:
            self.emit(
                IRLabel(
                    name=label_else,
                    loc=self._loc(stmt),
                ),
                ast_stmt=stmt,
            )
            for s in stmt.else_body:
                self.lower_stmt(s)
            self.emit(
                IRGoto(
                    target_label=label_end,
                    loc=self._loc(stmt),
                ),
                ast_stmt=stmt,
            )

        self.emit(
            IRLabel(
                name=label_end,
                loc=self._loc(stmt),
            ),
            ast_stmt=stmt,
        )

    def _lower_for(self, stmt: ForStmt):
        loop_var_name: str = stmt.var

        start_val = self.lower_expr(stmt.start)
        self.emit(
            IRAssign(
                target=loop_var_name,
                src=start_val,
                loc=self._loc(stmt),
            ),
            ast_stmt=stmt,
        )

        label_header = self.new_label("for_header")
        label_body = self.new_label("for_body")
        label_end = self.new_label("for_end")

        self.emit(IRLabel(name=label_header, loc=self._loc(stmt)), ast_stmt=stmt)

        end_val = self.lower_expr(stmt.end)
        t_cond = self.new_temp()
        self.emit(
            IRBinOp(
                dest=t_cond,
                op="<=",
                left=loop_var_name,
                right=end_val,
                loc=self._loc(stmt),
            ),
            ast_stmt=stmt,
        )

        self.emit(
            IRBranchCond(
                cond=t_cond,
                true_label=label_body,
                false_label=label_end,
                loc=self._loc(stmt),
            ),
            ast_stmt=stmt,
        )

        self.emit(IRLabel(name=label_body, loc=self._loc(stmt)), ast_stmt=stmt)
        for s in stmt.body:
            self.lower_stmt(s)

        if stmt.step is not None:
            step_val = self.lower_expr(stmt.step)
        else:
            t_step = self.new_temp()
            self.emit(
                IRAssign(
                    target=t_step,
                    src="1",
                    loc=self._loc(stmt),
                ),
                ast_stmt=stmt,
            )
            step_val = t_step

        t_next = self.new_temp()
        self.emit(
            IRBinOp(
                dest=t_next,
                op="+",
                left=loop_var_name,
                right=step_val,
                loc=self._loc(stmt),
            ),
            ast_stmt=stmt,
        )
        self.emit(
            IRAssign(
                target=loop_var_name,
                src=t_next,
                loc=self._loc(stmt),
            ),
            ast_stmt=stmt,
        )

        self.emit(
            IRGoto(
                target_label=label_header,
                loc=self._loc(stmt),
            ),
            ast_stmt=stmt,
        )
        self.emit(
            IRLabel(
                name=label_end,
                loc=self._loc(stmt),
            ),
            ast_stmt=stmt,
        )
    
    def _lower_while(self, stmt: WhileStmt):
        label_head = self.new_label("while_head")
        label_body = self.new_label("while_body")
        label_end  = self.new_label("while_end")

        self.emit(IRLabel(name=label_head, loc=self._loc(stmt)), ast_stmt=stmt)

        cond_var = self.lower_expr(stmt.cond)
        self.emit(
            IRBranchCond(cond=cond_var, true_label=label_body, false_label=label_end, loc=self._loc(stmt)),
            ast_stmt=stmt,
        )

        self.emit(IRLabel(name=label_body, loc=self._loc(stmt)), ast_stmt=stmt)
        for s in stmt.body:
            self.lower_stmt(s)

        self.emit(IRGoto(target_label=label_head, loc=self._loc(stmt)), ast_stmt=stmt)
        self.emit(IRLabel(name=label_end, loc=self._loc(stmt)), ast_stmt=stmt)

    def _lower_repeat(self, stmt: RepeatStmt):
        label_body = self.new_label("repeat_body")
        label_end  = self.new_label("repeat_end")

        self.emit(IRLabel(name=label_body, loc=self._loc(stmt)), ast_stmt=stmt)

        for s in stmt.body:
            self.lower_stmt(s)

        # REPEAT ... UNTIL cond END_REPEAT
        # UNTIL 为真则退出，否则继续
        until_var = self.lower_expr(stmt.until)
        self.emit(
            IRBranchCond(cond=until_var, true_label=label_end, false_label=label_body, loc=self._loc(stmt)),
            ast_stmt=stmt,
        )
        self.emit(IRLabel(name=label_end, loc=self._loc(stmt)), ast_stmt=stmt)

    def _lower_case(self, stmt: CaseStmt):
        label_end  = self.new_label("endcase")
        label_else = self.new_label("case_else") if stmt.else_body else None

        # 让所有分支至少控制依赖于 selector（保守，不做精确标签匹配）
        cond_var = self.lower_expr(stmt.cond)

        next_label = None
        for i, entry in enumerate(stmt.entries):
            label_branch = self.new_label(f"case_{i}")
            next_label = self.new_label(f"case_next_{i}") if i < len(stmt.entries) - 1 else (label_else or label_end)

            # 保守：以 cond_var 作为“是否进入该分支”的门控
            self.emit(
                IRBranchCond(cond=cond_var, true_label=label_branch, false_label=next_label, loc=self._loc(stmt)),
                ast_stmt=stmt,
            )

            self.emit(IRLabel(name=label_branch, loc=self._loc(stmt)), ast_stmt=stmt)
            for s in entry.body:
                self.lower_stmt(s)
            self.emit(IRGoto(target_label=label_end, loc=self._loc(stmt)), ast_stmt=stmt)

            # next label
            self.emit(IRLabel(name=next_label, loc=self._loc(stmt)), ast_stmt=stmt)

        if stmt.else_body and label_else is not None:
            # 如果上面最后一个 next_label 已经是 label_else，这里会再落一次 else；可按你的实现微调
            self.emit(IRLabel(name=label_else, loc=self._loc(stmt)), ast_stmt=stmt)
            for s in stmt.else_body:
                self.lower_stmt(s)
            self.emit(IRGoto(target_label=label_end, loc=self._loc(stmt)), ast_stmt=stmt)

        self.emit(IRLabel(name=label_end, loc=self._loc(stmt)), ast_stmt=stmt)

