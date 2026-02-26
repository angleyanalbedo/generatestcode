from typing import List,Dict,Any

from stparser.anltr4.generated.IEC61131Parser import IEC61131Parser
from stparser.anltr4.generated.IEC61131ParserVisitor import IEC61131ParserVisitor

# ---------------------------------------------------------
# 2. 自定义 AST 构建器 (Visitor 模式)
# ---------------------------------------------------------

class STAstBuilder(IEC61131ParserVisitor):
    """
    纯字典版 AST 构建器。
    将 ANTLR Parse Tree 转换为松耦合的 Dictionary，完美兼容旧版数据处理流水线。
    """

    # ==========================================
    # 🌟 核心防雷：万能文本提取器
    # ==========================================
    def safe_text(self, obj) -> str:
        """安全提取文本，彻底解决 Token 和 Context 的 API 冲突"""
        if obj is None:
            return ""
        # 1. 如果它是方法 (比如 ctx.identifier)，先调用它获取对象
        if callable(obj):
            try:
                obj = obj()
            except:
                pass

        if obj is None:
            return ""

        # 2. 如果是 Rule Context，调用 getText()
        if hasattr(obj, 'getText'):
            return obj.getText()

        # 3. 如果是 Lexer Token，直接读取 text
        if hasattr(obj, 'text'):
            return obj.text

        return str(obj)

    # ==========================================
    # 1. 顶层结构 (Program, Function Block)
    # ==========================================

    def visitStart(self, ctx: IEC61131Parser.StartContext) -> List[Dict[str, Any]]:
        pous = []
        for elem in ctx.library_element_declaration():
            ast = self.visit(elem)
            if ast:
                # 因为一个文件可能有多个 Program/FB，这里平铺到一个列表中
                if isinstance(ast, list):
                    pous.extend(ast)
                else:
                    pous.append(ast)
        return pous

    # 1. PROGRAM 名字提取
    def visitProgram_declaration(self, ctx: IEC61131Parser.Program_declarationContext) -> Dict[str, Any]:
        return {
            "unit_type": "PROGRAM",
            "name": self.safe_text(getattr(ctx, 'identifier', None)) or "Unnamed",
            "var_blocks": self.visit(ctx.var_decls()) if ctx.var_decls() else [],
            "body": self._extract_body(ctx.body())
        }

    # 2. FB 名字提取
    def visitFunction_block_declaration(self, ctx: IEC61131Parser.Function_block_declarationContext) -> Dict[
        str, Any]:
        return {
            "unit_type": "FUNCTION_BLOCK",
            "name": self.safe_text(getattr(ctx, 'identifier', None)) or "Unnamed",
            "var_blocks": self.visit(ctx.var_decls()) if ctx.var_decls() else [],
            "body": self._extract_body(ctx.body())
        }

    # 3. FUNCTION 名字提取
    def visitFunction_declaration(self, ctx: IEC61131Parser.Function_declarationContext) -> Dict[str, Any]:
        return {
            "unit_type": "FUNCTION",
            "name": self.safe_text(getattr(ctx, 'identifier', None)) or "Unnamed",
            "return_type": self.safe_text(getattr(ctx, 'type_declaration', None)) or "UNKNOWN",
            "var_blocks": self.visit(ctx.var_decls()) if ctx.var_decls() else [],
            "body": self._extract_body(ctx.body())
        }

    # 4. 函数/功能块调用提取 (彻底解决 Symbolic_variableContext 和 NameContext 报错)
    def visitInvocation(self, ctx: IEC61131Parser.InvocationContext) -> Dict[str, Any]:
        # 优先尝试获取 id_，如果没有则获取 symbolic_variable
        func_name = self.safe_text(getattr(ctx, "id_", None))
        if not func_name:
            func_name = self.safe_text(getattr(ctx, "symbolic_variable", None))

        args = []
        for pa in ctx.param_assignment():
            args.append(self.visit(pa))
        for e in ctx.expression():
            args.append(self.visit(e))

        return {
            "stmt_type": "call",
            "func_name": func_name,
            "args": args
        }

    # 5. 作为表达式的调用提取
    def visitPrimary_expression(self, ctx: IEC61131Parser.Primary_expressionContext) -> Dict[str, Any]:
        if ctx.constant():
            return self.visit(ctx.constant())
        if ctx.v:
            return self.visit(ctx.v)
        if ctx.invocation():
            inv = ctx.invocation()

            func_name = self.safe_text(getattr(inv, "id_", None))
            if not func_name:
                func_name = self.safe_text(getattr(inv, "symbolic_variable", None))

            args = []
            for pa in inv.param_assignment(): args.append(self.visit(pa))
            for e in inv.expression(): args.append(self.visit(e))

            return {
                "expr_type": "call",
                "func_name": func_name,
                "args": args
            }

        return {"expr_type": "unknown", "text": self.safe_text(ctx)}

    def _extract_body(self, body_ctx) -> List[Dict]:
        """提取 body 中的 statement_list"""
        if body_ctx and body_ctx.statement_list():
            return self.visit(body_ctx.statement_list())
        return []

    # ==========================================
    # 2. 变量声明 (VAR ... END_VAR)
    # ==========================================

    def visitVar_decls(self, ctx: IEC61131Parser.Var_declsContext) -> List[Dict[str, Any]]:
        vars_list = []
        for vd in ctx.var_decl():
            decls = self.visit(vd)
            if decls:
                vars_list.extend(decls)
        return vars_list

    def visitVar_decl(self, ctx: IEC61131Parser.Var_declContext) -> List[Dict[str, Any]]:
        storage = "VAR"
        vk = ctx.variable_keyword()
        if vk and vk.getChildCount() > 0:
            storage = vk.getChild(0).getText().upper()

        inner = ctx.var_decl_inner()
        if not inner:
            return []

        decls = []
        for id_list_ctx, type_ctx in zip(inner.identifier_list(), inner.type_declaration()):
            type_str = type_ctx.getText()

            # 💡 提取可能的初始化表达式
            init_value = None
            if hasattr(inner, 'expression') and inner.expression():
                init_value = self.visit(inner.expression())
            elif hasattr(type_ctx, 'expression') and type_ctx.expression():
                init_value = self.visit(type_ctx.expression())

            for name_ctx in id_list_ctx.variable_names():
                decls.append({
                    "storage": storage,
                    "name": name_ctx.getText(),
                    "type": type_str,
                    "init_value": init_value
                })
        return decls

    # ==========================================
    # 3. 语句 (Statements)
    # ==========================================

    def visitStatement_list(self, ctx: IEC61131Parser.Statement_listContext) -> List[Dict[str, Any]]:
        stmts = []
        for sctx in ctx.statement():
            stmt = self.visit(sctx)
            if stmt:
                stmts.append(stmt)
        return stmts

    def visitAssignment_statement(self, ctx: IEC61131Parser.Assignment_statementContext) -> Dict[str, Any]:
        return {
            "stmt_type": "assign",
            # target 作为表达式递归处理（兼容数组下标等）
            "target": self.visit(ctx.left),
            "value": self.visit(ctx.right)
        }

    def visitIf_statement(self, ctx: IEC61131Parser.If_statementContext) -> Dict[str, Any]:
        # 提取主 IF
        main_cond = self.visit(ctx.cond[0])
        main_then = self.visit(ctx.thenlist[0])

        # 提取 ELSIF
        elif_branches = []
        for i in range(1, len(ctx.cond)):
            elif_branches.append({
                "cond": self.visit(ctx.cond[i]),
                "then_body": self.visit(ctx.thenlist[i])
            })

        # 提取 ELSE
        else_body = self.visit(ctx.elselist) if ctx.elselist else []

        return {
            "stmt_type": "if",
            "cond": main_cond,
            "then_body": main_then,
            "elif_branches": elif_branches,
            "else_body": else_body
        }

    def visitCase_statement(self, ctx: IEC61131Parser.Case_statementContext) -> Dict[str, Any]:
        entries = []
        for ectx in ctx.case_entry():
            conds = [cctx.getText() for cctx in ectx.case_condition()]
            entries.append({
                "conds": conds,
                "body": self.visit(ectx.statement_list())
            })

        return {
            "stmt_type": "case",
            "cond": self.visit(ctx.cond),
            "entries": entries,
            "else_body": self.visit(ctx.elselist) if ctx.elselist else []
        }

    def visitFor_statement(self, ctx: IEC61131Parser.For_statementContext) -> Dict[str, Any]:
        return {
            "stmt_type": "for",
            "var": ctx.var.text,
            "start": self.visit(ctx.begin),
            "end": self.visit(ctx.endPosition),
            "step": self.visit(ctx.by) if ctx.by else None,
            "body": self.visit(ctx.statement_list())
        }

    def visitWhile_statement(self, ctx: IEC61131Parser.While_statementContext) -> Dict[str, Any]:
        return {
            "stmt_type": "while",
            "cond": self.visit(ctx.expression()),
            "body": self.visit(ctx.statement_list())
        }

    def visitInvocation_statement(self, ctx: IEC61131Parser.Invocation_statementContext) -> Dict[str, Any]:
        return self.visit(ctx.invocation())


    def visitParam_assignment(self, ctx: IEC61131Parser.Param_assignmentContext):
        if ctx.v:
            return self.visit(ctx.v)
        if ctx.expression():
            return self.visit(ctx.expression())
        return None

    # ==========================================
    # 4. 表达式 (Expressions)
    # ==========================================

    def _make_binop(self, ctx) -> Dict[str, Any]:
        """通用的二元操作符构造器"""
        return {
            "expr_type": "binop",
            "op": ctx.op.text.upper(),
            "left": self.visit(ctx.left),
            "right": self.visit(ctx.right)
        }

    # ANTLR 会根据不同的运算优先级生成不同的 Context，这里统一走 _make_binop
    def visitBinaryPowerExpr(self, ctx: IEC61131Parser.BinaryPowerExprContext):
        return self._make_binop(ctx)

    def visitBinaryModDivExpr(self, ctx: IEC61131Parser.BinaryModDivExprContext):
        return self._make_binop(ctx)

    def visitBinaryMultExpr(self, ctx: IEC61131Parser.BinaryMultExprContext):
        return self._make_binop(ctx)

    def visitBinaryPlusMinusExpr(self, ctx: IEC61131Parser.BinaryPlusMinusExprContext):
        return self._make_binop(ctx)

    def visitBinaryCmpExpr(self, ctx: IEC61131Parser.BinaryCmpExprContext):
        return self._make_binop(ctx)

    def visitBinaryEqExpr(self, ctx: IEC61131Parser.BinaryEqExprContext):
        return self._make_binop(ctx)

    def visitBinaryAndExpr(self, ctx: IEC61131Parser.BinaryAndExprContext):
        return self._make_binop(ctx)

    def visitBinaryOrExpr(self, ctx: IEC61131Parser.BinaryOrExprContext):
        return self._make_binop(ctx)

    def visitBinaryXORExpr(self, ctx: IEC61131Parser.BinaryXORExprContext):
        return self._make_binop(ctx)

    def visitUnaryMinusExpr(self, ctx: IEC61131Parser.UnaryMinusExprContext):
        return {
            "expr_type": "unaryop",
            "op": "-",
            "operand": self.visit(ctx.sub)
        }

    def visitUnaryNegateExpr(self, ctx: IEC61131Parser.UnaryNegateExprContext):
        return {
            "expr_type": "unaryop",
            "op": "NOT",
            "operand": self.visit(ctx.sub)
        }

    def visitParenExpr(self, ctx: IEC61131Parser.ParenExprContext):
        # 括号表达式直接提取内部的表达式即可
        return self.visit(ctx.sub)

    def visitPrimaryExpr(self, ctx: IEC61131Parser.PrimaryExprContext):
        return self.visit(ctx.primary_expression())

    def visitConstant(self, ctx: IEC61131Parser.ConstantContext) -> Dict[str, Any]:
        return {
            "expr_type": "literal",
            "value": ctx.getText()
        }

    def visitVariable(self, ctx) -> Dict[str, Any]:
        # 提取变量引用（支持数组下标和结构体成员的纯文本形式）
        return {
            "expr_type": "var",
            "name": ctx.getText()
        }


    def visitRepeat_statement(self, ctx: IEC61131Parser.Repeat_statementContext) -> Dict[str, Any]:
        return {
            "stmt_type": "repeat",
            "body": self.visit(ctx.statement_list()) if ctx.statement_list() else [],
            "until_cond": self.visit(ctx.expression())
        }

    def visitReturn_statement(self, ctx: IEC61131Parser.Return_statementContext) -> Dict[str, Any]:
        return {"stmt_type": "return"}

    def visitExit_statement(self, ctx: IEC61131Parser.Exit_statementContext) -> Dict[str, Any]:
        return {"stmt_type": "exit"}

    def visitContinue_statement(self, ctx: IEC61131Parser.Continue_statementContext) -> Dict[str, Any]:
        return {"stmt_type": "continue"}
