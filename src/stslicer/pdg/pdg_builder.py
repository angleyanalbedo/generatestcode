from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Literal, Tuple

from ..ir.ir_nodes import IRInstr, IRBranchCond
from ..cfg.cfg_builder import InstrCFG
from ..dataflow.def_use import DefUseResult

EdgeType = Literal["data", "control"]


# =========================
#  第一层：IR 级 PDG（后继边）
# =========================

@dataclass
class PDG:
    """
    程序依赖图（Program Dependence Graph）

    节点：每条 IR 指令（索引 0..n-1）
    边：
      - data_deps[u] ：u 的数据依赖后继集合（u -> v）
      - control_deps[u] ：u 的控制依赖后继集合（u -> v）
    """
    instrs: List[IRInstr]
    data_deps: Dict[int, Set[int]] = field(default_factory=dict)
    control_deps: Dict[int, Set[int]] = field(default_factory=dict)


class PDGBuilder:
    """
    PDG 构造器（IR 级，使用“后继”表示依赖）。

    输入：
      - 指令级 CFG (InstrCFG)
      - Def-Use 分析结果 (DefUseResult)

    输出：
      - PDG（包含数据依赖 + 控制依赖）
    """

    def __init__(self, cfg: InstrCFG, du: DefUseResult):
        self.cfg = cfg
        self.du = du
        self.instrs = cfg.instrs
        self.n = len(self.instrs)

        # 扩展后的后继（包含虚拟出口）
        self.succ_ext: Dict[int, List[int]] = {}
        self.virtual_exit: Optional[int] = None

        # Postdominator 集合
        self.postdom: Dict[int, Set[int]] = {}

        # PDG 边
        self.data_deps: Dict[int, Set[int]] = {}
        self.control_deps: Dict[int, Set[int]] = {}

    # -------- 外部主入口 --------

    def build(self) -> PDG:
        """
        主入口：构造 PDG（数据依赖 + 控制依赖）。
        """
        # 1) 构造带虚拟出口的扩展后继图 & 求 postdom
        self._build_extended_successors()
        self._compute_postdominators()

        # 2) 基于 Def-Use 构造数据依赖边
        self._build_data_deps()

        # 3) 基于 postdom frontier 构造控制依赖边
        self._build_control_deps()

        return PDG(
            instrs=self.instrs,
            data_deps=self.data_deps,
            control_deps=self.control_deps,
        )

    # -------- 步骤 1：扩展 CFG 为单出口图 --------

    def _build_extended_successors(self):
        """
        为了做 postdom 分析，我们需要一个“单出口”的图：
          - 新增一个虚拟出口节点 VE（编号 = n）
          - 对每个 CFG 的出口节点 e（succ[e] 为空），加入一条 e -> VE
        """
        n_real = self.n
        ve = n_real
        self.virtual_exit = ve

        # 初始化 succ_ext
        self.succ_ext = {i: list(self.cfg.succ[i]) for i in range(n_real)}
        self.succ_ext[ve] = []

        for e in self.cfg.exits:
            self.succ_ext[e].append(ve)

    # -------- 步骤 2：Postdominator 分析 --------

    def _compute_postdominators(self):
        """
        在扩展图上（含虚拟出口）做 postdom 分析。
        使用经典迭代算法：

          PD[ve] = {ve}
          PD[n] = 所有节点（初始）
          迭代：
            PD[n] = {n} ∪ 交集( PD[s] for s in succ_ext[n] )

        计算完后，只保留真实结点 0..n-1 的 postdom 结果。
        """
        assert self.virtual_exit is not None
        ve = self.virtual_exit
        all_nodes: Set[int] = set(self.succ_ext.keys())

        PD: Dict[int, Set[int]] = {}
        for n in all_nodes:
            if n == ve:
                PD[n] = {ve}
            else:
                PD[n] = set(all_nodes)

        changed = True
        while changed:
            changed = False
            for n in all_nodes:
                if n == ve:
                    continue

                succs = self.succ_ext[n]
                if not succs:
                    new_pd_succ = set(all_nodes)
                else:
                    new_pd_succ = set(all_nodes)
                    for s in succs:
                        new_pd_succ &= PD[s]

                new_pd = {n} | new_pd_succ
                if new_pd != PD[n]:
                    PD[n] = new_pd
                    changed = True

        # 只保留真实结点 0..n-1 的 postdom 结果
        self.postdom = {i: PD[i] for i in range(self.n)}

    # -------- 步骤 3：数据依赖边 --------

    def _build_data_deps(self):
        """
        使用 DefUseResult 中的 def2uses 构造数据依赖边：
          对于 (def_idx, var) -> [use_idx ...]
          在 PDG 中加入 def_idx -> use_idx（数据依赖）
        """
        for (def_idx, var), uses in self.du.def2uses.items():
            for use_idx in uses:
                self._add_data_dep(def_idx, use_idx)

    def _add_data_dep(self, src: int, dst: int):
        if src == dst:
            return
        self.data_deps.setdefault(src, set()).add(dst)

    # -------- 步骤 4：控制依赖边 --------

    def _build_control_deps(self):
        """
        使用 post-dominator 信息构造控制依赖边。

        思路：
          对每个条件分支指令 b：
            - 后支配集合 PD[b]
            - 合流结点集合 stop_nodes = PD[b] - {b}
            对每个后继 s：
              从 s 沿 CFG 前进，直到遇到 stop_nodes 为止，
              路上所有节点都控制依赖于 b。
        """
        ctrl = {i: set() for i in range(self.n)}

        for idx, instr in enumerate(self.instrs):
            if not isinstance(instr, IRBranchCond):
                continue

            branch_idx = idx
            succs = self.cfg.succ.get(branch_idx, [])
            postdom_b = self.postdom.get(branch_idx, set())
            # b 自己一定在 postdom[b] 里，合流点是 postdom_b - {b}
            stop_nodes = postdom_b - {branch_idx}

            for s in succs:
                self._propagate_ctrl_from_succ(branch_idx, s, stop_nodes, ctrl)

        # 去掉空集
        self.control_deps = {k: v for k, v in ctrl.items() if v}

    def _propagate_ctrl_from_succ(
        self,
        branch_idx: int,
        start: int,
        stop_nodes: Set[int],
        ctrl: Dict[int, Set[int]],
    ):
        visited: Set[int] = set()
        worklist: List[int] = [start]

        while worklist:
            n = worklist.pop()
            if n in visited:
                continue
            visited.add(n)

            # 如果到达 b 的后支配结点（合流点）就停止，不记录依赖
            if n in stop_nodes:
                continue

            if 0 <= n < self.n:
                ctrl[branch_idx].add(n)

            for succ in self.cfg.succ.get(n, []):
                if succ not in visited:
                    worklist.append(succ)


