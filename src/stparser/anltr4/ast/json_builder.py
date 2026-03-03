from typing import List,Dict,Any

from src.stparser.anltr4.generated.IEC61131Parser import IEC61131Parser
from src.stparser.anltr4.generated.IEC61131ParserVisitor import IEC61131ParserVisitor

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
        """
        终极防弹文本提取：自动处理属性、方法、Token、Context
        """
        if obj is None: return ""

        # 如果 obj 本身已经是字符串了（例如之前处理过的）
        if isinstance(obj, str): return obj

        try:
            # 1. 如果是方法，尝试调用它获取节点
            if callable(obj):
                # 针对 ANTLR：如果它是 Token 节点，调用会失败，我们捕获它
                temp = obj()
                if temp is not None:
                    obj = temp

            # 2. 如果是 Context (有 getText 方法)
            if hasattr(obj, 'getText'):
                return obj.getText()

            # 3. 如果是 Token (有 text 属性)
            if hasattr(obj, 'text'):
                return obj.text

            # 4. 递归处理列表 (例如 identifier_list)
            if isinstance(obj, list):
                return "".join([self.safe_text(i) for i in obj])

        except Exception as e:
            # 这里的诊断能帮你定位是哪个 Token 出了问题
            print(f"[AST诊断] safe_text 在处理 {type(obj)} 时报错: {e}")

        return str(obj)



    # ==========================================
    # 开始
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

    # ==========================================
    # 1. 顶层结构 (Program, Function Block)
    # ==========================================
    def visitProgram_declaration(self, ctx: IEC61131Parser.Program_declarationContext) -> Dict[str, Any]:
        # 💡 正确做法：直接调用 ANTLR 生成的方法获取 Context 对象
        body_ctx = ctx.body() if hasattr(ctx, 'body') else None

        return {
            "unit_type": "PROGRAM",
            "name": self.safe_text(ctx.identifier),
            "var_blocks": self.visit(ctx.var_decls()) if ctx.var_decls() else [],
            # 💡 只有通过 visit(body_ctx)，才能触发下面的 visitBody 逻辑
            "body": self.visit(body_ctx) if body_ctx else []
        }


    def visitFunction_block_declaration(self, ctx: IEC61131Parser.Function_block_declarationContext) -> Dict[
        str, Any]:
        body_ctx = ctx.body() if hasattr(ctx, 'body') else None
        return {
            "unit_type": "FUNCTION_BLOCK",
            "name": self.safe_text(ctx.identifier),
            "var_blocks": self.visit(ctx.var_decls()) if ctx.var_decls() else [],
            "body": self.visit(body_ctx) if body_ctx else []
        }

    def visitFunction_declaration(self, ctx: IEC61131Parser.Function_declarationContext) -> Dict[str, Any]:
        # 💡 注意：Function 通常使用 funcBody()
        body_ctx = ctx.funcBody() if hasattr(ctx, 'funcBody') else None
        return {
            "unit_type": "FUNCTION",
            "name": self.safe_text(ctx.identifier),
            "return_type": self.safe_text(ctx.elementary_type_name) or "UNKNOWN",
            "var_blocks": self.visit(ctx.var_decls()) if ctx.var_decls() else [],
            "body": self.visit(body_ctx) if body_ctx else []
        }


    def visitBody(self, ctx: IEC61131Parser.BodyContext):
        """处理 PROGRAM 和 FB 的身体部分"""
        # 💡 核心修复：必须加括号 () 调用方法，才能拿到 Context 节点
        stmt_list_ctx = ctx.statement_list()

        if stmt_list_ctx:
            # 只有拿到节点，visit 才会根据类型分发到 visitStatement_list
            return self.visit(stmt_list_ctx)

        return []

    def visitFuncBody(self, ctx: IEC61131Parser.FuncBodyContext):
        """处理 FUNCTION 的身体部分"""
        # 💡 同理，Function 的 funcBody 也要显式调用其内部的 statement_list()
        stmt_list_ctx = ctx.statement_list()

        if stmt_list_ctx:
            return self.visit(stmt_list_ctx)

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
        """
                不要管类型提示，严格按照这个签名写。
                """
        # 打印这一行，如果没印出来，说明重写确实没生效
        # print("DEBUG: Successfully entered visitStatement_list")

        stmts = []
        # 获取语句列表 (注意：ctx.statement() 返回的是列表)
        children = ctx.children
        if children:
            for child in children:
                res = self.visit(child)
                if res:
                    stmts.append(res)

        # 🚩 必须 return，这个值会直接返回给上面的 visitBody
        return stmts

    def visitStatement(self, ctx: IEC61131Parser.StatementContext):
        return super().visitStatement(ctx)
    def visitAssignment_statement(self, ctx: IEC61131Parser.Assignment_statementContext) -> Dict[str, Any]:
        return {
            "stmt_type": "assign",
            # target 作为表达式递归处理（兼容数组下标等）
            "left": self.visit(ctx.left) if ctx.left else None,
            "right": self.visit(ctx.right) if ctx.right else None,
            "op": ctx.op.text.upper(),

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

    def visitInvocation(self, ctx: IEC61131Parser.InvocationContext) -> Dict[str, Any]:
        # 💡 统一使用 safe_text 配合 getattr，不加括号调用
        func_name = self.safe_text(getattr(ctx, "id_", None)) or \
                    self.safe_text(getattr(ctx, "symbolic_variable", None))

        args = []
        # 提取参数赋值 (如 IN1 := X)
        if hasattr(ctx, 'param_assignment'):
            for pa in ctx.param_assignment():
                args.append(self.visit(pa))

        # 提取直接表达式参数 (如 ABS(X))
        if hasattr(ctx, 'expression'):
            for e in ctx.expression():
                args.append(self.visit(e))

        return {
            "stmt_type": "call",  # 默认作为语句
            "expr_type": "call",  # 同时提供给表达式识别
            "func_name": func_name,
            "args": [a for a in args if a is not None]
        }

    def visitPrimary_expression(self, ctx: IEC61131Parser.Primary_expressionContext) -> Dict[str, Any]:
        # 1. 处理常量
        if ctx.constant():
            return self.visit(ctx.constant())

        # 2. 处理变量 (你之前的 ctx.v 对应 G4 里的变量节点)
        if hasattr(ctx, 'v') and ctx.v:
            return self.visit(ctx.v)

        # 3. 处理函数调用 (🌟 核心：直接 visit，不要手动提取)
        if ctx.invocation():
            res = self.visit(ctx.invocation())
            # 💡 对齐补丁：如果是作为表达式使用，将 stmt_type 转换为 expr_type
            if res and isinstance(res, dict):
                res["expr_type"] = "call"
            return res

        # 4. 处理括号嵌套 ( (A+B) )
        if hasattr(ctx, 'expression') and ctx.expression():
            return self.visit(ctx.expression())

        return {"expr_type": "unknown", "text": self.safe_text(ctx)}

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
            "value": ctx.start
        }

    def visitVariable(self, ctx:IEC61131Parser.VariableContext) -> Dict[str, Any]:
        # 提取变量引用（支持数组下标和结构体成员的纯文本形式）
        return {
            "expr_type": "var",
            "name": ctx.start
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
