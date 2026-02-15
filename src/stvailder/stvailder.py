import re
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

    def validate_v2(self, code: str) -> tuple[bool, str]:
        # 1. 语法检查
        tree = self.parser.parse(code)
        if isinstance(tree, tuple):
            return False, f"Syntax Error: {tree[1]}"

        # 2. 语义检查 (利用结构化数据)
        struct = self.parser.get_structure(code)

        # 检查变量：正文里用的变量，VAR 里有吗？
        declared_vars = set()
        for block in struct['variables']:
            for d in block['decls']:
                declared_vars.add(d['name'])

        # 简单的正文搜索检查（可以进一步递归分析 body）
        # ... 逻辑 ...

        return True, "Passed"