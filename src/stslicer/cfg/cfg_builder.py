from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional

from ..ir.ir_nodes import (
    IRInstr,
    IRBranchCond,
    IRGoto,
    IRLabel,
)


# ============ 指令级 CFG 结构 ============

@dataclass
class InstrCFG:
    """
    指令级控制流图（每条 IR 指令作为一个节点）
    """
    instrs: List[IRInstr]

    # i -> 后继指令下标列表
    succ: Dict[int, List[int]]

    # j -> 前驱指令下标列表
    pred: Dict[int, List[int]]

    # 入口指令下标（通常为 0）
    entry: int

    # 所有可能终止的指令下标集合
    exits: Set[int]


class CFGBuilder:
    """
    根据 IR 指令序列构造指令级 CFG。

    用法示例：
        irb = IRBuilder(pou_name="TEST19")
        ...
        instrs = irb.instrs

        cfg_builder = CFGBuilder(instrs)
        cfg = cfg_builder.build()

        # 查看某条指令的后继
        print(cfg.succ[10])

    """

    def __init__(self, instrs: List[IRInstr]):
        self.instrs = instrs
        self.n = len(instrs)

        # label 名 -> 指令下标
        self.label_index: Dict[str, int] = {}

        # i -> succ indices
        self.succ: Dict[int, List[int]] = {i: [] for i in range(self.n)}

        # j -> pred indices
        self.pred: Dict[int, List[int]] = {i: [] for i in range(self.n)}

    # ---------- 外部主入口 ----------

    def build(self) -> InstrCFG:
        """
        构造完整的指令级 CFG。
        """
        self._collect_labels()
        self._build_edges()
        entry = 0 if self.n > 0 else -1
        exits = {i for i in range(self.n) if not self.succ[i]}
        return InstrCFG(
            instrs=self.instrs,
            succ=self.succ,
            pred=self.pred,
            entry=entry,
            exits=exits,
        )

    # ---------- 内部步骤 1：扫描 label ----------

    def _collect_labels(self):
        """
        扫描 IR 指令，建立 label -> 指令下标 的映射。
        """
        for idx, instr in enumerate(self.instrs):
            if isinstance(instr, IRLabel):
                # 假设 IRLabel 有字段 name: str
                self.label_index[instr.name] = idx

    # ---------- 内部步骤 2：根据指令类型加边 ----------

    def _add_edge(self, i: int, j: int):
        """
        在 CFG 中加入一条边 i -> j，同时维护 succ 和 pred。
        """
        if i < 0 or i >= self.n or j < 0 or j >= self.n:
            return
        if j not in self.succ[i]:
            self.succ[i].append(j)
        if i not in self.pred[j]:
            self.pred[j].append(i)

    def _build_edges(self):
        """
        遍历每条指令，根据类型添加控制流边。
        """
        for i, instr in enumerate(self.instrs):
            # 1) 条件跳转：BRANCH cond, true_label, false_label
            if isinstance(instr, IRBranchCond):
                t_label = instr.true_label
                f_label = instr.false_label

                if t_label not in self.label_index:
                    raise KeyError(f"[CFGBuilder] unknown label in true_label: {t_label}")
                if f_label not in self.label_index:
                    raise KeyError(f"[CFGBuilder] unknown label in false_label: {f_label}")

                t_idx = self.label_index[t_label]
                f_idx = self.label_index[f_label]

                self._add_edge(i, t_idx)
                self._add_edge(i, f_idx)

                # 注意：条件跳转已经显式指定 true/false 两个后继，
                # 不再添加顺序后继 i+1

            # 2) 无条件跳转：GOTO target_label
            elif isinstance(instr, IRGoto):
                target_label = instr.target_label
                if target_label not in self.label_index:
                    raise KeyError(f"[CFGBuilder] unknown label in goto: {target_label}")
                j = self.label_index[target_label]
                self._add_edge(i, j)
                # 无条件跳转不再拥有 fall-through（不连到 i+1）

            else:
                # 3) 其它指令（Assign / BinOp / Call / Label 等）顺序连接到下一条
                if i + 1 < self.n:
                    self._add_edge(i, i + 1)


# ============ （可选）Basic Block 结构示例 ============

