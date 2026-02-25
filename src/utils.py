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