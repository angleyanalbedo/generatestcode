import random
from typing import Any, List

class STRewriter:
    """
    针对字典型 AST 的重写器 (已适配新版 ANTLR 字典结构)。
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
            # 先递归处理内部的每一条语句/节点
            processed_list = [self.rewrite(item) for item in node]
            # 然后在当前层级尝试进行指令重排
            return self._reorder_body(processed_list)

        # 2. 如果是 AST 节点 (字典)
        if isinstance(node, dict):
            # 深层遍历：先处理所有子节点 (自底向上变异)
            new_node = {}
            for k, v in node.items():
                new_node[k] = self.rewrite(v)

            # 拿到当前节点的类型，开始实施变异策略
            stmt_type = new_node.get("stmt_type")
            expr_type = new_node.get("expr_type")

            # --- 策略 A: 算术与逻辑等价变换 (A + B -> B + A) ---
            if expr_type == "binop" and new_node.get("op") in ["+", "*", "AND", "OR"]:
                if random.random() > 0.5:
                    new_node["left"], new_node["right"] = new_node["right"], new_node["left"]

            # --- 策略 B: 逻辑变换 (Condition Inversion) ---
            # 将 IF A THEN B ELSE C 转换为 IF NOT A THEN C ELSE B
            # 💡 安全保护：只有当存在 ELSE 且 不存在 ELSIF 时，翻转才是绝对安全的
            elif stmt_type == "if" and new_node.get("else_body") and not new_node.get("elif_branches"):
                if random.random() > 0.5:
                    original_cond = new_node["cond"]
                    new_node["cond"] = {
                        "expr_type": "unaryop",
                        "op": "NOT",
                        "operand": original_cond
                    }
                    # 交换 THEN 和 ELSE 分支
                    new_node["then_body"], new_node["else_body"] = new_node["else_body"], new_node["then_body"]

            # --- 策略 C: 变量名混淆 (Variable Obfuscation) ---
            elif expr_type == "var":
                name = new_node.get("name", "")

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

            # --- 核心依赖检查 (使用咱们最新更新的 DependencyAnalyzer) ---
            r_a = self.analyzer.get_read_vars(stmt_a)
            w_a = self.analyzer.get_write_vars(stmt_a)

            r_b = self.analyzer.get_read_vars(stmt_b)
            w_b = self.analyzer.get_write_vars(stmt_b)

            # 判断是否存在冲突 (Data Hazard)
            has_dependency = (w_a & r_b) or (r_a & w_b) or (w_a & w_b)

            # 如果没有依赖，50% 概率交换它们的顺序
            if not has_dependency and random.random() > 0.5:
                new_items[i], new_items[i + 1] = new_items[i + 1], new_items[i]

        return new_items