# =====================================
#  第二层：面向切片的前驱式 PDG 封装
# =====================================

@dataclass
class PdgNode:
    """
    面向切片的 PDG 节点封装：
      - id ：IR 指令索引
      - ast_node ：可以绑定到 AST 节点或 IR 指令本身
      - lineno ：源代码行号（如果有的话）
    """
    id: int
    ast_node: object
    lineno: Optional[int] = None


@dataclass
class ProgramDependenceGraph:
    """
    为切片算法提供的“前驱”风格 PDG：
      - data_pred[v] ：所有对 v 有数据依赖的前驱节点集合
      - ctrl_pred[v] ：所有对 v 有控制依赖的前驱节点集合
    """
    nodes: Dict[int, PdgNode] = field(default_factory=dict)
    data_pred: Dict[int, Set[int]] = field(default_factory=dict)
    ctrl_pred: Dict[int, Set[int]] = field(default_factory=dict)

    def add_node(self, node_id: int, ast_node, lineno: Optional[int] = None):
        self.nodes[node_id] = PdgNode(node_id, ast_node, lineno)

    def add_data_edge(self, src: int, dst: int):
        self.data_pred.setdefault(dst, set()).add(src)

    def add_ctrl_edge(self, src: int, dst: int):
        self.ctrl_pred.setdefault(dst, set()).add(src)

    def predecessors(self, node_id: int) -> List[Tuple[int, EdgeType]]:
        res: List[Tuple[int, EdgeType]] = []
        for p in self.data_pred.get(node_id, ()):
            res.append((p, "data"))
        for p in self.ctrl_pred.get(node_id, ()):
            res.append((p, "control"))
        return res


def build_program_dependence_graph(ir_instrs: List[IRInstr], pdg: PDG) -> ProgramDependenceGraph:
    """
    辅助函数：把“后继风格”的 PDG 转换成“前驱风格”的 ProgramDependenceGraph，
    方便切片算法使用。
    """
    g = ProgramDependenceGraph()

    # 1. 建节点（这里直接把 IR 指令作为 ast_node 绑定）
    for idx, instr in enumerate(ir_instrs):
        lineno = getattr(instr, "lineno", None)
        g.add_node(idx, ast_node=instr, lineno=lineno)

    # 2. 把 data_deps/control_deps 反向成前驱
    for src, dsts in pdg.data_deps.items():
        for dst in dsts:
            g.add_data_edge(src, dst)

    for src, dsts in pdg.control_deps.items():
        for dst in dsts:
            g.add_ctrl_edge(src, dst)

    return g
