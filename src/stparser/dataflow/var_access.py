# dataflow/var_access.py
from dataclasses import dataclass, field
from typing import Tuple, Optional

@dataclass(frozen=True)
class VarAccess:
    base: str                         # 基础名字，比如 "axis", "gState"
    fields: Tuple[str, ...] = field(default_factory=tuple)
    indices: Tuple[str, ...] = field(default_factory=tuple)
    # indices 里可以先简单放 index 表达式的源码字符串，
    # 以后需要更精细时再换成 AST 或符号化结构。

    def pretty(self) -> str:
        s = self.base
        for idx in self.indices:
            s += f"[{idx}]"
        for fld in self.fields:
            s += f".{fld}"
        return s
