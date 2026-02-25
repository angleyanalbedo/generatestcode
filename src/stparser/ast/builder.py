from __future__ import annotations

from typing import List, Optional

from antlr4 import ParserRuleContext

from ..anltr4.generated.IEC61131ParserVisitor import IEC61131ParserVisitor
from ..anltr4.generated.IEC61131Parser import IEC61131Parser

from .nodes import (
    SourceLocation,
    ProgramDecl,
    FBDecl,
    VarDecl,
    Stmt,
    Expr,
    Assignment,
    IfStmt,
    ForStmt,
    CallStmt,
    VarRef,
    Literal,
    BinOp,
    CallExpr,   #新增
    CaseStmt,
    CaseEntry,
    CaseCond,
    WhileStmt,
    RepeatStmt,
    # 如果你在 nodes.py 里有 UnaryOp，可以自己改成用 UnaryOp
    # UnaryOp,
)


class ASTBuilder(IEC61131ParserVisitor):
    """
    基于 IEC61131Parser.g4 的简化 AST 构造器。

    当前支持：
      - PROGRAM / FUNCTION_BLOCK 定义
      - VAR 变量声明（含 VAR_INPUT / VAR_OUTPUT / VAR_IN_OUT / VAR_GLOBAL 等）
      - 语句：赋值、调用(invocation)、IF、FOR
      - 表达式：一元/二元运算（+ - * / MOD DIV 比较 布尔运算 等）

    暂时忽略：
      - SFC / IL / 类 / 接口 / 方法 / CASE / WHILE / REPEAT 等复杂结构
      - 复杂类型初始化（initializations）
    """

    def __init__(self, filename: str = "<memory>"):
        self.filename = filename

    # ========= 工具函数 =========

    def _loc(self, ctx: ParserRuleContext) -> SourceLocation:
        token = ctx.start
        return SourceLocation(
            file=self.filename,
            line=token.line,
            column=getattr(token, "column", 0),
        )

    # ========= 顶层入口 =========

    def visitStart(self, ctx: IEC61131Parser.StartContext) -> List[ProgramDecl | FBDecl]:
        """
        start
          : (library_element_declaration)* ;
        """
        pous: List[ProgramDecl | FBDecl] = []
        for elem in ctx.library_element_declaration():
            ast = self.visit(elem)
            if ast is None:
                continue
            if isinstance(ast, (ProgramDecl, FBDecl)):
                pous.append(ast)
            elif isinstance(ast, list):
                for a in ast:
                    if isinstance(a, (ProgramDecl, FBDecl)):
                        pous.append(a)
        return pous

    def visitLibrary_element_declaration(
        self, ctx: IEC61131Parser.Library_element_declarationContext
    ):
        """
        library_element_declaration
          : data_type_declaration
          | function_declaration
          | class_declaration
          | interface_declaration
          | function_block_declaration
          | program_declaration
          | configuration_declaration
          ;
        """
        if ctx.program_declaration():
            return self.visit(ctx.program_declaration())
        if ctx.function_block_declaration():
            return self.visit(ctx.function_block_declaration())
        # 其它暂不处理
        return None

    # ========= POU：PROGRAM / FUNCTION_BLOCK =========

    def visitProgram_declaration(
        self, ctx: IEC61131Parser.Program_declarationContext
    ) -> ProgramDecl:
        """
        program_declaration
          : PROGRAM identifier=IDENTIFIER
            var_decls
            action*
            body
            END_PROGRAM
          ;
        """
        name = ctx.identifier.text

        vars_: List[VarDecl] = []
        if ctx.var_decls():
            vars_ = self.visit(ctx.var_decls())

        body_stmts: List[Stmt] = []
        if ctx.body():
            body_stmts = self._extract_body_statements(ctx.body())

        return ProgramDecl(
            name=name,
            vars=vars_,
            body=body_stmts,
            loc=self._loc(ctx),
        )

    def visitFunction_block_declaration(
        self, ctx: IEC61131Parser.Function_block_declarationContext
    ) -> FBDecl:
        """
        function_block_declaration
          : FUNCTION_BLOCK (FINAL | ABSTRACT)?
            identifier = IDENTIFIER
            (EXTENDS inherit=IDENTIFIER)?
            (IMPLEMENTS interfaces=identifier_list)?
            var_decls
            methods
            action*
            body
            END_FUNCTION_BLOCK
          ;
        """
        name = ctx.identifier.text

        vars_: List[VarDecl] = []
        if ctx.var_decls():
            vars_ = self.visit(ctx.var_decls())

        body_stmts: List[Stmt] = []
        if ctx.body():
            body_stmts = self._extract_body_statements(ctx.body())

        return FBDecl(
            name=name,
            vars=vars_,
            body=body_stmts,
            loc=self._loc(ctx),
        )

    def _extract_body_statements(
        self, body_ctx: IEC61131Parser.BodyContext
    ) -> List[Stmt]:
        """
        body :
            sfc
          | IL_CODE ilBody
          | statement_list
          ;
        这里只处理 statement_list，SFC/IL 暂时忽略。
        """
        if body_ctx.statement_list():
            return self.visit(body_ctx.statement_list())
        return []

    # ========= 变量声明 =========

    def visitVar_decls(self, ctx: IEC61131Parser.Var_declsContext) -> List[VarDecl]:
        """
        var_decls
          : (var_decl)* ;
        """
        vars_: List[VarDecl] = []
        for vd in ctx.var_decl():
            decls = self.visit(vd)
            if decls:
                vars_.extend(decls)
        return vars_

    def visitVar_decl(self, ctx: IEC61131Parser.Var_declContext) -> List[VarDecl]:
        """
        var_decl
          : variable_keyword
            var_decl_inner
            END_VAR
          ;
        """
        storage = "VAR"
        vk = ctx.variable_keyword()
        if vk is not None and vk.getChildCount() > 0:
            # variable_keyword 的第一个子节点一般是 VAR / VAR_INPUT / VAR_OUTPUT 等
            storage = vk.getChild(0).getText()

        inner = ctx.var_decl_inner()
        decls: List[VarDecl] = []

        if inner is None:
            return []

        # var_decl_inner :
        #   (identifier_list COLON td=type_declaration SEMICOLON)* ;
        type_list = inner.type_declaration()
        id_list_list = inner.identifier_list()

        for id_list_ctx, type_ctx in zip(id_list_list, type_list):
            type_str = type_ctx.getText()
            # identifier_list : names+=variable_names (COMMA names+=variable_names)* ;
            for name_ctx in id_list_ctx.variable_names():
                name = name_ctx.getText()
                decls.append(
                    VarDecl(
                        name=name,
                        type=type_str,
                        storage=storage,
                        init_expr=None,  # 初始化先不处理
                        loc=self._loc(ctx),
                    )
                )
        return decls

    # ========= 语句列表 & 语句 =========

    def visitStatement_list(
        self, ctx: IEC61131Parser.Statement_listContext
    ) -> List[Stmt]:
        """
        statement_list
          : (statement)* ;
        """
        stmts: List[Stmt] = []
        for sctx in ctx.statement():
            stmt = self.visit(sctx)
            if isinstance(stmt, Stmt):
                stmts.append(stmt)
        return stmts

    def visitStatement(self, ctx: IEC61131Parser.StatementContext) -> Optional[Stmt]:
        """
        statement :
              assignment_statement SEMICOLON
            | mult_assignment_statement SEMICOLON
            | invocation_statement SEMICOLON
            | return_statement SEMICOLON
            | jump_statement SEMICOLON
            | label_statement SEMICOLON
            | if_statement SEMICOLON?
            | case_statement SEMICOLON?
            | for_statement SEMICOLON?
            | while_statement SEMICOLON?
            | repeat_statement SEMICOLON?
            | exit_statement SEMICOLON
            | continue_statement SEMICOLON
            | empty_statement
          ;
        """
        if ctx.assignment_statement():
            return self.visit(ctx.assignment_statement())
        if ctx.invocation_statement():
            return self.visit(ctx.invocation_statement())
        if ctx.if_statement():
            return self.visit(ctx.if_statement())
        if ctx.case_statement():
            return self.visit(ctx.case_statement())
        if ctx.for_statement():
            return self.visit(ctx.for_statement())
        if ctx.while_statement():
            return self.visit(ctx.while_statement())
        if ctx.repeat_statement():
            return self.visit(ctx.repeat_statement())
        return None

    # --- 赋值语句 ---

    def visitAssignment_statement(
        self, ctx: IEC61131Parser.Assignment_statementContext
    ) -> Assignment:
        """
        assignment_statement
          : left=variable op=(ASSIGN_ATTEMPT|RASSIGN|ASSIGN|INCREAE|DECREASE) right=expression
          ;
        这里统一当成普通赋值（忽略 op 的差别）。
        """
        target_expr = self.visit(ctx.left)
        value_expr = self.visit(ctx.right)
        return Assignment(
            target=target_expr,
            value=value_expr,
            loc=self._loc(ctx),
        )

    # --- 调用语句（FB/函数调用） ---

    def visitInvocation_statement(
        self, ctx: IEC61131Parser.Invocation_statementContext
    ) -> CallStmt:
        """
        invocation_statement
          : invocation
          ;
        """
        return self.visit(ctx.invocation())

    def visitInvocation(self, ctx: IEC61131Parser.InvocationContext) -> CallStmt:
        """
        invocation
        : id=symbolic_variable LPAREN
            ( (expression | param_assignment)
                (COMMA (expression | param_assignment))* )?
            RPAREN
        ;
        """
        # 有的生成器会把 label id 变成 id_
        if hasattr(ctx, "id_") and ctx.id_ is not None:
            fb_name = ctx.id_.getText()
        else:
            # 兜底：直接用第一个 symbolic_variable 作为名字
            fb_name = ctx.symbolic_variable().getText()

        args: List[Expr] = []

        for pa in ctx.param_assignment():
            expr = self.visit(pa)
            if isinstance(expr, Expr):
                args.append(expr)

        for e in ctx.expression():
            expr = self.visit(e)
            if isinstance(expr, Expr):
                args.append(expr)

        return CallStmt(
            fb_name=fb_name,
            args=args,
            loc=self._loc(ctx),
        )


    def visitParam_assignment(
        self, ctx: IEC61131Parser.Param_assignmentContext
    ) -> Expr:
        """
        param_assignment
          : id=IDENTIFIER ARROW_RIGHT v=variable
          | (id=IDENTIFIER ASSIGN)? expression
          ;
        AST 里我们只关心“被传入的值/变量”，忽略参数名。
        """
        if ctx.v:
            return self.visit(ctx.v)
        if ctx.expression():
            return self.visit(ctx.expression())
        raise RuntimeError("Unexpected param_assignment without value")

    # --- IF 语句 ---
    def visitIf_statement(self, ctx: IEC61131Parser.If_statementContext) -> IfStmt:
        """
        if_statement
        : IF cond+=expression THEN thenlist+=statement_list
            (ELSEIF cond+=expression THEN thenlist+=statement_list)*
            (ELSE elselist = statement_list)?
            END_IF SEMICOLON?
        ;
        """

        # 至少有一个 IF ... THEN
        if not ctx.cond or not ctx.thenlist:
            raise RuntimeError("if_statement without condition/then body")

        # -------- 主 IF 分支 --------
        # cond[0] / thenlist[0] 对应最前面的 IF
        main_cond = self.visit(ctx.cond[0])
        main_then = self.visit(ctx.thenlist[0])  # statement_list -> List[Stmt]

        # -------- ELSIF 分支 --------
        elif_branches = []
        cond_list = ctx.cond
        then_list = ctx.thenlist
        # 从索引 1 开始是各个 ELSIF
        for i in range(1, len(cond_list)):
            c = self.visit(cond_list[i])
            t = self.visit(then_list[i])
            elif_branches.append((c, t))

        # -------- ELSE 分支（可选）--------
        else_body = []
        # 这里注意：elselist 是一个属性（Statement_listContext），不是方法
        if ctx.elselist is not None:
            else_body = self.visit(ctx.elselist)  # -> List[Stmt]

        return IfStmt(
            cond=main_cond,
            then_body=main_then,
            elif_branches=elif_branches,  # 如果 IfStmt 没这个字段，要在 nodes.py 里加上
            else_body=else_body,
            loc=self._loc(ctx),
        )

    def visitCase_statement(self, ctx: IEC61131Parser.Case_statementContext) -> CaseStmt:
        """
        case_statement
        : CASE cond=expression OF
            (case_entry)+
            (ELSE COLON? elselist=statement_list)?
            END_CASE
        ;
        """

        # selector expression
        selector = self.visit(ctx.cond)

        entries: List[CaseEntry] = []
        for ectx in ctx.case_entry():
            # case_entry
            #   : case_condition (COMMA case_condition)*
            #     COLON statement_list
            #   ;
            conds: List[CaseCond] = []
            for cctx in ectx.case_condition():
                conds.append(CaseCond(text=cctx.getText(), loc=self._loc(cctx)))

            body = self.visit(ectx.statement_list())  # -> List[Stmt]

            entries.append(
                CaseEntry(
                    conds=conds,
                    body=body,
                    loc=self._loc(ectx),
                )
            )

        else_body: List[Stmt] = []
        # 注意：elselist 在 g4 里是命名字段：elselist=statement_list
        if ctx.elselist is not None:
            else_body = self.visit(ctx.elselist)

        return CaseStmt(
            cond=selector,
            entries=entries,
            else_body=else_body,
            loc=self._loc(ctx),
        )

    # --- FOR 语句 ---

    def visitFor_statement(self, ctx: IEC61131Parser.For_statementContext) -> ForStmt:
        """
        for_statement
          : FOR var=IDENTIFIER ASSIGN
              begin=expression TO endPosition=expression
              (BY by = expression)?
              DO statement_list END_FOR
          ;
        """
        var_name = ctx.var.text
        start_expr = self.visit(ctx.begin)
        end_expr = self.visit(ctx.endPosition)
        step_expr: Optional[Expr] = self.visit(ctx.by) if ctx.by else None
        body_stmts = self.visit(ctx.statement_list())

        return ForStmt(
            var=var_name,
            start=start_expr,
            end=end_expr,
            step=step_expr,
            body=body_stmts,
            loc=self._loc(ctx),
        )
    
    def visitWhile_statement(self, ctx: IEC61131Parser.While_statementContext) -> WhileStmt:
        """
        while_statement
        : WHILE expression DO statement_list END_WHILE
        ;
        """
        cond = self.visit(ctx.expression())
        body = self.visit(ctx.statement_list())
        return WhileStmt(cond=cond, body=body, loc=self._loc(ctx))


    def visitRepeat_statement(self, ctx: IEC61131Parser.Repeat_statementContext) -> RepeatStmt:
        """
        repeat_statement
        : REPEAT statement_list UNTIL expression END_REPEAT
        ;
        """
        body = self.visit(ctx.statement_list())
        until = self.visit(ctx.expression())
        return RepeatStmt(body=body, until=until, loc=self._loc(ctx))

    # ========= 表达式 =========
    # 表达式在 grammar 里有一堆带 #label 的备选，ANTLR 会生成对应的 *Context，
    # 我们给它们写对应的 visitXXX 方法。

    # unaryMinusExpr : MINUS sub=expression
    def visitUnaryMinusExpr(
        self, ctx: IEC61131Parser.UnaryMinusExprContext
    ) -> Expr:
        sub = self.visit(ctx.sub)
        # 如果你以后有 UnaryOp，可以改成 UnaryOp("-", sub)
        return BinOp(
            op="UMINUS",
            left=Literal(value="0", type="NUM", loc=self._loc(ctx)),
            right=sub,
            loc=self._loc(ctx),
        )

    # unaryNegateExpr : NOT sub=expression
    def visitUnaryNegateExpr(
        self, ctx: IEC61131Parser.UnaryNegateExprContext
    ) -> Expr:
        sub = self.visit(ctx.sub)
        return BinOp(
            op="NOT",
            left=sub,
            right=Literal(value="1", type="BOOL", loc=self._loc(ctx)),
            loc=self._loc(ctx),
        )

    # parenExpr : LPAREN sub=expression RPAREN
    def visitParenExpr(self, ctx: IEC61131Parser.ParenExprContext) -> Expr:
        return self.visit(ctx.sub)

    # binaryPowerExpr : left=expression op=POWER right=expression
    def visitBinaryPowerExpr(
        self, ctx: IEC61131Parser.BinaryPowerExprContext
    ) -> Expr:
        return self._make_binop(ctx)

    # binaryModDivExpr : <assoc=right> left=expression op=(MOD|DIV) right=expression
    def visitBinaryModDivExpr(
        self, ctx: IEC61131Parser.BinaryModDivExprContext
    ) -> Expr:
        return self._make_binop(ctx)

    # binaryMultExpr : left=expression op=MULT right=expression
    def visitBinaryMultExpr(
        self, ctx: IEC61131Parser.BinaryMultExprContext
    ) -> Expr:
        return self._make_binop(ctx)

    # binaryPlusMinusExpr : left=expression op=(PLUS|MINUS) right=expression
    def visitBinaryPlusMinusExpr(
        self, ctx: IEC61131Parser.BinaryPlusMinusExprContext
    ) -> Expr:
        return self._make_binop(ctx)

    # binaryCmpExpr : left=expression op=(<,>,<=,>=) right=expression
    def visitBinaryCmpExpr(
        self, ctx: IEC61131Parser.BinaryCmpExprContext
    ) -> Expr:
        return self._make_binop(ctx)

    # binaryEqExpr : left=expression op=(=,<>) right=expression
    def visitBinaryEqExpr(
        self, ctx: IEC61131Parser.BinaryEqExprContext
    ) -> Expr:
        return self._make_binop(ctx)

    # binaryAndExpr : left=expression op=(AND|AMPERSAND) right=expression
    def visitBinaryAndExpr(
        self, ctx: IEC61131Parser.BinaryAndExprContext
    ) -> Expr:
        return self._make_binop(ctx)

    # binaryOrExpr : left=expression op=OR right=expression
    def visitBinaryOrExpr(
        self, ctx: IEC61131Parser.BinaryOrExprContext
    ) -> Expr:
        return self._make_binop(ctx)

    # binaryXORExpr : left=expression op=XOR right=expression
    def visitBinaryXORExpr(
        self, ctx: IEC61131Parser.BinaryXORExprContext
    ) -> Expr:
        return self._make_binop(ctx)

    # primaryExpr : primary_expression
    def visitPrimaryExpr(
        self, ctx: IEC61131Parser.PrimaryExprContext
    ) -> Expr:
        return self.visit(ctx.primary_expression())

    def _make_binop(self, ctx) -> BinOp:
        """
        通用二元运算构造，ctx 需要有 left / right / op 三个属性。
        """
        left = self.visit(ctx.left)
        right = self.visit(ctx.right)
        op_text = ctx.op.text
        return BinOp(
            op=op_text,
            left=left,
            right=right,
            loc=self._loc(ctx),
        )

    # ========= primary_expression / constant / variable =========

    def visitPrimary_expression(
        self, ctx: IEC61131Parser.Primary_expressionContext
    ) -> Expr:
        """
        primary_expression
        : constant
        | v=variable
        | invocation
        ;
        """
        if ctx.constant():
            return self.visit(ctx.constant())
        if ctx.v:
            return self.visit(ctx.v)
        if ctx.invocation():
            inv = ctx.invocation()

            # 取函数/FB 名字
            if hasattr(inv, "id_") and inv.id_ is not None:
                func_name = inv.id_.getText()
            else:
                func_name = inv.symbolic_variable().getText()

            # 收集参数表达式（和 visitInvocation 里的逻辑类似，但这里返回 Expr）
            args: List[Expr] = []

            for pa in inv.param_assignment():
                expr = self.visit(pa)
                if isinstance(expr, Expr):
                    args.append(expr)

            for e in inv.expression():
                expr = self.visit(e)
                if isinstance(expr, Expr):
                    args.append(expr)

            return CallExpr(
                func=func_name,
                args=args,
                loc=self._loc(inv),
            )

        raise RuntimeError("Unexpected primary_expression")

    def visitConstant(self, ctx: IEC61131Parser.ConstantContext) -> Literal:
        """
        constant
          : integer
          | real
          | string
          | time
          | timeofday
          | date
          | datetime
          | cast
          | bits
          | ref_null
          | reference_value
          ;
        这里只是把字面量文本原样存下来。
        """
        return Literal(
            value=ctx.getText(),
            type="CONST",
            loc=self._loc(ctx),
        )
    
    def visitPrimary(self, ctx):
        """
        兼容 visitVariable 里调用的 visitPrimary。
        实际直接转发到已有的 visitPrimaryExpr。
        """
        return self.visitPrimaryExpr(ctx)

    def visitVariable(self, ctx) -> Expr:
        # 假设 grammar roughly: variable: primary ( '[' expr ']' )* ( '.' IDENT )*;
        # base = self.visitPrimary(ctx.primary())

        # # 处理数组下标链
        # for idx_ctx in ctx.indexExprList():  # 根据你的 grammar 实际名字调整
        #     index_expr = self.visitExpr(idx_ctx)
        #     base = ArrayAccess(base=base, index=index_expr, loc=self._loc(idx_ctx))

        # # 处理结构体字段链
        # for field_tok in ctx.DOT_ID_LIST():  # 例如 ".Pos", ".Status"
        #     field_name = field_tok.getText()[1:]  # 去掉 '.'
        #     base = FieldAccess(base=base, field=field_name, loc=self._loc(field_tok))

        # return base
        name = ctx.getText()
        return VarRef(name=name, loc=self._loc(ctx))


