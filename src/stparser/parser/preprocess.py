import re

def preprocess_st(code: str) -> str:
    code = code.replace("&lt;", "<").replace("&gt;", ">")

    # 删除 or 替换 (* ... *) 注释
    code = re.sub(r"\(\*.*?\*\)", " ", code, flags=re.S)

    # 自动修复空输出参数
    code = re.sub(r'=>\s*,', '=> __dummy__,', code)
    code = re.sub(r'=>\s*\)', '=> __dummy__ )', code)

    return code
