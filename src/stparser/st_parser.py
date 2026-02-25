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
        if not node:
            return set()

        # 1. 如果是列表(代码块)，递归遍历所有子语句
        if isinstance(node, list):
            res = set()
            for x in node:
                res |= self.get_write_vars(x)
            return res

        if not isinstance(node, dict):
            return set()

        ntype = node.get("type")
        res = set()

        # 2. 捕捉核心的写入动作：赋值
        if ntype == "assignment":
            target = node.get("target")
            # 兼容 target 是字典或字符串
            if isinstance(target, dict) and target.get("type") == "variable":
                res.add(target.get("name"))
            elif isinstance(target, str):
                res.add(target)

        # 3. 深入控制流内部挖掘嵌套的写入
        elif ntype == "if_statement":
            res |= self.get_write_vars(node.get("then_branch"))
            res |= self.get_write_vars(node.get("else_branch"))

        elif ntype == "case_statement":
            for selection in node.get("selections", []):
                res |= self.get_write_vars(selection.get("body"))
            res |= self.get_write_vars(node.get("else_branch"))

        elif ntype == "for_loop":
            res |= self.get_write_vars(node.get("body"))

        elif ntype == "while_loop":
            res |= self.get_write_vars(node.get("body"))

        # 注意：如果 ST 代码中存在通过参数传递修改外部变量的情况 (比如 VAR_IN_OUT)，
        # 这里还需要解析 func_call 来捕捉写入。目前标准赋值已经足够应付基础打乱。

        return res

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

    # ---------------------------------------------------------
    # --- 新增：数据依赖分析 (Data Dependency Analysis) ---
    # ---------------------------------------------------------

    def get_read_vars(self, stmt):
        """
        递归遍历 AST 节点，提取所有被“读取”的变量。
        """
        reads = set()

        def walk(node):
            if isinstance(node, dict):
                # 如果遇到变量节点，记录它
                if node.get("type") == "variable":
                    reads.add(node.get("name"))

                # 继续往下遍历所有子节点
                for key, value in node.items():
                    # ⚠️ 关键过滤：如果是赋值语句，等号左边的变量是被“写入”的，不能算作读取
                    # (注意：如果是 A[i] := 1，这里的 i 是读取，但目前你的 AST 尚未支持数组索引，后续可扩展)
                    if node.get("type") == "assignment" and key == "target":
                        continue
                    walk(value)
            elif isinstance(node, list):
                for item in node:
                    walk(item)

        walk(stmt)
        return reads

    def get_write_vars(self, stmt):
        """
        提取语句中被“写入/修改”的变量。
        在目前的 ST 子集中，主要就是赋值语句 (assignment) 的 target。
        """
        writes = set()

        if not isinstance(stmt, dict):
            return set()

        # 如果是赋值语句，提取等号左边的变量名
        if stmt.get("type") == "assignment":
            target = stmt.get("target")
            if isinstance(target, dict) and target.get("type") == "variable":
                writes.add(target.get("name"))
            elif isinstance(target, str):  # 兼容 target 直接是字符串的情况
                writes.add(target)

        # 注意：如果未来支持了功能块调用 (比如 Timer(IN:=TRUE))，
        # Timer 本身的状态也被写入了，可以在这里扩展逻辑。

        return writes

# ==========================================
# 4. 代码还原器
# ==========================================
class STUnparser:
    def unparse(self, node, indent=0) -> str:
        if not node: return ""
        spacing = "    " * indent

        # 处理语句列表
        if isinstance(node, list):
            return "".join([self.unparse(item, indent) for item in node])

        # 获取节点类型
        if isinstance(node, dict):
            ntype = node.get("type")

            # --- 原有逻辑 ---
            if ntype == "if_statement":
                code = f"{spacing}IF {self._expr(node['condition'])} THEN\n"
                code += self.unparse(node['then_branch'], indent + 1)
                if node.get("else_branch"):
                    code += f"{spacing}ELSE\n"
                    code += self.unparse(node['else_branch'], indent + 1)
                code += f"{spacing}END_IF;\n"
                return code

            if ntype == "assignment":
                # 兼容 target 是字典或字符串的情况
                target_str = self._expr(node['target']) if isinstance(node['target'], dict) else str(node['target'])
                return f"{spacing}{target_str} := {self._expr(node['expr'])};\n"

            if ntype == "return":
                return f"{spacing}RETURN;\n"

            # --- 新增：函数块/程序声明 ---
            if node.get("unit_type") in ["FUNCTION_BLOCK", "PROGRAM", "FUNCTION"]:
                unit_type = node.get("unit_type")
                name = node.get("name")
                code = f"{spacing}{unit_type} {name}\n"
                # 渲染所有 VAR 块
                for var_block in node.get("var_blocks", []):
                    code += self.unparse(var_block, indent + 1)
                # 渲染主体代码
                code += self.unparse(node.get("body"), indent + 1)
                code += f"{spacing}END_{unit_type}\n"
                return code

            # --- 新增：变量块 (VAR ... END_VAR) ---
            if "kind" in node and "vars" in node:
                code = f"{spacing}{node['kind']}\n"
                for v in node["vars"]:
                    code += self.unparse(v, indent + 1)
                code += f"{spacing}END_VAR\n"
                return code

            # --- 新增：单行变量声明 (A : INT := 1;) ---
            if "name" in node and "type" in node and not ntype:
                name = node["name"]
                vtype = node["type"]
                code = f"{spacing}{name} : {vtype}"
                if node.get("init"):
                    code += f" := {self._expr(node['init'])}"
                code += ";\n"
                return code

            # --- 新增：函数/功能块调用作为独立语句 (如 Timer(IN:=TRUE);) ---
            if ntype == "func_call":
                return f"{spacing}{self._expr(node)};\n"

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
            elif expr['op'].upper() == "NOT":
                return f"NOT {self._expr(expr['operand'])}"
            return f"{expr['op']}({self._expr(expr['operand'])})"

        # --- 新增：处理函数/功能块调用的参数渲染 ---
        if etype == "func_call":
            name = expr.get("name")
            args = []
            for arg in expr.get("arg_list", []):
                if isinstance(arg, dict) and "param_name" in arg:
                    # 命名参数调用 (IN:=TRUE)
                    args.append(f"{arg['param_name']}:={self._expr(arg['expr'])}")
                else:
                    # 位置参数调用 (TRUE)
                    args.append(self._expr(arg))
            return f"{name}({', '.join(args)})"

        return ""