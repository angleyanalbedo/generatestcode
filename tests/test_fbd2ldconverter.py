import os
from pathlib import Path
from tqdm import tqdm
import xml.etree.ElementTree as ET

from src.fbd2ldconverter import FbdToLdConverter
from src.xmlvalidtor import IEC61131Validator


# ⚠️ 记得根据你的项目路径导入这些类
# from converter import FbdToLdConverter
# from validator import IEC61131Validator

def test_fbd2ldconverter(
        input_folder: str = "../data/fbd_output",
        output_folder: str = "../data/ld_output",
        xsd_rel_path: str = "../resource/xsd/IEC61131_10_Ed1_0.xsd"  # 新增 XSD 路径
):
    """
    测试 FbdToLdConverter：批量读取 FBD XML -> 转换为 LD XML -> XSD 校验 -> 落地保存。
    """
    input_path = Path(input_folder)
    output_dir = Path(output_folder)
    xsd_path = Path(xsd_rel_path)

    # 1. 检查目录与 XSD 文件
    if not input_path.exists() or not input_path.is_dir():
        print(f"❌ 错误: 输入文件夹 '{input_folder}' 不存在。")
        return
    if not xsd_path.exists():
        print(f"❌ 错误: XSD 校验文件 '{xsd_path}' 不存在。")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    xml_files = list(input_path.rglob("*.xml"))
    total_files = len(xml_files)

    if total_files == 0:
        print(f"❓ 警告: 在 '{input_folder}' 中没有找到任何 .xml 文件。")
        return

    print(f"🔍 发现 {total_files} 个 FBD 文件，开始 LD 转换与 XSD 双重测试...")

    # 2. 初始化核心组件
    converter = FbdToLdConverter()
    validator = IEC61131Validator(xsd_path)

    # 3. 统计与错误追踪 (新增 xsd_fail)
    stats = {
        "success": 0,
        "read_fail": 0,
        "convert_fail": 0,
        "xsd_fail": 0,  # 👈 新增 XSD 失败统计
        "write_fail": 0
    }
    failure_details = []

    # 4. 执行批量处理
    for file_path in tqdm(xml_files, desc="Converting & Validating LD"):
        # [阶段 A] 读取文件
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                fbd_xml_content = f.read()
        except Exception as e:
            stats["read_fail"] += 1
            failure_details.append({"file": file_path.name, "stage": "Read", "error": str(e)})
            continue

        # [阶段 B] 执行 XML 图元转换
        try:
            ld_xml_output = converter.convert(fbd_xml_content)
            if not ld_xml_output or not ld_xml_output.strip():
                raise ValueError("转换器返回了空字符串。")
        except Exception as e:
            stats["convert_fail"] += 1
            failure_details.append({"file": file_path.name, "stage": "Convert", "error": str(e)})
            continue

        # [阶段 C] 🌟 严格 XSD 校验
        is_valid, errors = validator.validate_string(ld_xml_output)
        if not is_valid:
            stats["xsd_fail"] += 1
            failure_details.append({
                "file": file_path.name,
                "stage": "XSD Validate",
                # 强制转 str 避免 Runtime Crash，并且只取前 3 个错误防止刷屏
                "error": " | ".join([str(err) for err in errors[:3]])
            })
            continue  # 校验失败的“毒”文件，直接丢弃，不落地！

        # [阶段 D] 保存完全合法的文件
        try:
            out_file_path = output_dir / f"{file_path.stem}_LD.xml"
            out_file_path.write_text(ld_xml_output, encoding="utf-8")
            stats["success"] += 1
        except Exception as e:
            stats["write_fail"] += 1
            failure_details.append({"file": file_path.name, "stage": "Write", "error": str(e)})

    # 5. 打印最终大盘战报
    print("\n" + "=" * 60)
    print("📊 FBD -> LD 转换及 XSD 校验战报")
    print("=" * 60)
    print(f"📁 FBD 输入目录: {input_path.absolute()}")
    print(f"📁 LD 输出目录 : {output_dir.absolute()}")
    print(f"📦 参与测试文件数: {total_files}")
    print("-" * 60)

    success_rate = (stats['success'] / total_files) * 100 if total_files > 0 else 0
    print(f"✅ 完美通关 (生成合法 LD): {stats['success']} ({success_rate:.1f}%)")
    print(f"❌ 阶段A: 读取文件失败:    {stats['read_fail']}")
    print(f"❌ 阶段B: XML 转换失败:    {stats['convert_fail']}")
    print(f"❌ 阶段C: XSD 校验失败:    {stats['xsd_fail']}")
    print(f"❌ 阶段D: 写入文件失败:    {stats['write_fail']}")
    print("-" * 60)

    # 打印失败细节
    if failure_details:
        print("\n🚩 失败清单 (前 10 个):")
        for i, detail in enumerate(failure_details[:10]):
            print(f"{i + 1}. [{detail['file']}] @ {detail['stage']} -> {detail['error']}")

        if len(failure_details) > 10:
            print(f"... 以及另外 {len(failure_details) - 10} 个错误，请检查日志。")
    print("=" * 60)


if __name__ == "__main__":
    test_fbd2ldconverter()