import re


def auto_repair(code_text: str) -> str:
    if not code_text: return ""
    md_match = r"```[a-zA-Z]*\n(.*?)```"
    match = re.search(md_match, code_text, flags=re.IGNORECASE | re.DOTALL)
    code = match.group(1).strip() if match else code_text.strip()

    # --- Step 2: 过滤完全不相关的垃圾 ---
    if re.search(r'^(variables|import|def\s|class\s|#\s)', code, re.I):
        return ""

    return code

def remove_st_comments(code: str) -> str:
    # 模式说明：
    # 1. 单引号字符串 '...'
    # 2. 双引号字符串 "..."
    # 3. 单行注释 //...
    # 4. 多行注释 (*...*)
    pattern = r"('[^']*'|\"[^\"]*\")|(//[^\r\n]*|\(\*.*?\*\))"

    def replacer(match):
        # 如果是 group(1) 命中了，说明是字符串，原样返回
        if match.group(1):
            return match.group(1)
        # 否则是 group(2) 命中了，说明是注释，替换为空
        return ""

    # 注意：这里继续使用 re.DOTALL 保证多行注释正常工作
    return re.sub(pattern, replacer, code, flags=re.DOTALL).upper()