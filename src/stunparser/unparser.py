


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