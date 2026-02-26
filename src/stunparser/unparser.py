


# ==========================================
# 4. 代码还原器
# ==========================================
from typing import List, Dict, Any


class STUnparser:
    """
    代码还原器 (Unparser)。
    将 STAstBuilder 生成的字典型 AST 完美还原为带有标准缩进的 IEC 61131-3 源码。
    """

    def unparse(self, node, indent=0) -> str:
        if node is None:
            return ""

        spacing = "    " * indent

        # 1. 如果是列表（多个语句或 POU），递归平铺
        if isinstance(node, list):
            return "".join([self.unparse(item, indent) for item in node])

        if not isinstance(node, dict):
            return ""

        # ==========================================
        # 2. 顶层 POU 结构 (PROGRAM / FB / FUNCTION)
        # ==========================================
        if "unit_type" in node:
            ut = node["unit_type"]
            name = node.get("name", "Unnamed")

            if ut == "FUNCTION" and "return_type" in node:
                code = f"{spacing}{ut} {name} : {node['return_type']}\n"
            else:
                code = f"{spacing}{ut} {name}\n"

            # 渲染变量块
            code += self._unparse_var_blocks(node.get("var_blocks", []), indent + 1)
            # 渲染主体语句
            code += self.unparse(node.get("body", []), indent + 1)
            code += f"{spacing}END_{ut}\n"
            return code

        # ==========================================
        # 3. 语句级还原 (Statements)
        # ==========================================
        stmt_type = node.get("stmt_type")

        if stmt_type == "assign":
            target = self._expr(node.get("target"))
            value = self._expr(node.get("value"))
            return f"{spacing}{target} := {value};\n"

        elif stmt_type == "if":
            cond = self._expr(node.get("cond"))
            code = f"{spacing}IF {cond} THEN\n"
            code += self.unparse(node.get("then_body", []), indent + 1)

            for elif_b in node.get("elif_branches", []):
                e_cond = self._expr(elif_b.get("cond"))
                code += f"{spacing}ELSIF {e_cond} THEN\n"
                code += self.unparse(elif_b.get("then_body", []), indent + 1)

            else_b = node.get("else_body", [])
            if else_b:
                code += f"{spacing}ELSE\n"
                code += self.unparse(else_b, indent + 1)

            code += f"{spacing}END_IF;\n"
            return code

        elif stmt_type == "case":
            cond = self._expr(node.get("cond"))
            code = f"{spacing}CASE {cond} OF\n"
            for entry in node.get("entries", []):
                conds = ", ".join(entry.get("conds", []))
                code += f"{spacing}    {conds}:\n"
                code += self.unparse(entry.get("body", []), indent + 2)

            else_b = node.get("else_body", [])
            if else_b:
                code += f"{spacing}    ELSE\n"
                code += self.unparse(else_b, indent + 2)
            code += f"{spacing}END_CASE;\n"
            return code

        elif stmt_type == "for":
            var = node.get("var", "")
            start = self._expr(node.get("start"))
            end = self._expr(node.get("end"))
            code = f"{spacing}FOR {var} := {start} TO {end}"
            if node.get("step"):
                code += f" BY {self._expr(node.get('step'))}"
            code += " DO\n"
            code += self.unparse(node.get("body", []), indent + 1)
            code += f"{spacing}END_FOR;\n"
            return code

        elif stmt_type == "while":
            cond = self._expr(node.get("cond"))
            code = f"{spacing}WHILE {cond} DO\n"
            code += self.unparse(node.get("body", []), indent + 1)
            code += f"{spacing}END_WHILE;\n"
            return code

        elif stmt_type == "repeat":
            code = f"{spacing}REPEAT\n"
            code += self.unparse(node.get("body", []), indent + 1)
            cond = self._expr(node.get("until_cond"))
            code += f"{spacing}UNTIL {cond}\n{spacing}END_REPEAT;\n"
            return code

        elif stmt_type == "call":
            func_name = node.get("func_name", "")
            args = [self._expr(a) for a in node.get("args", [])]
            return f"{spacing}{func_name}({', '.join(args)});\n"

        elif stmt_type == "return":
            return f"{spacing}RETURN;\n"
        elif stmt_type == "exit":
            return f"{spacing}EXIT;\n"
        elif stmt_type == "continue":
            return f"{spacing}CONTINUE;\n"

        return ""

    # ==========================================
    # 4. 表达式级还原 (Expressions)
    # ==========================================
    def _expr(self, expr) -> str:
        if expr is None: return ""
        if isinstance(expr, str): return expr
        if not isinstance(expr, dict): return str(expr)

        expr_type = expr.get("expr_type")

        if expr_type == "var":
            return expr.get("name", "")

        elif expr_type == "literal":
            return str(expr.get("value", ""))

        elif expr_type == "binop":
            left = self._expr(expr.get("left"))
            right = self._expr(expr.get("right"))
            op = expr.get("op", "")
            return f"({left} {op} {right})"

        elif expr_type == "unaryop":
            op = expr.get("op", "")
            operand = self._expr(expr.get("operand"))
            if op.upper() == "NOT":
                return f"NOT {operand}"
            return f"{op}{operand}"

        elif expr_type == "call":
            func_name = expr.get("func_name", "")
            args = [self._expr(a) for a in expr.get("args", [])]
            return f"{func_name}({', '.join(args)})"

        # 如果遇到未知的表达式，尽力将其转为字符串
        return str(expr.get("text", ""))

    # ==========================================
    # 5. 辅助方法：变量块智能聚合
    # ==========================================
    def _unparse_var_blocks(self, var_list: List[Dict], indent: int) -> str:
        """
        因为 AST 中变量是平铺的 [{"storage": "VAR", "name": "A"...}],
        我们需要把相同 storage (如 VAR_INPUT) 的变量聚合成一个块。
        """
        if not var_list:
            return ""

        spacing = "    " * indent
        code = ""
        current_storage = None

        for v in var_list:
            storage = v.get("storage", "VAR")

            # 遇到新的块类型（如从 VAR 切换到 VAR_INPUT）
            if storage != current_storage:
                if current_storage is not None:
                    code += f"{spacing}END_VAR\n"
                code += f"{spacing}{storage}\n"
                current_storage = storage

            # 渲染单个变量
            name = v.get("name", "")
            vtype = v.get("type", "INT")
            init = v.get("init_value")

            line = f"{spacing}    {name} : {vtype}"
            if init is not None:
                line += f" := {self._expr(init)}"
            line += ";\n"
            code += line

        # 闭合最后一个块
        if current_storage is not None:
            code += f"{spacing}END_VAR\n"

        return code