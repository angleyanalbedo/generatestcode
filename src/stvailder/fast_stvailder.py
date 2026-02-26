import re
from typing import Tuple


class FastValidator:
    """第一层漏斗：极速文本与结构校验，拦截低级错误，节省编译器 IO 开销"""

    def __init__(self):
        self.pairs = {
            "IF": "END_IF",
            "CASE": "END_CASE",
            "FOR": "END_FOR",
            "WHILE": "END_WHILE",
            "FUNCTION_BLOCK": "END_FUNCTION_BLOCK",
            "FUNCTION": "END_FUNCTION",
            "PROGRAM": "END_PROGRAM",
            "VAR": "END_VAR"
        }





    def validate(self, code: str) -> Tuple[bool, str]:
        if re.search(r"\b\w+\s*=\s*\w+;", code): return False, "Illegal assignment '='"
        required = ["FUNCTION_BLOCK", "END_FUNCTION_BLOCK", "VAR", "END_VAR"]
        if not all(k in code for k in required): return False, "Missing structure keywords"
        if "ARRAY[*]" in code.upper() or "ARRAY [*]" in code.upper(): return False, "Dynamic arrays not supported"
        return True, "Passed"
