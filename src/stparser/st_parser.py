import json
import re
from lark import Lark, Transformer, v_args, exceptions
from typing import Dict, List, Any, Optional

# 1. 定义符合 IEC 61131-3 标准的 EBNF 语法
# 涵盖了 FB 结构、变量块、赋值、IF/CASE 逻辑
ST_GRAMMAR = r"""
    ?start: program_unit

    ?program_unit: fb_decl | function_decl

    fb_decl: "FUNCTION_BLOCK" IDENT var_block* body "END_FUNCTION_BLOCK"
    function_decl: "FUNCTION" IDENT ":" TYPE var_block* body "END_FUNCTION"

    var_block: ("VAR" | "VAR_INPUT" | "VAR_OUTPUT" | "VAR_IN_OUT" | "VAR_TEMP") var_decl+ "END_VAR"

    var_decl: IDENT ":" TYPE [":=" expr] ";"
            | IDENT ":" IDENT [":=" expr] ";"  // 支持自定义类型或 FB 实例

    body: (stmt)*

    ?stmt: assign_stmt 
         | if_stmt 
         | case_stmt 
         | for_stmt 
         | while_stmt
         | func_call

    assign_stmt: IDENT ":=" expr ";"

    if_stmt: "IF" expr "THEN" body ("ELSIF" expr "THEN" body)* ["ELSE" body] "END_IF" ";"

    case_stmt: "CASE" expr "OF" (case_selection)+ ["ELSE" body] "END_CASE" ";"
    case_selection: case_list ":" body
    case_list: (NUMBER | IDENT) ("," (NUMBER | IDENT))*

    for_stmt: "FOR" IDENT ":=" expr "TO" expr ["BY" expr] "DO" body "END_FOR" ";"
    while_stmt: "WHILE" expr "DO" body "END_WHILE" ";"

    func_call: IDENT "(" [arg_list] ")" ";"
    arg_list: expr ("," expr)*

    ?expr: term
         | expr "+" term   -> add
         | expr "-" term   -> sub
         | expr ">" term   -> gt
         | expr "<" term   -> lt
         | expr "=" term   -> eq
         | expr "<>" term  -> ne
         | expr "AND" term -> and_op
         | expr "OR" term  -> or_op

    ?term: factor
         | term "*" factor -> mul
         | term "/" factor -> div

    ?factor: NUMBER        -> num
           | IDENT         -> var
           | "(" expr ")"
           | "NOT" factor  -> not_op

    IDENT: /[a-zA-Z_]\w*/
    TYPE: "BOOL" | "INT" | "UINT" | "DINT" | "REAL" | "LREAL" | "TIME" | "WORD" | "DWORD" | "STRING"

    %import common.NUMBER
    %import common.WS
    %import common.CPP_COMMENT
    %import common.C_COMMENT
    %ignore WS
    %ignore CPP_COMMENT
    %ignore C_COMMENT
"""


class STParser:
    def __init__(self):
        # 使用 LALR 解析器，速度极快，适合大规模清洗
        self.parser = Lark(ST_GRAMMAR, parser='lalr', maybe_placeholders=False)

    def parse(self, code: str):
        """解析代码返回原始语法树"""
        try:
            return self.parser.parse(code)
        except exceptions.LarkError as e:
            return None, str(e)

    def get_structure(self, code: str) -> Optional[Dict]:
        """将 AST 转换为易于操作的 Python 字典结构"""
        tree = self.parse(code)
        if isinstance(tree, tuple):  # 报错了
            return {"status": "error", "message": tree[1]}

        analyzer = STSemanticAnalyzer()
        return analyzer.transform(tree)


class STSemanticAnalyzer(Transformer):
    """
    将 Lark Tree 转换为结构化字典，用于后续的：
    1. 变量定义检查
    2. 代码重构生成
    """

    @v_args(inline=True)
    def IDENT(self, token):
        return str(token)

    @v_args(inline=True)
    def TYPE(self, token):
        return str(token)

    def var_decl(self, items):
        # 返回单个变量定义对象
        return {
            "name": items[0],
            "type": items[1],
            "init": items[2] if len(items) > 2 else None
        }

    def var_block(self, items):
        # 区分 VAR_INPUT, VAR_OUTPUT 等
        return {
            "kind": str(items[0]),
            "vars": items[1:]
        }

    def fb_decl(self, items):
        # items: [Name, VarBlock1, VarBlock2..., Body]
        name = items[0]
        body = items[-1]
        var_blocks = items[1:-1]
        return {
            "unit_type": "FUNCTION_BLOCK",
            "name": name,
            "var_blocks": var_blocks,
            "body": body
        }

    def assign_stmt(self, items):
        return {"type": "assignment", "target": items[0], "expr": items[1]}

    def body(self, items):
        return items  # 语句列表