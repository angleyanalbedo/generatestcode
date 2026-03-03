import os
from pathlib import Path
from tqdm import tqdm

from src.fbdunparser.unparser import FBDXmlUnparser
from src.xmlvalidtor import IEC61131Validator
from src.stparser.anltr4 import STParser

def test_st_to_fbd_pipeline(
        input_folder: str = "../resource/st_source_code",
        xsd_rel_path: str = "../resource/xsd/IEC61131_10_Ed1_0.xsd"
):
    # 1. 初始化所有组件
    parser = STParser()
    unparser = FBDXmlUnparser()

    input_path = Path(input_folder)
    xsd_path = Path(xsd_rel_path)

    if not input_path.exists():
        print(f"❌ 错误: 源码文件夹 '{input_folder}' 不存在")
        return
    if not xsd_path.exists():
        print(f"❌ 错误: XSD 校验文件 '{xsd_path}' 不存在")
        return

    validator = IEC61131Validator(xsd_path)

    st_files = list(input_path.rglob("*.st"))
    total_files = len(st_files)

    if total_files == 0:
        print(f"❓ 警告: 在 '{input_folder}' 中没找到任何 .st 文件")
        return

    print(f"🔍 正在执行全链路测试: {total_files} 个 ST 源码文件...")

    # 统计数据
    stats = {
        "success": 0,
        "parse_fail": 0,
        "unparse_fail": 0,
        "xsd_fail": 0
    }
    failure_details = []

    # 2. 遍历测试
    for file_path in tqdm(st_files, desc="Processing Pipeline"):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()

            # --- 阶段 1: ST 解析为 AST ---
            parse_result = parser.get_ast(code)
            if parse_result.get("status") != "success":
                stats["parse_fail"] += 1
                failure_details.append({
                    "file": file_path.name,
                    "stage": "AST Parse",
                    "error": parse_result.get("message", "Unknown Parse Error")
                })
                continue

            # 假设 parser 成功时将 AST 存在 result["ast"] 或类似字段中
            ast_data = parse_result.get("ast") or parse_result.get("data")
            if not ast_data:
                stats["parse_fail"] += 1
                failure_details.append({"file": file_path.name, "stage": "AST Parse", "error": "AST data is empty"})
                continue

            # --- 阶段 2: AST 还原为 FBD XML ---
            xml_output = ""
            try:
                xml_output = unparser.unparse(ast_data)
                if not xml_output.strip():
                    raise ValueError("Unparser returned empty string (possibly unsupported syntax)")
            except Exception as e:
                stats["unparse_fail"] += 1
                failure_details.append({
                    "file": file_path.name,
                    "stage": "XML Unparse",
                    "error": str(e)
                })
                continue

            # --- 阶段 3: XSD 校验 ---
            is_valid, errors = validator.validate_string(xml_output)
            if not is_valid:
                stats["xsd_fail"] += 1
                failure_details.append({
                    "file": file_path.name,
                    "stage": "XSD Validate",
                    "error": " | ".join(errors[:3])  # 只记录前3个校验错误避免刷屏
                })
                continue

            # 如果走到这里，说明全链路成功！
            stats["success"] += 1

        except Exception as e:
            stats["parse_fail"] += 1
            failure_details.append({
                "file": file_path.name,
                "stage": "Runtime Crash",
                "error": str(e)
            })

    # --- 3. 打印最终战报 ---
    print("\n" + "=" * 60)
    print("📊 ST -> FBD XML 全链路合成数据测试战报")
    print("=" * 60)
    print(f"📁 测试目录: {input_path.absolute()}")
    print(f"📦 总文件数: {total_files}")
    print("-" * 60)
    print(f"✅ 完美通关 (生成合法 XML): {stats['success']} ({stats['success'] / total_files * 100:.1f}%)")
    print(f"❌ 阶段1 AST解析失败:    {stats['parse_fail']}")
    print(f"❌ 阶段2 XML生成失败:    {stats['unparse_fail']} (包含不支持的语法过滤)")
    print(f"❌ 阶段3 XSD校验失败:    {stats['xsd_fail']}")
    print("-" * 60)

    if failure_details:
        print("\n🚩 失败清单 (前 10 个):")
        for i, detail in enumerate(failure_details[:10]):
            print(f"{i + 1}. [{detail['file']}] @ {detail['stage']} -> {detail['error']}")

        if len(failure_details) > 10:
            print(f"... 以及另外 {len(failure_details) - 10} 个错误，请检查日志。")

    print("=" * 60)


