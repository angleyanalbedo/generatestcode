import json
import re
from lark import Lark, Transformer, v_args, exceptions
from typing import Dict, List, Any, Optional

# ==========================================
# 1. 工业级 IEC 61131-3 EBNF 语法定义 (完全体)
# ==========================================
ST_GRAMMAR = r"""
    ?start: program_unit

    ?program_unit: fb_decl | function_decl

    fb_decl: "FUNCTION_BLOCK" IDENT var_block* body "END_FUNCTION_BLOCK"
    function_decl: "FUNCTION" IDENT ":" type_def var_block* body "END_FUNCTION"

    var_block: ("VAR" | "VAR_INPUT" | "VAR_OUTPUT" | "VAR_IN_OUT" | "VAR_TEMP") var_decl+ "END_VAR"

    // --- 升级：支持复杂的变量类型定义 (ARRAY, STRUCT) ---
    ?type_def: TYPE
             | IDENT
             | "STRING" ["(" NUMBER ")"]
             | "ARRAY" "[" NUMBER ".." NUMBER "]" "OF" type_def
             | "STRUCT" var_decl+ "END_STRUCT"

    var_decl: IDENT ":" type_def [":=" expr] ";"
    // --------------------------------------------------

    body: (stmt)*

    ?stmt: assign_stmt 
         | if_stmt 
         | case_stmt 
         | for_stmt 
         | while_stmt
         | func_call
         | "RETURN" ";" -> return_stmt  // 新增：支持 RETURN 语句

    assign_stmt: IDENT ":=" expr ";"

    if_stmt: "IF" expr "THEN" body ("ELSIF" expr "THEN" body)* ["ELSE" body] "END_IF" ";"

    case_stmt: "CASE" expr "OF" (case_selection)+ ["ELSE" body] "END_CASE" ";"
    case_selection: case_list ":" body
    case_list: (NUMBER | IDENT) ("," (NUMBER | IDENT))*

    for_stmt: "FOR" IDENT ":=" expr "TO" expr ["BY" expr] "DO" body "END_FOR" ";"
    while_stmt: "WHILE" expr "DO" body "END_WHILE" ";"

    // --- 升级：支持标准的带 := 的功能块传参 ---
    func_call: IDENT "(" [param_list] ")" ";"
    
    ?param_list: formal_param_list | informal_param_list
    informal_param_list: expr ("," expr)*
    formal_param_list: formal_param ("," formal_param)*
    formal_param: IDENT ":=" expr
    // ------------------------------------------

    // --- 升级：支持 <=, >= 等运算符 ---
    ?expr: term
         | expr "+" term   -> add
         | expr "-" term   -> sub
         | expr ">" term   -> gt
         | expr "<" term   -> lt
         | expr ">=" term  -> ge
         | expr "<=" term  -> le
         | expr "=" term   -> eq
         | expr "<>" term  -> ne
         | expr "AND" term -> and_op
         | expr "OR" term  -> or_op

    ?term: factor
         | term "*" factor -> mul
         | term "/" factor -> div

    // --- 升级：支持函数调用、工业字面量 (T#1s) 和负数 ---
    ?factor: NUMBER        -> num
           | ST_LITERAL    -> literal
           | "-" factor    -> neg_op
           | IDENT         -> var
           | "(" expr ")"
           | "NOT" factor  -> not_op
           | IDENT "(" [param_list] ")" -> expr_func_call
    // ----------------------------------------------------

    IDENT: /[a-zA-Z_]\w*/
    TYPE: "BOOL" | "INT" | "UINT" | "DINT" | "REAL" | "LREAL" | "TIME" | "WORD" | "DWORD" | "STRING" | "BYTE"
    
    // 匹配工业专有字面量，如 T#10ms, 16#FFFF
    ST_LITERAL: /[a-zA-Z_0-9]+#[a-zA-Z_0-9\.\-]+/

    %import common.NUMBER
    %import common.WS
    %import common.CPP_COMMENT
    %import common.C_COMMENT
    %ignore WS
    %ignore CPP_COMMENT
    %ignore C_COMMENT
    
    // 匹配 IEC 61131-3 专有块注释 (* ... *)
    ST_COMMENT: "(*" /(.|\n)*?/ "*)"
    %ignore ST_COMMENT
"""

