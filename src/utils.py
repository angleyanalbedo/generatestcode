import re


def auto_repair(code_text: str) -> str:
    if not code_text: return ""
    md_match = r"```[a-zA-Z]*\n(.*?)```"
    match = re.search(md_match, code_text, flags=re.IGNORECASE | re.DOTALL)
    code = match.group(1).strip() if match else code_text.strip()

    # --- Step 2: 过滤完全不相关的垃圾 ---
    if re.search(r'^(variables|import|def\s|class\s|#\s)', code, re.I):
        return ""

    # --- Step 3: 适配 PROGRAM 包装 ---
    # 检查是否已经是完整的定义块
    has_header = re.match(r'^\s*(PROGRAM|FUNCTION_BLOCK|FUNCTION|CONFIGURATION)', code, re.IGNORECASE)

    if not has_header:
        # 如果代码里有 VAR_GLOBAL，说明它一定是一个 PROGRAM 或 CONFIGURATION 的片段
        # 我们统一包装成 PROGRAM，这在逻辑增强阶段是最安全的

        # 补齐必要的 VAR 段（如果代码里只有赋值语句，没写 VAR...END_VAR）
        if "VAR" not in code.upper():
            # 尝试分离全局变量和局部变量（可选，简单处理直接合在一起）
            code = "VAR\n    // 自动补全的变量段\nEND_VAR\n" + code

        # 包装成 PROGRAM
        code = f"PROGRAM Main_Logic\n{code}\nEND_PROGRAM"

    # 特殊处理：如果代码里有 VAR_GLOBAL 但没被包裹，强行在外层套 PROGRAM
    elif "VAR_GLOBAL" in code.upper() and not code.upper().strip().startswith("PROGRAM"):
        # 有些数据可能只写了 VAR_GLOBAL...END_VAR 然后接逻辑，这种也需要套 PROGRAM
        code = f"PROGRAM Global_Context\n{code}\nEND_PROGRAM"

    return code