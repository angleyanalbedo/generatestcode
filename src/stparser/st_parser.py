import re

from lark import Lark, Transformer, v_args, exceptions
from typing import Dict, List, Any, Optional
import logging
from lark import Lark, exceptions
from .gamera import ST_GRAMMAR

logger = logging.getLogger(__name__)
# ==========================================
# 解析器类
# ==========================================
class STParser:
    def __init__(self):
        self.parser = Lark(ST_GRAMMAR, parser='lalr', propagate_positions=True, maybe_placeholders=False,
                           g_regex_flags=re.IGNORECASE)

    @staticmethod
    def preprocess(code: str) -> str:
        """预处理：清理干扰字符，统一换行符"""
        if not code: return ""
        # 很多从网上爬的代码带有不可见的 BOM 头或者奇怪的缩进
        code = code.lstrip('\ufeff')
        return code.strip().replace('\r\n', '\n')

    def parse(self, code: str):
        """核心解析逻辑，包含精细化的错误诊断"""
        clean_code = self.preprocess(code)
        try:
            return self.parser.parse(clean_code)

        except exceptions.UnexpectedToken as e:
            msg = f"Unexpected token '{e.token}' at line {e.line}, column {e.column}. Expected one of: {e.expected}"
            logger.warning(f"AST Parsing Failed: {msg}")
            return None, msg

        except exceptions.UnexpectedCharacters as e:
            msg = f"Unexpected character at line {e.line}, column {e.column}.\nContext: {e.get_context(clean_code)}"
            logger.warning(f"AST Parsing Failed: {msg}")
            return None, msg

        except exceptions.LarkError as e:
            msg = f"General Parsing Error: {str(e)}"
            logger.error(msg)
            return None, msg

    def get_ast(self, code: str):
        """
        对外提供一键获取字典型 AST 的接口，屏蔽掉底层的 Tree 和 Transformer 逻辑。
        """
        result = self.parse(code)

        # 如果返回的是 tuple，说明 parse 阶段报错了
        if isinstance(result, tuple):
            return {"status": "error", "message": result[1]}

        if not result:
            return {"status": "error", "message": "Unknown parsing failure"}

        try:
            # 实例化你的分析器，把 Tree 洗成干净的 Dict
            analyzer = STSemanticAnalyzer()
            ast_dict = analyzer.transform(result)
            return {"status": "success", "ast": ast_dict}
        except Exception as e:
            logger.error(f"Semantic Transformation Error: {str(e)}")
            return {"status": "error", "message": f"Transformer Error: {str(e)}"}

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
    def get_read_vars(self, node: Any) -> set:
        if not node: return set()
        if isinstance(node, list):
            res = set()
            for x in node: res |= self.get_read_vars(x)
            return res
        if not isinstance(node, dict): return set()

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
                    res |= self.get_read_vars(arg["expr"])
                else:
                    res |= self.get_read_vars(arg)
        return res

    def get_write_vars(self, node: Any) -> set:
        if not node: return set()
        if isinstance(node, list):
            res = set()
            for x in node: res |= self.get_write_vars(x)
            return res
        if not isinstance(node, dict): return set()

        ntype = node.get("type")
        res = set()

        if ntype == "assignment":
            target = node.get("target")
            if isinstance(target, dict) and target.get("type") == "variable":
                res.add(target.get("name"))
            elif isinstance(target, str):
                res.add(target)
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
        return res

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