# ==========================================
# 2. 解析器类
# ==========================================
class STParser:
    def __init__(self):
        self.parser = Lark(ST_GRAMMAR, parser='lalr', maybe_placeholders=False)

    def parse(self, code: str):
        try:
            return self.parser.parse(code)
        except exceptions.LarkError as e:
            return None, str(e)

    def get_structure(self, code: str) -> Optional[Dict]:
        tree = self.parse(code)
        if isinstance(tree, tuple):  
            return {"status": "error", "message": tree[1]}

        analyzer = STSemanticAnalyzer()
        return analyzer.transform(tree)

    def get_read_vars(self, node: Any) -> set:
        if not node:
            return set()

        if isinstance(node, list):
            res = set()
            for x in node:
                res |= self.get_read_vars(x)
            return res

        if not isinstance(node, dict):
            return set()

        ntype = node.get("type")
        res = set()

        if ntype == "variable":
            res.add(node["name"])

        elif ntype == "binary_op":
            res |= self.get_read_vars(node["left"])
            res |= self.get_read_vars(node["right"])

        elif ntype == "unary_op":
            res |= self.get_read_vars(node["operand"])

        elif ntype == "assignment":
            res |= self.get_read_vars(node["expr"])
            if isinstance(node.get("target_metadata"), dict): 
                res |= self.get_read_vars(node["target_metadata"])

        elif ntype == "if_statement":
            res |= self.get_read_vars(node["condition"])
            res |= self.get_read_vars(node["then_branch"])
            if node.get("else_branch"):
                res |= self.get_read_vars(node["else_branch"])

        elif ntype == "case_statement":
            res |= self.get_read_vars(node["expression"]) 
            for selection in node.get("selections", []):
                res |= self.get_read_vars(selection["body"])
            if node.get("else_branch"):
                res |= self.get_read_vars(node["else_branch"])

        elif ntype == "for_loop":
            res |= self.get_read_vars(node["from"])
            res |= self.get_read_vars(node["to"])
            res |= self.get_read_vars(node["step"])
            res |= self.get_read_vars(node["body"])

        elif ntype == "while_loop":
            res |= self.get_read_vars(node["condition"])
            res |= self.get_read_vars(node["body"])

        elif ntype == "func_call":
            for arg in node.get("arg_list", []):
                if isinstance(arg, dict) and "param_name" in arg:
                    # 正式参数调用 IN:=X0，只读右侧 expr
                    res |= self.get_read_vars(arg["expr"])
                else:
                    res |= self.get_read_vars(arg)

        return res

    def get_write_vars(self, node: Any) -> set:
        if isinstance(node, dict) and node.get("type") == "assignment":
            return {node["target"]}
        return set()

# ==========================================
# 3. 语义分析器 (负责将 AST 转换为 Python 字典)
# ==========================================
class STSemanticAnalyzer(Transformer):
    @v_args(inline=True)
    def IDENT(self, token): return str(token)

    @v_args(inline=True)
    def TYPE(self, token): return str(token)

    @v_args(inline=True)
    def num(self, token): return {"type": "literal", "value": str(token)}

    @v_args(inline=True)
    def var(self, token): return {"type": "variable", "name": str(token)}

    # --- 新增：工业字面量、负数与 RETURN 语句 ---
    @v_args(inline=True)
    def literal(self, token): return {"type": "literal", "value": str(token)}
    
    def neg_op(self, items): return {"type": "unary_op", "op": "-", "operand": items[0]}
    
    def return_stmt(self, items): return {"type": "return"}

    def type_def(self, items):
        # 拼接复杂的类型如 ARRAY[1..10] OF REAL
        return "".join(str(i) for i in items if i is not None)
    # --------------------------------------------

    def not_op(self, items): return {"type": "unary_op", "op": "NOT", "operand": items[0]}

    def add(self, items): return self._bin_op("+", items)
    def sub(self, items): return self._bin_op("-", items)
    def mul(self, items): return self._bin_op("*", items)
    def div(self, items): return self._bin_op("/", items)
    def gt(self, items):  return self._bin_op(">", items)
    def lt(self, items):  return self._bin_op("<", items)
    def ge(self, items):  return self._bin_op(">=", items)  # 新增 >=
    def le(self, items):  return self._bin_op("<=", items)  # 新增 <=
    def eq(self, items):  return self._bin_op("=", items)
    def ne(self, items):  return self._bin_op("<>", items)
    def and_op(self, items): return self._bin_op("AND", items)
    def or_op(self, items):  return self._bin_op("OR", items)

    def _bin_op(self, op, items):
        return {
            "type": "binary_op",
            "op": op,
            "left": items[0],
            "right": items[1]
        }

    def var_decl(self, items):
        return {
            "name": items[0],
            "type": items[1],
            "init": items[2] if len(items) > 2 else None
        }

    def var_block(self, items):
        return {
            "kind": str(items[0]),
            "vars": items[1:]
        }

    def fb_decl(self, items):
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
        return items

    def expr_func_call(self, items):
        return {
            "type": "func_call",
            "name": str(items[0]),
            "arg_list": items[1] if len(items) > 1 else []
        }

    def func_call(self, items):
        return self.expr_func_call(items)

    def informal_param_list(self, items):
        return items

    def formal_param_list(self, items):
        return items

    def formal_param(self, items):
        return {
            "param_name": str(items[0]),
            "expr": items[1]
        }

# ==========================================
# 4. 代码还原器
# ==========================================
class STUnparser:
    def unparse(self, node, indent=0) -> str:
        if not node: return ""
        spacing = "    " * indent

        if isinstance(node, list):
            return "".join([self.unparse(item, indent) for item in node])

        ntype = node.get("type")

        if ntype == "if_statement":
            code = f"{spacing}IF {self._expr(node['condition'])} THEN\n"
            code += self.unparse(node['then_branch'], indent + 1)
            if node.get("else_branch"):
                code += f"{spacing}ELSE\n"
                code += self.unparse(node['else_branch'], indent + 1)
            code += f"{spacing}END_IF;\n"
            return code

        if ntype == "assignment":
            return f"{spacing}{node['target']} := {self._expr(node['expr'])};\n"
            
        if ntype == "return":
            return f"{spacing}RETURN;\n"

        return ""

    def _expr(self, expr) -> str:
        if isinstance(expr, str): return expr
        if not isinstance(expr, dict): return str(expr)

        etype = expr.get("type")
        if etype == "variable": return expr["name"]
        if etype == "literal": return str(expr["value"])
        if etype == "binary_op":
            return f"({self._expr(expr['left'])} {expr['op']} {self._expr(expr['right'])})"
        if etype == "unary_op":
            if expr['op'] == "-":
                return f"-{self._expr(expr['operand'])}"
            return f"{expr['op']}({self._expr(expr['operand'])})"
        return ""