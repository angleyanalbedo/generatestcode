import os
from pathlib import Path
from tqdm import tqdm

from src.ldunparser import LDXmlUnparser
from src.stparser import STParser
from src.xmlvalidtor import IEC61131Validator


def test_st_to_ld_pipeline(
        input_folder: str = "../resource/st_source_code",  # 你的 ST 源码目录
        xsd_rel_path: str = "../resource/xsd/IEC61131_10_Ed1_0.xsd",
        output_rel_dir: str = "../data/ld_direct_output"  # 直接生成的 LD 存放目录
):
    # 1. 初始化所有组件
    parser = STParser()
    ld_unparser = LDXmlUnparser()

    input_path = Path(input_folder)
    xsd_path = Path(xsd_rel_path)
    output_dir = Path(output_rel_dir)

    # 安全创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists() or not input_path.is_dir():
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

    print(f"🔍 正在执行直接生成 LD 全链路测试: {total_files} 个 ST 源码文件...")

    # 统计数据盘
    stats = {
        "success": 0,
        "parse_fail": 0,
        "unparse_fail": 0,
        "xsd_fail": 0,
        "io_fail": 0
    }
    failure_details = []

    for file_path in tqdm(st_files, desc="ST -> LD Pipeline"):
        try:
            # --- 阶段 0: 读取源码 ---
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

            ast_data = parse_result.get("ast") or parse_result.get("data")
            if not ast_data:
                stats["parse_fail"] += 1
                failure_details.append({"file": file_path.name, "stage": "AST Parse", "error": "AST data is empty"})
                continue

            # --- 阶段 2: AST 直接还原为 LD XML ---
            ld_xml_output = ""
            try:
                # 🌟 核心：召唤你刚写的 LDXmlUnparser
                ld_xml_output = ld_unparser.unparse(ast_data)
                if not ld_xml_output or not ld_xml_output.strip():
                    raise ValueError("LD Unparser 返回了空字符串 (可能是遇到了不支持的语句，如 IF/FOR)")
            except Exception as e:
                stats["unparse_fail"] += 1
                failure_details.append({
                    "file": file_path.name,
                    "stage": "LD Unparse",
                    "error": str(e)
                })
                continue

            # --- 阶段 3: XSD 严格校验 ---
            is_valid, errors = validator.validate_string(ld_xml_output)
            if not is_valid:
                stats["xsd_fail"] += 1
                failure_details.append({
                    "file": file_path.name,
                    "stage": "XSD Validate",
                    # 防崩溃：强制转 str
                    "error": " | ".join([str(err) for err in errors[:3]])
                })
                continue

            # --- 阶段 4: 落地保存纯净合规的 LD XML ---
            try:
                out_file_path = output_dir / f"{file_path.stem}_Direct_LD.xml"
                out_file_path.write_text(ld_xml_output, encoding="utf-8")
                stats["success"] += 1
            except Exception as e:
                stats["io_fail"] += 1
                failure_details.append({"file": file_path.name, "stage": "File Save", "error": str(e)})

        except Exception as e:
            stats["parse_fail"] += 1
            failure_details.append({
                "file": file_path.name,
                "stage": "Runtime Crash",
                "error": str(e)
            })

    # --- 🖨️ 打印最终大盘战报 ---
    print("\n" + "=" * 60)
    print("📊 ST -> AST -> LD 直接渲染测试战报")
    print("=" * 60)
    print(f"📁 源码输入: {input_path.absolute()}")
    print(f"📁 梯形图输出: {output_dir.absolute()}")
    print(f"📦 测试总数: {total_files}")
    print("-" * 60)

    success_rate = (stats['success'] / total_files) * 100 if total_files > 0 else 0
    print(f"✅ 完美通关 (生成合法 LD): {stats['success']} ({success_rate:.1f}%)")
    print(f"❌ 阶段1 AST解析失败:    {stats['parse_fail']}")
    print(f"❌ 阶段2 LD渲染失败:     {stats['unparse_fail']} (包含未实现的图形节点跳过)")
    print(f"❌ 阶段3 XSD校验失败:    {stats['xsd_fail']}")
    print(f"❌ 阶段4 文件保存失败:   {stats['io_fail']}")
    print("-" * 60)

    if failure_details:
        print("\n🚩 失败清单 (前 10 个):")
        for i, detail in enumerate(failure_details[:10]):
            print(f"{i + 1}. [{detail['file']}] @ {detail['stage']} -> {detail['error']}")

        if len(failure_details) > 10:
            print(f"... 以及另外 {len(failure_details) - 10} 个错误，请检查日志。")

    print("=" * 60)


if __name__ == "__main__":
    test_st_to_ld_pipeline()