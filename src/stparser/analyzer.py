from typing import Any





class DependencyAnalyzer:
    """独立的 AST 数据依赖分析器，用于提取读/写变量集合"""

    @classmethod
    def get_read_vars(cls, node: Any) -> set:
        if not node: return set()
        if isinstance(node, list):
            res = set()
            for x in node: res |= cls.get_read_vars(x)
            return res
        if not isinstance(node, dict): return set()

        ntype = node.get("type")
        res = set()

        if ntype == "variable":
            res.add(node["name"])
        elif ntype == "binary_op":
            res |= cls.get_read_vars(node["left"])
            res |= cls.get_read_vars(node["right"])
        elif ntype == "unary_op":
            res |= cls.get_read_vars(node["operand"])
        elif ntype == "assignment":
            res |= cls.get_read_vars(node["expr"])
            if isinstance(node.get("target_metadata"), dict):
                res |= cls.get_read_vars(node["target_metadata"])
        elif ntype == "if_statement":
            res |= cls.get_read_vars(node["condition"])
            res |= cls.get_read_vars(node["then_branch"])
            if node.get("else_branch"):
                res |= cls.get_read_vars(node["else_branch"])
        elif ntype == "case_statement":
            res |= cls.get_read_vars(node["expression"])
            for selection in node.get("selections", []):
                res |= cls.get_read_vars(selection["body"])
            if node.get("else_branch"):
                res |= cls.get_read_vars(node["else_branch"])
        elif ntype == "for_loop":
            res |= cls.get_read_vars(node["from"])
            res |= cls.get_read_vars(node["to"])
            res |= cls.get_read_vars(node["step"])
            res |= cls.get_read_vars(node["body"])
        elif ntype == "while_loop":
            res |= cls.get_read_vars(node["condition"])
            res |= cls.get_read_vars(node["body"])
        elif ntype == "func_call":
            for arg in node.get("arg_list", []):
                if isinstance(arg, dict) and "param_name" in arg:
                    res |= cls.get_read_vars(arg["expr"])
                else:
                    res |= cls.get_read_vars(arg)
        return res

    @classmethod
    def get_write_vars(cls, node: Any) -> set:
        if not node: return set()
        if isinstance(node, list):
            res = set()
            for x in node: res |= cls.get_write_vars(x)
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
            res |= cls.get_write_vars(node.get("then_branch"))
            res |= cls.get_write_vars(node.get("else_branch"))
        elif ntype == "case_statement":
            for selection in node.get("selections", []):
                res |= cls.get_write_vars(selection.get("body"))
            res |= cls.get_write_vars(node.get("else_branch"))
        elif ntype == "for_loop":
            res |= cls.get_write_vars(node.get("body"))
        elif ntype == "while_loop":
            res |= cls.get_write_vars(node.get("body"))
        return res
