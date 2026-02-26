from src.stparser import STParser
from src.stparser import STUnparser


# from src.stparser.st_unparser import STUnparser # 你的老版 unparser

def test_new_engine():
    code = """
    PROGRAM Main
    VAR
        A : INT := 10;
        B : INT;
    END_VAR
    IF A > 5 THEN
        B := A + 1;
    END_IF;
    END_PROGRAM
    """

    # 1. 用新引擎解析
    parser = STParser()
    result = parser.get_ast(code)

    if result["status"] == "success":
        print("✅ AST 解析成功！生成的字典如下：")
        import json
        print(json.dumps(result["ast"], indent=2, ensure_ascii=False))

        # 2. 用老引擎还原 (如果你已经导入了 STUnparser)
        unparser = STUnparser()
        new_code = unparser.unparse(result["ast"])
        print("\n✅ 代码还原成功：\n", new_code)
    else:
        print("❌ 解析失败：", result["message"])


if __name__ == "__main__":
    test_new_engine()