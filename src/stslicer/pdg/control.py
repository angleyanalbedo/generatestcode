from typing import Dict, List, Set


class PDGControlBuilder:
    """
    使用 Post-Dominance Frontier 计算控制依赖：
    1) 已有扩展 CFG（含虚拟出口） + 后支配集合 postdom
    2) 计算立即后支配 ipostdom（postdom tree）
    3) 自底向上计算每个结点 X 的 Post-Dominance Frontier(X)
    4) 反向得到 Control Dependence：如果 Y ∈ PDF(X)，则 Y 控制 X
    """

    def __init__(
        self,
        succ_ext: Dict[int, List[int]],
        exit_id: int,
        postdom: Dict[int, Set[int]],
    ):
        """
        :param succ_ext: 扩展后的 CFG 邻接表（包含虚拟出口）
        :param exit_id: 虚拟出口结点编号（通常 = 实际指令数 n）
        :param postdom: 每个结点的后支配集合（包含自己），只包括真实结点 0..n-1
                        注意：虚拟出口的 postdom 集合需要我们自己补上
        """
        self.succ_ext = succ_ext
        self.exit_id = exit_id

        # 构造包含虚拟出口的结点集合
        self.nodes: Set[int] = set(succ_ext.keys())

        # 把 postdom 扩展到包含虚拟出口
        self.postdom: Dict[int, Set[int]] = dict(postdom)
        if exit_id not in self.postdom:
            self.postdom[exit_id] = {exit_id}

        # 反向边
        self.pred_ext: Dict[int, List[int]] = {n: [] for n in self.nodes}
        for u, vs in self.succ_ext.items():
            for v in vs:
                self.pred_ext.setdefault(v, []).append(u)

    # ---------- 工具：立即后支配 & postdom tree ----------

    def _compute_ipostdom(self) -> Dict[int, int]:
        """
        根据 postdom 集合，计算每个结点的立即后支配 ipd[n]。
        朴素实现：在 postdom[n] \ {n} 中选 postdom 集合规模最小的结点。
        """
        ipd: Dict[int, int] = {}

        for n in self.nodes:
            if n == self.exit_id:
                ipd[n] = self.exit_id
                continue

            candidates = [p for p in self.postdom[n] if p != n]
            if not candidates:
                ipd[n] = self.exit_id
                continue

            # 选 postdom 集合最小的那个作为“最近”的后支配者
            ipd[n] = min(candidates, key=lambda p: len(self.postdom[p]))

        return ipd

    def _build_postdom_tree(self, ipd: Dict[int, int]) -> Dict[int, List[int]]:
        """
        根据 ipostdom，构造后支配树的 children 列表。
        """
        children: Dict[int, List[int]] = {n: [] for n in self.nodes}
        for n in self.nodes:
            if n == self.exit_id:
                continue
            parent = ipd[n]
            children.setdefault(parent, []).append(n)
        return children

    def _postdom_tree_postorder(
        self, root: int, children: Dict[int, List[int]]
    ) -> List[int]:
        """
        返回后支配树上的后序遍历序列（用于自底向上计算 PDF）。
        """
        order: List[int] = []

        def dfs(u: int):
            for v in children.get(u, []):
                dfs(v)
            order.append(u)

        dfs(root)
        return order

    # ---------- 核心：计算 Post-Dominance Frontier & 控制依赖 ----------

    def build(self) -> Dict[int, Set[int]]:
        """
        返回 ctrl_deps: Dict[int, Set[int]]
        意义：ctrl_deps[c] = { n | n 受结点 c 控制 }，即 c --ctrl--> n。
        """
        ipd = self._compute_ipostdom()
        children = self._build_postdom_tree(ipd)
        postorder = self._postdom_tree_postorder(self.exit_id, children)

        # 1) 计算每个结点 X 的 Post-Dominance Frontier(X)
        pdf: Dict[int, Set[int]] = {n: set() for n in self.nodes}

        # 自底向上遍历 postdom tree
        for x in reversed(postorder):
            # (a) 直接前驱
            for y in self.pred_ext.get(x, []):
                if ipd.get(y) != x:
                    pdf[x].add(y)

            # (b) 从子节点继承
            for z in children.get(x, []):
                for y in pdf[z]:
                    if ipd.get(y) != x:
                        pdf[x].add(y)

        # 2) 反向 PDF 得到控制依赖：如果 y ∈ PDF(x)，则 y 控制 x
        ctrl_deps: Dict[int, Set[int]] = {n: set() for n in self.nodes}
        for x in self.nodes:
            for y in pdf[x]:
                # y --ctrl--> x
                ctrl_deps.setdefault(y, set()).add(x)

        # 不需要虚拟出口的依赖边
        if self.exit_id in ctrl_deps:
            del ctrl_deps[self.exit_id]

        return ctrl_deps
