import json
import os
from pathlib import Path
from tqdm import tqdm

from src.fbdunparser import FBDXmlUnparser
from src.xmlvalidtor import IEC61131Validator
from src.stparser.anltr4 import STParser

def test_st_to_fbd_pipeline(
        input_folder: str = "../resource/st_source_code",
        xsd_rel_path: str = "../resource/xsd/IEC61131_10_Ed1_0.xsd",
        output_rel_dir: str = "../data/fbd_output",):
    # 1. 初始化所有组件
    parser = STParser()
    unparser = FBDXmlUnparser()

    input_path = Path(input_folder)
    xsd_path = Path(xsd_rel_path)
    output_dir = Path(output_rel_dir)

    if not output_dir.exists():
        os.mkdir(output_dir)

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
            # ==========================================
            # 🌟 阶段 4: 保存成功的 XML 文件 (新增)
            # ==========================================
            try:
                # 提取原文件名 (例如 AIN1.ST -> AIN1) 并加上 .xml 后缀
                out_file_path = output_dir / f"{file_path.stem}.xml"
                # 写入文件，指定 utf-8 编码防止中文注释乱码
                out_file_path.write_text(xml_output, encoding="utf-8")
            except Exception as e:
                failure_details.append({
                    "file": file_path.name,
                    "stage": "File Save Error",
                    "error": f"写入本地文件失败: {str(e)}"
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

    # ==========================================
    # 🌟 修复谎言：真正保存日志文件！
    # ==========================================
    log_file_path = output_dir / "failure_details_log.json"
    try:
        with open(log_file_path, "w", encoding="utf-8") as log_file:
            # 将错误列表格式化保存为 JSON，方便阅读和后续分析
            json.dump(failure_details, log_file, indent=4, ensure_ascii=False)
        print(f"\n📂 [真·日志] 完整的 {len(failure_details)} 条错误记录已保存至: \n   👉 {log_file_path.absolute()}")
    except Exception as e:
        print(f"\n❌ 警告: 尝试保存日志文件时失败: {e}")
def debug_single_st(file_path: str):
    """
    单文件手术刀：深度打印 AST 结构，确认 body 到底去哪了
    """
    parser = STParser()
    unparser = FBDXmlUnparser()

    print(f"🔬 正在诊断文件: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()

    # 1. 解析 AST
    result = parser.get_ast(code)
    ast = result.get("ast") or result.get("data")

    if not ast:
        print("❌ AST 解析结果为空!")
        return

    # 2. 深度观察 POU 和 Body
    # 假设 ast 是一个列表（Start 节点返回多个 POU）
    pous = ast if isinstance(ast, list) else [ast]

    print(f"📦 发现 {len(pous)} 个 POU 节点:")
    for i, pou in enumerate(pous):
        name = pou.get("name", "Unnamed")
        u_type = pou.get("unit_type", "Unknown")
        body = pou.get("body", [])

        print(f"\n--- POU [{i}] : {name} ({u_type}) ---")
        print(f"  🔹 变量块数量: {len(pou.get('var_blocks', []))}")
        print(f"  🔹 Body 内容: {body}")

        if not body:
            print("  ⚠️ 警告: Body 是空的！这说明 Builder 没有进入语句块解析。")
        else:
            print(f"  ✅ Body 抓取成功，包含 {len(body)} 条顶级语句。")
            # 打印第一条语句的细节确认格式
            print(f"  📄 第一条语句样版: {str(body[0])[:100]}...")

    # 3. 尝试运行 Unparser 诊断
    try:
        print("\n⚡ 尝试执行 XML Unparse...")
        xml = unparser.unparse(ast)
        print("✅ XML 生成成功！内容片段:")
        print(xml[:200] + "...")
    except Exception as e:
        print(f"❌ Unparse 失败: {str(e)}")

def test_single_st():
    debug_single_st("../resource/st_source_code/ACOSH.ST")