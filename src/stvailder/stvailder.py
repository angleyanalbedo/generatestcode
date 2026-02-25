import re
from typing import Tuple

from src.stparser.st_parser import STParser

# --- 校验器 ---

class STValidator:
    """
    严谨版 ST 校验器：支持变量对齐、嵌套闭合及语法规范检查。
    语法树检查应该在事后清洗
    """

    def __init__(self):
        # 定义成对出现的关键字
        self.pair_keywords = {
            "IF": "END_IF",
            "CASE": "END_CASE",
            "FOR": "END_FOR",
            "WHILE": "END_WHILE",
            "REPEAT": "UNTIL",
            "FUNCTION_BLOCK": "END_FUNCTION_BLOCK",
            "VAR": "END_VAR",
            "VAR_INPUT": "END_VAR",
            "VAR_OUTPUT": "END_VAR"
        }
        self.parser = STParser()

    def _extract_declared_vars(self, code):
        """提取 VAR 块中定义的所有变量名"""
        # 匹配 VAR...END_VAR 之间的内容
        var_blocks = re.findall(r"(?i)VAR.*?END_VAR", code, re.DOTALL)
        declared_vars = set()
        for block in var_blocks:
            # 匹配变量定义行，如: Motor_Start : BOOL;
            lines = re.findall(r"(\w+)\s*:\s*\w+", block)
            declared_vars.update(lines)
        return declared_vars

    def _check_nesting(self, code):
        """校验结构是否完全闭合"""
        upper_code = code.upper()
        for start, end in self.pair_keywords.items():
            start_count = len(re.findall(rf"\b{start}\b", upper_code))
            end_count = len(re.findall(rf"\b{end}\b", upper_code))
            if start_count != end_count:
                return False, f"Structural imbalance: {start}({start_count}) vs {end}({end_count})"
        return True, "Success"

    def validate(self, code):
        # 1. 基础语法：禁止使用 = 进行赋值 (ST 必须使用 :=)
        # 排除掉注释后的内容进行检查
        clean_code = re.sub(r"//.*|(\(\*.*?\*\))", "", code, flags=re.DOTALL)

        if re.search(r"(?<![:<>])=(?!=)", clean_code):
            return False, "Assignment Error: Found '=' instead of ':=' for assignment."

        # 2. 结构闭合检查
        is_closed, nest_msg = self._check_nesting(clean_code)
        if not is_closed:
            return False, nest_msg

        # 3. 核心关键字检查
        required = ["FUNCTION_BLOCK", "VAR", "END_VAR", "END_FUNCTION_BLOCK"]
        if not all(k in clean_code.upper() for k in required):
            return False, "Standard Structure Error: Missing FB or VAR declarations."

        # 4. 变量存在性检查 (可选，但建议开启)
        # 这一步可以防止模型幻觉出未定义的变量
        declared = self._extract_declared_vars(clean_code)
        # 简单逻辑：如果正文中有 'Variable :=' 但 'Variable' 没被定义
        # 这里仅作演示，实际实现需排除关键字

        # 5. 浮点数直接比较检查
        if re.search(r"==|(?<![:<>])=(?!=)", clean_code) and "REAL" in clean_code.upper():
            # 这里可以细化，提醒模型使用 ABS(a-b) < epsilon
            pass

        return True, "Passed All Strict Checks"

    def _extract_used_vars(self, body_element) -> set:
        """递归提取语句中使用的所有变量名"""
        used = set()
        if isinstance(body_element, list):
            for item in body_element:
                used.update(self._extract_used_vars(item))
        elif isinstance(body_element, dict):
            # 如果是赋值语句，target 和 expr 里的变量都要抓
            if body_element.get("type") == "assignment":
                used.add(body_element["target"])
                # 这里简单处理，实际 expr 可能是复杂的树，需进一步递归
                if isinstance(body_element["expr"], str):
                    used.add(body_element["expr"])
            # 如果是 IF/CASE 等结构，递归其 body 部分
            if "body" in body_element:
                used.update(self._extract_used_vars(body_element["body"]))
        return used

    def validate_v2(self, code: str) -> tuple[bool, str]:
        # 1. 语法校验 (Syntax Check)
        # 如果 Lark 报错，直接打回
        tree = self.parser.parse(code)
        if isinstance(tree, tuple):  # 假设 parse 返回 (None, err_msg)
            return False, f"Syntax Error: {tree[1]}"

        # 2. 获取结构化数据 (Semantic Analysis)
        try:
            struct = self.parser.get_ast(code)
        except Exception as e:
            return False, f"Analysis Error: {str(e)}"

        # 3. 语义校验：变量对齐
        # A. 收集所有声明的变量
        declared_vars = set()
        for block in struct.get('var_blocks', []):
            for v in block['vars']:
                declared_vars.add(v['name'])

        # B. 递归收集正文中使用的标识符
        used_vars = self._extract_used_vars(struct.get('body', []))

        # C. 过滤掉系统关键字和常量数字
        # 简单逻辑：如果标识符全是数字，忽略
        used_vars = {v for v in used_vars if not v.isdigit()}

        # D. 求差集：找出未定义的变量
        undefined = used_vars - declared_vars

        if undefined:
            return False, f"Semantic Error: Undefined variables used: {', '.join(undefined)}"

        return True, "Passed"


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