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
        upper_code = code.upper()

        # 1. 核心关键字检查：至少得是个块
        if not any(k in upper_code for k in ["FUNCTION_BLOCK", "FUNCTION", "PROGRAM"]):
            return False, "Missing basic ST structure (no FB/FUN/PROG)"

        # 2. 结构闭合极速检查 (忽略注释里的干扰)
        clean_code = re.sub(r"//.*|(\(\*.*?\*\))", "", code, flags=re.DOTALL).upper()
        for start, end in self.pairs.items():
            start_count = len(re.findall(rf"\b{start}\b", clean_code))
            end_count = len(re.findall(rf"\b{end}\b", clean_code))
            # VAR 块有点特殊，VAR_INPUT 等也是以 END_VAR 结尾，所以 END_VAR 会多，这里简单跳过 VAR 的严格对齐
            if start != "VAR" and start_count != end_count:
                return False, f"Imbalance: {start}({start_count}) vs {end}({end_count})"

        # 3. 低级赋值错误拦截 (出现单个 = 且不在条件判断中)
        if re.search(r"(?<![:<>])=(?!=)", clean_code):
            return False, "Found '=' used for assignment instead of ':='"

        return True, "Passed fast check"
