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

    def get_read_vars(self, node: Any) -> set:
        """
        递归获取一个 AST 节点中所有‘读’（被引用）的变量名。
        用于构建数据依赖图（DDG）。
        """
        if not node:
            return set()

        # 处理列表（通常是语句列表 body）
        if isinstance(node, list):
            res = set()
            for x in node:
                res |= self.get_read_vars(x)
            return res

        # 如果是基础类型（比如直接解析出的字符串或数字），不涉及变量读取
        if not isinstance(node, dict):
            return set()

        ntype = node.get("type")
        res = set()

        # 1. 基础表达式
        if ntype == "variable":
            res.add(node["name"])

        elif ntype == "binary_op":
            res |= self.get_read_vars(node["left"])
            res |= self.get_read_vars(node["right"])

        elif ntype == "unary_op":
            res |= self.get_read_vars(node["operand"])

        # 2. 赋值语句 (LHS 是写，RHS 是读)
        elif ntype == "assignment":
            res |= self.get_read_vars(node["expr"])
            # 注意：如果存在数组下标访问如 A[i] := 10，则 i 也是被‘读’的
            if isinstance(node.get("target_metadata"), dict):  # 预留给未来数组/结构体处理
                res |= self.get_read_vars(node["target_metadata"])

        # 3. 控制流结构 (Condition 部分是读)
        elif ntype == "if_statement":
            res |= self.get_read_vars(node["condition"])
            res |= self.get_read_vars(node["then_branch"])
            if node.get("else_branch"):
                res |= self.get_read_vars(node["else_branch"])
            # 如果你处理了 ELSIF，也需要在这里递归

        elif ntype == "case_statement":
            res |= self.get_read_vars(node["expression"])  # CASE x OF 中的 x
            for selection in node.get("selections", []):
                res |= self.get_read_vars(selection["body"])
            if node.get("else_branch"):
                res |= self.get_read_vars(node["else_branch"])

        elif ntype == "for_loop":
            # 循环的边界值和步长都是读
            res |= self.get_read_vars(node["from"])
            res |= self.get_read_vars(node["to"])
            res |= self.get_read_vars(node["step"])
            res |= self.get_read_vars(node["body"])

        elif ntype == "while_loop":
            res |= self.get_read_vars(node["condition"])
            res |= self.get_read_vars(node["body"])

        # 4. 函数调用 (所有参数都是读)
        elif ntype == "func_call":
            for arg in node.get("arg_list", []):
                res |= self.get_read_vars(arg)

        return res

    def get_write_vars(self, node: Any) -> set:
        """获取一个节点中所有‘写’的变量"""
        if isinstance(node, dict) and node.get("type") == "assignment":
            return {node["target"]}
        return set()


class STUnparser:
    """将结构化字典还原为 IEC 61131-3 文本"""

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

        return ""

    def _expr(self, expr) -> str:
        """递归处理表达式"""
        if isinstance(expr, str): return expr
        if not isinstance(expr, dict): return str(expr)

        etype = expr.get("type")
        if etype == "variable": return expr["name"]
        if etype == "literal": return str(expr["value"])
        if etype == "binary_op":
            return f"({self._expr(expr['left'])} {expr['op']} {self._expr(expr['right'])})"
        if etype == "unary_op":
            return f"{expr['op']}({self._expr(expr['operand'])})"
        return ""

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

    # 在 STSemanticAnalyzer 类中添加这些方法

    @v_args(inline=True)
    def num(self, token):
        return {"type": "literal", "value": str(token)}

    @v_args(inline=True)
    def var(self, token):
        return {"type": "variable", "name": str(token)}

    def not_op(self, items):
        return {"type": "unary_op", "op": "NOT", "operand": items[0]}

    def add(self, items): return self._bin_op("+", items)

    def sub(self, items): return self._bin_op("-", items)

    def mul(self, items): return self._bin_op("*", items)

    def div(self, items): return self._bin_op("/", items)

    def gt(self, items):  return self._bin_op(">", items)

    def lt(self, items):  return self._bin_op("<", items)

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