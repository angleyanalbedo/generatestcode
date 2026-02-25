import random
from lark import Transformer, v_args
from typing import Any, List, Dict

from ..stparser.lark.analyzer import STSemanticAnalyzer


class STRewriterDeprecated(Transformer):
    """
    通过修改 AST 节点实现代码重构与数据增强。
    """

    def __init__(self, rename_map: dict = None, mode: str = "augment"):
        super().__init__()
        self.rename_map = rename_map or {}
        self.mode = mode  # augment: 随机增强, rename: 强制重命名
        self.analyzer = STSemanticAnalyzer()

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
        Lark Transformer 钩子：处理语句列表。
        在这里实现基于依赖分析的“指令重排”。
        """
        # 如果 body 里只有 0 或 1 条语句，没法重排
        if len(items) < 2:
            return items

        new_items = list(items)
        # 我们进行多次随机交换尝试
        for _ in range(len(new_items)):
            # 随机选择两个相邻的索引
            i = random.randint(0, len(new_items) - 2)
            stmt_a = new_items[i]
            stmt_b = new_items[i+1]

            # --- 核心依赖检查 ---
            # 1. 提取读写集合
            r_a, w_a = self.analyzer.get_read_vars(stmt_a), self.analyzer.get_write_vars(stmt_a)
            r_b, w_b = self.analyzer.get_read_vars(stmt_b), self.analyzer.get_write_vars(stmt_b)

            # 2. 判断是否存在冲突 (Data Hazard)
            # RAW (Read After Write): A 写 B 读
            # WAR (Write After Read): A 读 B 写
            # WAW (Write After Write): A 写 B 写
            has_dependency = (w_a & r_b) or (r_a & w_b) or (w_a & w_b)

            if not has_dependency:
                # 如果没有依赖，50% 概率交换顺序
                if random.random() > 0.5:
                    new_items[i], new_items[i+1] = new_items[i+1], new_items[i]

        return new_items


class STRewriter:
    """
    针对字典型 AST 的重写器。
    基于数据依赖分析 (Data Dependency Analysis)，在保证语义等价的前提下，
    通过修改 AST 节点实现代码重构与数据增强。
    """

    def __init__(self, analyzer: Any, rename_map: dict = None, mode: str = "augment"):
        """
        :param analyzer: 语义分析器实例，需提供 get_read_vars 和 get_write_vars 方法
        :param rename_map: 强制重命名映射字典
        :param mode: 'augment' (随机增强) 或 'rename' (仅重命名)
        """
        self.analyzer = analyzer
        self.rename_map = rename_map or {}
        self.mode = mode

    def rewrite(self, node: Any) -> Any:
        """递归遍历并变异 AST 节点"""

        # 1. 如果是代码块 (语句列表)
        if isinstance(node, list):
            # 先递归处理内部的每一条语句
            processed_list = [self.rewrite(item) for item in node]
            # 然后在当前层级尝试进行指令重排
            return self._reorder_body(processed_list)

        # 2. 如果是 AST 节点 (字典)
        if isinstance(node, dict):
            # 深层遍历：先处理所有子节点
            new_node = {}
            for k, v in node.items():
                new_node[k] = self.rewrite(v)

            # 拿到当前节点的类型，开始实施变异策略
            ntype = new_node.get("type")

            # --- 策略 A: 算术等价变换 (A + B -> B + A) ---
            if ntype == "binary_op" and new_node.get("op") in ["+", "*"]:
                if random.random() > 0.5:
                    new_node["left"], new_node["right"] = new_node["right"], new_node["left"]

            # --- 策略 B: 逻辑变换 (Condition Inversion) ---
            # 将 IF A THEN B ELSE C 转换为 IF NOT A THEN C ELSE B
            elif ntype == "if_statement" and new_node.get("else_branch"):
                if random.random() > 0.5:
                    original_cond = new_node["condition"]
                    new_node["condition"] = {
                        "type": "unary_op",
                        "op": "NOT",
                        "operand": original_cond
                    }
                    # 交换 THEN 和 ELSE 分支
                    new_node["then_branch"], new_node["else_branch"] = new_node["else_branch"], new_node["then_branch"]

            # --- 策略 C: 变量名混淆 (Variable Obfuscation) ---
            elif ntype == "variable":
                name = new_node["name"]

                # 如果在强制重命名映射中，优先替换
                if name in self.rename_map:
                    new_node["name"] = self.rename_map[name]

                # 否则，如果是 augment 模式，随机加前缀
                elif self.mode == "augment" and random.random() > 0.7:
                    # 简单过滤：全大写的通常是常量或系统字面量，不混淆；防止重复加前缀
                    if not name.isupper() and not name.startswith("var_"):
                        new_node["name"] = f"var_{name}"

            return new_node

        # 3. 其他基本类型 (字符串、数字等)，直接返回
        return node

    def _reorder_body(self, items: List[Any]) -> List[Any]:
        """
        基于依赖分析的“指令重排” (Instruction Scheduling)。
        检测 RAW, WAR, WAW 数据冒险，确保乱序后的代码逻辑绝对安全。
        """
        # 如果 body 里只有 0 或 1 条语句，没法重排
        if len(items) < 2:
            return items

        new_items = list(items)

        # 我们进行多次随机交换尝试 (尝试次数等于语句条数)
        for _ in range(len(new_items)):
            # 随机选择两个相邻的索引
            i = random.randint(0, len(new_items) - 2)
            stmt_a = new_items[i]
            stmt_b = new_items[i + 1]

            # --- 核心依赖检查 ---
            # 1. 提取读写集合
            r_a = self.analyzer.get_read_vars(stmt_a)
            w_a = self.analyzer.get_write_vars(stmt_a)

            r_b = self.analyzer.get_read_vars(stmt_b)
            w_b = self.analyzer.get_write_vars(stmt_b)

            # 2. 判断是否存在冲突 (Data Hazard)
            # RAW (Read After Write): A 写 B 读
            # WAR (Write After Read): A 读 B 写
            # WAW (Write After Write): A 写 B 写
            has_dependency = (w_a & r_b) or (r_a & w_b) or (w_a & w_b)

            # 3. 如果没有依赖，50% 概率交换它们的顺序
            if not has_dependency and random.random() > 0.5:
                new_items[i], new_items[i + 1] = new_items[i + 1], new_items[i]

        return new_items


