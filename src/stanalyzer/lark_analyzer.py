from typing import Any

from lark import Transformer, v_args

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
