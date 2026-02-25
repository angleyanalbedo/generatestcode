from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Dict, Set, Tuple, Optional

from .var_access import VarAccess
from ..ast.nodes import (
    VarRef,
    ArrayAccess,
    FieldAccess,
    Expr,
    Assignment,
    CallStmt,
)

from ..ir.ir_nodes import (
    IRInstr,
    IRAssign,
    IRBinOp,
    IRCall,
    IRBranchCond,
    IRGoto,
    IRLabel,
)
from ..cfg.cfg_builder import InstrCFG


VarName = str
DefSite = Tuple[int, VarName]
UseSite = Tuple[int, VarName]


def _normalize_var(name: Optional[str]) -> Optional[str]:
    """
    变量名归一化：
      - None 直接返回
      - 截断数组下标：var[i*2-1] -> var
      - 过滤字面量（数字、TRUE/FALSE），返回 None
    """
    if name is None:
        return None
    if not isinstance(name, str):
        return None

    s = name.strip()

    # # 去掉数组下标
    # bracket_pos = s.find("[")
    # if bracket_pos != -1:
    #     s = s[:bracket_pos]

    # 过滤布尔字面量
    if s.upper() in ("TRUE", "FALSE"):
        return None

    # 过滤纯整数/浮点数字面量（简单判断）
    try:
        float(s)
        return None  # 是数字字面量，不当变量
    except ValueError:
        pass

    # 这里可以根据需要再过滤十六进制字面量、16#01 之类，
    # 不过这些目前通常在 IR 中已经被作为字面量常量提前处理了。

    return s

def _expr_to_str_fallback(e: Expr) -> str:
    """
    简单的 expr -> 字符串，用于数组下标记录。
    如果你后面有正式的 AST->ST pretty printer，可以在这里替换掉。
    """
    # 尝试使用节点自己的 pretty 方法
    to_source = getattr(e, "to_source", None)
    if callable(to_source):
        try:
            return to_source()
        except Exception:
            pass
    # 兜底：用 repr 或 class 名
    return repr(e)

def collect_var_accesses(expr: Expr) -> Set[VarAccess]:
    result: Set[VarAccess] = set()

    def _walk(e: Expr, fields=(), indices=()):
        if isinstance(e, VarRef):
            result.add(
                VarAccess(
                    base=e.name,
                    fields=tuple(fields),
                    indices=tuple(indices),
                )
            )
            return

        if isinstance(e, ArrayAccess):
            idx_str = _expr_to_str_fallback(e.index)
            _walk(
                e.base,
                fields=fields,
                indices=indices + (idx_str,),
            )
            return

        if isinstance(e, FieldAccess):
            _walk(
                e.base,
                fields=fields + (e.field,),
                indices=indices,
            )
            return

        # 其他表达式类型：通过反射往下找 Expr / List[Expr]
        for attr in vars(e).values():
            if isinstance(attr, Expr):
                _walk(attr, fields, indices)
            elif isinstance(attr, list):
                for item in attr:
                    if isinstance(item, Expr):
                        _walk(item, fields, indices)

    _walk(expr)
    return result

@dataclass
class DefUseResult:
    def_vars: List[Set[VarName]]
    use_vars: List[Set[VarName]]

    # 结构化访问（可选，用于后续更精细切片）
    def_accesses: List[Set[VarAccess]] = field(default_factory=list)
    use_accesses: List[Set[VarAccess]] = field(default_factory=list)

    rd_in: List[Set[DefSite]] = field(default_factory=list)
    rd_out: List[Set[DefSite]] = field(default_factory=list)

    def2uses: Dict[DefSite, List[int]] = field(default_factory=dict)
    use2defs: Dict[UseSite, List[int]] = field(default_factory=dict)
    var2defs: Dict[VarName, Set[int]] = field(default_factory=dict)



