import random
from lark import Transformer, v_args


class STRewriter(Transformer):
    """
    通过修改 AST 节点实现代码重构与数据增强。
    """

    def __init__(self, rename_map: dict = None, mode: str = "augment"):
        super().__init__()
        self.rename_map = rename_map or {}
        self.mode = mode  # augment: 随机增强, rename: 强制重命名

    @v_args(inline=True)
    def IDENT(self, token):
        """
        1. 变量重命名：实现语义不变的混淆
        """
        name = str(token)
        # 如果在重命名映射中，则替换；否则根据模式随机加前缀
        if name in self.rename_map:
            return self.rename_map[name]

        if self.mode == "augment" and not name.isupper():  # 简单过滤掉可能是关键字的标识符
            return f"var_{name}"
        return name

    def if_stmt(self, items):
        """
        2. 逻辑变换：条件反转 (Condition Inversion)
        将 IF A THEN B ELSE C END_IF
        转换为 IF NOT A THEN C ELSE B END_IF
        """
        condition = items[0]
        then_body = items[1]

        # 只有在有 ELSE 分支且随机命中的情况下才进行反转增强
        if len(items) >= 3 and random.random() > 0.5:
            else_body = items[-1]
            return {
                "type": "if_statement",
                "condition": {"type": "unary_op", "op": "NOT", "operand": condition},
                "then_branch": else_body,
                "else_branch": then_body
            }

        return {
            "type": "if_statement",
            "condition": condition,
            "then_branch": then_body,
            "else_branch": items[-1] if len(items) % 2 == 0 else None
        }

    def assign_stmt(self, items):
        """
        3. 算术等价变换：比如 A := B + 1 变为 A := 1 + B
        """
        target = items[0]
        expr = items[1]

        if isinstance(expr, dict) and expr.get("op") == "+" and random.random() > 0.7:
            # 交换加法左右两边
            expr["left"], expr["right"] = expr["right"], expr["left"]

        return {"type": "assignment", "target": target, "expr": expr}

    def body(self, items):
        """
        4. 语句乱序（仅限无依赖的语句）
        注意：这需要配合你的 STSlicer 检查数据依赖，这里仅示意
        """
        # 如果两条连续赋值语句互不引用，可以交换顺序
        return items

# 使用方法
# tree = parser.parse(original_code)
# new_tree = STRewriter().transform(tree)
# new_code = new_tree.pretty() # Lark 提供的漂亮格式化输出