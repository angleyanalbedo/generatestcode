from typing import List, Set,Dict

class STSlicer:
    def __init__(self, parser_output: List[Dict]):
        self.body = parser_output
        self.slices = []

    def get_variables(self, node):
        """递归提取表达式中引用的所有变量 (Read Set)"""
        if not node or not isinstance(node, dict):
            return set()

        ntype = node.get("type")
        if ntype == "variable":
            return {node["name"]}
        elif ntype == "binary_op":
            return self.get_variables(node["left"]) | self.get_variables(node["right"])
        elif ntype == "unary_op":
            return self.get_variables(node["operand"])
        elif ntype == "if_statement":
            # IF 语句的依赖包含条件变量
            return self.get_variables(node["condition"])
        return set()

    def backward_slice(self, target_var: str) -> List[Dict]:
        """
        后向切片算法：
        从后往前扫，如果某行写了我们要找的变量，
        就把这行加入切片，并将这行读取的所有变量加入新的寻找目标。
        """
        relevant_vars = {target_var}
        sliced_statements = []

        # 从后往前遍历语句 (逆序分析)
        for stmt in reversed(self.body):
            added_this_round = False

            if stmt["type"] == "assignment":
                # 如果赋值目标在我们的关注列表中
                if stmt["target"] in relevant_vars:
                    sliced_statements.append(stmt)
                    # 关键逻辑：将被赋值变量移除，加入右侧引用的变量
                    relevant_vars.discard(stmt["target"])
                    relevant_vars.update(self.get_variables(stmt["expr"]))
                    added_this_round = True

            elif stmt["type"] == "if_statement":
                # 这里简化处理：如果 IF 块内有语句被切中，那么 IF 条件也必须包含
                # 在工业级切片中，这属于控制依赖 (Control Dependency)
                inner_slice = STSlicer(stmt["then_branch"]).backward_slice_set(relevant_vars)
                if inner_slice:
                    sliced_statements.append({
                        "type": "if_statement",
                        "condition": stmt["condition"],
                        "then_branch": inner_slice
                    })
                    relevant_vars.update(self.get_variables(stmt["condition"]))

        return list(reversed(sliced_statements))

    def backward_slice_set(self, var_set: Set[str]) -> List[Dict]:
        """
        基于初始变量集合进行后向切片，支持多变量依赖追踪。

        Args:
            var_set: 初始关注的变量名集合（例如：{'Motor_Speed', 'Fault_Reset'}）

        Returns:
            List[Dict]: 按照原始代码顺序排列的切片语句列表
        """
        # 复制一份初始变量集，避免修改输入参数
        relevant_vars = set(v.upper() for v in var_set)
        sliced_statements = []

        # 从后往前遍历语句 (逆序依赖分析)
        for stmt in reversed(self.body):
            if stmt["type"] == "assignment":
                target = stmt["target"].upper()
                # 命中：当前赋值语句的目标在我们的关注列表中
                if target in relevant_vars:
                    sliced_statements.append(stmt)

                    # 1. 既然已经找到了这个变量的来源，暂时移除它（除非它是自增 A := A + 1）
                    # 注意：在 PLC 中由于周期循环，通常不移除，这里视作单周期分析
                    # relevant_vars.discard(target)

                    # 2. 将等号右侧引用的所有变量加入“兴趣列表”
                    rhs_vars = self.get_variables(stmt["expr"])
                    relevant_vars.update(v.upper() for v in rhs_vars)

            elif stmt["type"] == "if_statement":
                # 对于控制流，逻辑更复杂一些：
                # 如果 IF 块内的任何语句对 relevant_vars 有贡献，
                # 那么整个 IF 结构（包括 Condition）都必须包含在切片中。

                # 递归分析 Then 块
                then_slicer = STSlicer(stmt["then_branch"])
                inner_then_slice = then_slicer.backward_slice_set(relevant_vars)

                # 递归分析 Else 块（如果存在）
                inner_else_slice = []
                if stmt.get("else_branch"):
                    else_slicer = STSlicer(stmt["else_branch"])
                    inner_else_slice = else_slicer.backward_slice_set(relevant_vars)

                if inner_then_slice or inner_else_slice:
                    # 只要分支里有东西被切中，Condition 引用的变量就变为了“必须关注”
                    cond_vars = self.get_variables(stmt["condition"])
                    relevant_vars.update(v.upper() for v in cond_vars)

                    # 构造一个新的切片后的 IF 节点
                    sliced_stmt = stmt.copy()
                    sliced_stmt["then_branch"] = inner_then_slice
                    sliced_stmt["else_branch"] = inner_else_slice
                    sliced_statements.append(sliced_stmt)

        # 因为是从后往前扫描的，最后返回前需要翻转回原始顺序
        return list(reversed(sliced_statements))