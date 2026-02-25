import re


def auto_repair(code: str) -> str:
    if not code: return ""
    md_match = re.search(r"```[a-zA-Z]*\n(.*?)```", code, re.DOTALL | re.IGNORECASE)
    if md_match: code = md_match.group(1)
    keywords = ["FUNCTION_BLOCK", "FUNCTION", "PROGRAM", "VAR", "TYPE"]
    first_idx = len(code)
    for kw in keywords:
        idx = code.upper().find(kw)
        if idx != -1 and idx < first_idx: first_idx = idx
    if first_idx != len(code) and first_idx > 0: code = code[first_idx:]
    return code.strip()