class DefUseAnalyzer:
    """
    在指令级 CFG 上做 Def-Use 分析。
    """

    def __init__(self, cfg: InstrCFG, ir2ast_stmt: Optional[List[object]] = None):
        self.cfg = cfg
        self.instrs = cfg.instrs
        self.n = len(self.instrs)

        # 关键：这里保存 IR index -> AST 语句的映射
        self.ir2ast_stmt: Optional[List[object]] = ir2ast_stmt

        self.def_vars: List[Set[VarName]] = [set() for _ in range(self.n)]
        self.use_vars: List[Set[VarName]] = [set() for _ in range(self.n)]
        self.def_accesses: List[Set[VarAccess]] = [set() for _ in range(self.n)]
        self.use_accesses: List[Set[VarAccess]] = [set() for _ in range(self.n)]

        self.var2defs: Dict[VarName, Set[int]] = {}

        self.gen: List[Set[DefSite]] = [set() for _ in range(self.n)]
        self.kill: List[Set[DefSite]] = [set() for _ in range(self.n)]
        self.rd_in: List[Set[DefSite]] = [set() for _ in range(self.n)]
        self.rd_out: List[Set[DefSite]] = [set() for _ in range(self.n)]

    def analyze(self) -> DefUseResult:
        self._compute_def_use()
        self._compute_gen_kill()
        self._solve_reaching_defs()
        def2uses, use2defs = self._build_def_use_chains()

        return DefUseResult(
            def_vars=self.def_vars,
            use_vars=self.use_vars,
            def_accesses=self.def_accesses,
            use_accesses=self.use_accesses,
            rd_in=self.rd_in,
            rd_out=self.rd_out,
            def2uses=def2uses,
            use2defs=use2defs,
            var2defs=self.var2defs,
        )
    # ---------- 步骤 1：每条指令的 DEF / USE ----------

    def _compute_def_use(self):
        # 先保留你原来那部分字符串变量名的逻辑
        for i, instr in enumerate(self.instrs):
            defs: Set[VarName] = set()
            uses: Set[VarName] = set()

            if isinstance(instr, IRAssign):
                v = _normalize_var(instr.target)
                if v is not None:
                    defs.add(v)
                u = _normalize_var(instr.src)
                if u is not None:
                    uses.add(u)

            elif isinstance(instr, IRBinOp):
                v = _normalize_var(instr.dest)
                if v is not None:
                    defs.add(v)
                u1 = _normalize_var(instr.left)
                u2 = _normalize_var(instr.right)
                if u1 is not None:
                    uses.add(u1)
                if u2 is not None:
                    uses.add(u2)

            elif isinstance(instr, IRCall):
                if instr.dest is not None:
                    v = _normalize_var(instr.dest)
                    if v is not None:
                        defs.add(v)
                for arg in instr.args:
                    u = _normalize_var(arg)
                    if u is not None:
                        uses.add(u)

            elif isinstance(instr, IRBranchCond):
                u = _normalize_var(instr.cond)
                if u is not None:
                    uses.add(u)

            # IRGoto / IRLabel 无 DEF/USE

            self.def_vars[i] = defs
            self.use_vars[i] = uses

            for v in defs:
                self.var2defs.setdefault(v, set()).add(i)

        # 再用 AST 做结构化访问（可选）
        if self.ir2ast_stmt is not None:
            for i, instr in enumerate(self.instrs):
                if not (0 <= i < len(self.ir2ast_stmt)):
                    continue
                ast_stmt = self.ir2ast_stmt[i]
                if ast_stmt is None:
                    continue

                dset: Set[VarAccess] = set()
                uset: Set[VarAccess] = set()

                if isinstance(ast_stmt, Assignment):
                    dset |= collect_var_accesses(ast_stmt.target)
                    uset |= collect_var_accesses(ast_stmt.value)
                elif isinstance(ast_stmt, CallStmt):
                    for arg in ast_stmt.args:
                        uset |= collect_var_accesses(arg)

                self.def_accesses[i] = dset
                self.use_accesses[i] = uset

    # ---------- 步骤 2：构造 GEN / KILL ----------

    def _compute_gen_kill(self):
        """
        基于 def_vars 和 var2defs 构造每条指令的 GEN / KILL 集合。
        GEN[i] = {(i, v) | v in DEF[i]}
        KILL[i] = {(j, v) | j != i 且 v in DEF[j]}
        """
        # 先初始化 GEN
        for i in range(self.n):
            for v in self.def_vars[i]:
                self.gen[i].add((i, v))

        # 再计算 KILL
        for v, def_indices in self.var2defs.items():
            # 这个变量 v 的所有定义语句集合
            for i in def_indices:
                # i 定义了 v，会杀掉其它对 v 的定义
                kill_set = set()
                for j in def_indices:
                    if j != i:
                        kill_set.add((j, v))
                self.kill[i].update(kill_set)

    # ---------- 步骤 3：求解 Reaching Definitions ----------

    def _solve_reaching_defs(self):
        """
        使用经典迭代算法，求出每条指令的 RD IN/OUT。
        """
        changed = True
        while changed:
            changed = False
            for i in range(self.n):
                # 1) IN[i] = ⋃ OUT[p] (p in pred[i])
                new_in: Set[DefSite] = set()
                for p in self.cfg.pred[i]:
                    new_in |= self.rd_out[p]

                # 2) OUT[i] = GEN[i] ∪ (IN[i] - KILL[i])
                new_out = self.gen[i] | (new_in - self.kill[i])

                if new_in != self.rd_in[i] or new_out != self.rd_out[i]:
                    self.rd_in[i] = new_in
                    self.rd_out[i] = new_out
                    changed = True

    # ---------- 步骤 4：构造 Def-Use 链 ----------

    def _build_def_use_chains(self) -> Tuple[Dict[DefSite, List[int]], Dict[UseSite, List[int]]]:
        """
        基于 RD IN 和 use_vars 构造：
          - def2uses: (def_index, var) -> [use_indices]
          - use2defs: (use_index, var) -> [def_indices]
        """
        def2uses: Dict[DefSite, List[int]] = {}
        use2defs: Dict[UseSite, List[int]] = {}

        for i in range(self.n):
            # 这条指令要使用的所有变量
            for v in self.use_vars[i]:
                # 所有能到达这里的对 v 的定义
                reaching_defs = [d for d in self.rd_in[i] if d[1] == v]
                def_indices = [d[0] for d in reaching_defs]

                # use -> defs
                use_key = (i, v)
                use2defs[use_key] = def_indices

                # defs -> use
                for d in reaching_defs:
                    def_key = d
                    def2uses.setdefault(def_key, []).append(i)

        return def2uses, use2defs