@dataclass
class BasicBlock:
    """
    一个 basic block：包含一段连续的指令 [start, end]（闭区间）
    """
    id: int
    instr_indices: List[int] = field(default_factory=list)
    succ: List[int] = field(default_factory=list)  # 后继 block id 列表
    pred: List[int] = field(default_factory=list)  # 前驱 block id 列表


@dataclass
class BlockCFG:
    """
    基于 basic block 的 CFG（可选扩展）
    """
    instrs: List[IRInstr]
    blocks: List[BasicBlock]
    entry_block: Optional[int]
    exit_blocks: Set[int]


class BlockCFGBuilder:
    """
    基于指令级 CFG 聚合 basic blocks 的一个示例实现。
    如果你暂时只用 instr 级 CFG，可以先不使用这个类。
    """

    def __init__(self, instr_cfg: InstrCFG):
        self.instr_cfg = instr_cfg
        self.instrs = instr_cfg.instrs
        self.n = len(self.instrs)

    def build(self) -> BlockCFG:
        if self.n == 0:
            return BlockCFG(
                instrs=[],
                blocks=[],
                entry_block=None,
                exit_blocks=set(),
            )

        leaders = self._find_leaders()
        blocks = self._build_blocks(leaders)
        self._connect_blocks(blocks)

        entry_block = 0  # leaders 按顺序，第一个就是入口 block
        exit_blocks = {
            b.id for b in blocks if self._block_is_exit(b, blocks)
        }

        return BlockCFG(
            instrs=self.instrs,
            blocks=blocks,
            entry_block=entry_block,
            exit_blocks=exit_blocks,
        )

    def _find_leaders(self) -> List[int]:
        """
        经典算法：
          - 第一条指令是 leader
          - 任何跳转目标指令是 leader
          - 任何跳转指令的下一条（如果存在）是 leader
        """
        leaders: Set[int] = set()
        leaders.add(0)

        # 收集跳转目标
        for i, instr in enumerate(self.instrs):
            if isinstance(instr, IRBranchCond):
                # true/false label 的指令下标
                # 需要一个 label -> index 映射，这里复用 InstrCFG 的 pred/succ 或重新扫一遍 label 也行
                # 为简单起见，我们重新扫一次 label：
                pass  # 你可以参考上面的 CFGBuilder._collect_labels 实现

            elif isinstance(instr, IRGoto):
                pass  # 同上，找到 target_label 对应的 index

        # 跳转后的下一条指令也是 leader
        for i, instr in enumerate(self.instrs):
            if isinstance(instr, (IRBranchCond, IRGoto)):
                if i + 1 < self.n:
                    leaders.add(i + 1)

        return sorted(leaders)

    def _build_blocks(self, leaders: List[int]) -> List[BasicBlock]:
        """
        根据 leaders 划分 basic blocks。
        """
        blocks: List[BasicBlock] = []
        for bi, start in enumerate(leaders):
            end = (leaders[bi + 1] - 1) if bi + 1 < len(leaders) else (self.n - 1)
            instr_indices = list(range(start, end + 1))
            blocks.append(
                BasicBlock(
                    id=bi,
                    instr_indices=instr_indices,
                )
            )
        return blocks

    def _connect_blocks(self, blocks: List[BasicBlock]):
        """
        利用指令级 CFG，把 basic block 之间的前驱/后继关系连起来。
        block 的后继 = block 最后一条指令的 succ 所在 block id 集合。
        """
        # 快速索引：指令 index -> block id
        instr2block: Dict[int, int] = {}
        for b in blocks:
            for i in b.instr_indices:
                instr2block[i] = b.id

        for b in blocks:
            if not b.instr_indices:
                continue
            last_i = b.instr_indices[-1]
            succ_instrs = self.instr_cfg.succ[last_i]
            for j in succ_instrs:
                bid = instr2block[j]
                if bid not in b.succ:
                    b.succ.append(bid)
                if b.id not in blocks[bid].pred:
                    blocks[bid].pred.append(b.id)

    def _block_is_exit(self, b: BasicBlock, blocks: List[BasicBlock]) -> bool:
        """
        如果 block 的最后一条指令没有 succ，则视为出口 block。
        """
        if not b.instr_indices:
            return False
        last_i = b.instr_indices[-1]
        return len(self.instr_cfg.succ[last_i]) == 0
