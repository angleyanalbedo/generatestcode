import os
from pathlib import Path
from tqdm import tqdm
import xml.etree.ElementTree as ET

from src.fbd2ldconverter import FbdToLdConverter


# 假设你已经将 FbdToLdConverter 放在了同目录的 converter.py 中，如果没有，请将类代码粘贴到这里
# from converter import FbdToLdConverter

def test_fbd2ldconverter(
        input_folder: str = "../data/fbd_output",
        output_folder: str = "../data/ld_output"
):
    """
    测试 FbdToLdConverter：批量读取文件夹中的 FBD XML，转换为 LD XML 并保存。
    """
    input_path = Path(input_folder)
    output_dir = Path(output_folder)

    # 1. 检查输入目录
    if not input_path.exists() or not input_path.is_dir():
        print(f"❌ 错误: 输入文件夹 '{input_folder}' 不存在或不是一个目录。")
        return

    # 2. 安全创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)

    # 3. 收集所有的 XML 文件
    xml_files = list(input_path.rglob("*.xml"))
    total_files = len(xml_files)

    if total_files == 0:
        print(f"❓ 警告: 在 '{input_folder}' 中没有找到任何 .xml 文件。")
        return

    print(f"🔍 发现 {total_files} 个 XML 文件，开始 FBD -> LD 批量转换测试...")

    # 初始化转换器
    converter = FbdToLdConverter()

    # 4. 统计与错误追踪
    stats = {
        "success": 0,
        "read_fail": 0,
        "convert_fail": 0,
        "write_fail": 0
    }
    failure_details = []

    # 5. 执行批量处理
    for file_path in tqdm(xml_files, desc="Converting FBD to LD"):
        # [阶段 A] 读取文件
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                fbd_xml_content = f.read()
        except Exception as e:
            stats["read_fail"] += 1
            failure_details.append({"file": file_path.name, "stage": "Read", "error": str(e)})
            continue

        # [阶段 B] 执行转换
        try:
            ld_xml_output = converter.convert(fbd_xml_content)
            if not ld_xml_output or not ld_xml_output.strip():
                raise ValueError("转换器返回了空字符串。")
        except Exception as e:
            stats["convert_fail"] += 1
            failure_details.append({"file": file_path.name, "stage": "Convert", "error": str(e)})
            continue

        # [阶段 C] 保存文件
        try:
            # 自动在文件名后加 _LD，例如：AIN1.xml -> AIN1_LD.xml
            out_file_path = output_dir / f"{file_path.stem}_LD.xml"
            out_file_path.write_text(ld_xml_output, encoding="utf-8")
            stats["success"] += 1
        except Exception as e:
            stats["write_fail"] += 1
            failure_details.append({"file": file_path.name, "stage": "Write", "error": str(e)})

    # 6. 打印测试战报
    print("\n" + "=" * 60)
    print("📊 FBD -> LD 转换器批量测试战报")
    print("=" * 60)
    print(f"📁 输入目录: {input_path.absolute()}")
    print(f"📁 输出目录: {output_dir.absolute()}")
    print(f"📦 参与测试文件数: {total_files}")
    print("-" * 60)

    success_rate = (stats['success'] / total_files) * 100 if total_files > 0 else 0
    print(f"✅ 转换成功并保存: {stats['success']} ({success_rate:.1f}%)")
    print(f"❌ 读取文件失败:   {stats['read_fail']}")
    print(f"❌ XML 转换失败:   {stats['convert_fail']}")
    print(f"❌ 写入文件失败:   {stats['write_fail']}")
    print("-" * 60)

    # 打印前 10 个失败细节
    if failure_details:
        print("\n🚩 失败清单 (前 10 个):")
        for i, detail in enumerate(failure_details[:10]):
            print(f"{i + 1}. [{detail['file']}] @ {detail['stage']} -> {detail['error']}")

        if len(failure_details) > 10:
            print(f"... 以及另外 {len(failure_details) - 10} 个错误，请检查输出日志。")
    print("=" * 60)


if __name__ == "__main__":
    # 你可以在这里修改为你实际的 FBD XML 存放路径和想要输出梯形图的路径
    test_fbd2ldconverter(
        input_folder="../data/fbd_output",
        output_folder="../data/ld_output"
    )