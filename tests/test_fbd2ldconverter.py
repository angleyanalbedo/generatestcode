import os
from pathlib import Path
from tqdm import tqdm


# 假设 FbdToLdConverter 和 IEC61131Validator 已经导入
# from your_module import FbdToLdConverter, IEC61131Validator

def test_fbd_to_ld_pipeline(
        input_folder: str = "../data/fbd_output",  # 上一步全链路生成的 FBD XML 目录
        xsd_rel_path: str = "../resource/xsd/IEC61131_10_Ed1_0.xsd",
        output_rel_dir: str = "../data/ld_output"  # 专门用于存放梯形图的目录
):
    # 1. 初始化组件
    converter = FbdToLdConverter()

    input_path = Path(input_folder)
    xsd_path = Path(xsd_rel_path)
    output_dir = Path(output_rel_dir)

    # 🛡️ 优化：使用 parents=True, exist_ok=True 避免目录层级缺失报错
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        print(f"❌ 错误: FBD 源码文件夹 '{input_folder}' 不存在")
        return
    if not xsd_path.exists():
        print(f"❌ 错误: XSD 校验文件 '{xsd_path}' 不存在")
        return

    validator = IEC61131Validator(xsd_path)

    # 寻找所有的 XML 文件
    fbd_files = list(input_path.rglob("*.xml"))
    total_files = len(fbd_files)

    if total_files == 0:
        print(f"❓ 警告: 在 '{input_folder}' 中没找到任何 .xml 文件")
        return

    print(f"🔍 正在执行 FBD -> LD 转换测试: {total_files} 个 XML 文件...")

    # 📊 完美继承：统计大盘
    stats = {
        "success": 0,
        "convert_fail": 0,
        "xsd_fail": 0,
        "io_fail": 0
    }
    failure_details = []

    for file_path in tqdm(fbd_files, desc="Converting to LD"):
        try:
            # --- 阶段 1: 读取 FBD XML ---
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    fbd_xml_content = f.read()
            except Exception as e:
                stats["io_fail"] += 1
                failure_details.append({"file": file_path.name, "stage": "File Read", "error": str(e)})
                continue

            # --- 阶段 2: 执行 FBD -> LD 转换 ---
            ld_xml_output = ""
            try:
                ld_xml_output = converter.convert(fbd_xml_content)
                if not ld_xml_output.strip():
                    raise ValueError("Converter returned empty string")
            except Exception as e:
                stats["convert_fail"] += 1
                failure_details.append({
                    "file": file_path.name,
                    "stage": "XML Convert",
                    "error": str(e)
                })
                continue

            # --- 阶段 3: XSD 校验 (校验 LD 语法的合法性) ---
            is_valid, errors = validator.validate_string(ld_xml_output)
            if not is_valid:
                stats["xsd_fail"] += 1
                failure_details.append({
                    "file": file_path.name,
                    "stage": "XSD Validate",
                    # 🛡️ 重点防雷：强制转 str，杜绝 expected str instance 崩溃
                    "error": " | ".join([str(err) for err in errors[:3]])
                })
                # 即使校验失败也可以选择保存下来看原因（把下面两行注释掉即可落盘）
                continue

            # --- 阶段 4: 保存成功的 LD XML 文件 ---
            try:
                out_file_path = output_dir / f"{file_path.stem}_LD.xml"
                out_file_path.write_text(ld_xml_output, encoding="utf-8")
            except Exception as e:
                stats["io_fail"] += 1
                failure_details.append({
                    "file": file_path.name,
                    "stage": "File Save",
                    "error": f"写入本地文件失败: {str(e)}"
                })
                continue

            # 如果走到这里，说明全链路成功！
            stats["success"] += 1

        except Exception as e:
            stats["convert_fail"] += 1
            failure_details.append({
                "file": file_path.name,
                "stage": "Runtime Crash",
                "error": str(e)
            })

    # --- 🖨️ 打印最终战报 ---
    print("\n" + "=" * 60)
    print("📊 FBD XML -> LD XML 批量转换测试战报")
    print("=" * 60)
    print(f"📁 输入目录: {input_path.absolute()}")
    print(f"📁 输出目录: {output_dir.absolute()}")
    print(f"📦 总文件数: {total_files}")
    print("-" * 60)
    print(f"✅ 完美通关 (生成合法 LD): {stats['success']} ({stats['success'] / total_files * 100:.1f}%)")
    print(f"❌ 阶段1/4 文件读写失败:   {stats['io_fail']}")
    print(f"❌ 阶段2 XML转换失败:      {stats['convert_fail']}")
    print(f"❌ 阶段3 XSD校验失败:      {stats['xsd_fail']}")
    print("-" * 60)

    if failure_details:
        print("\n🚩 失败清单 (前 10 个):")
        for i, detail in enumerate(failure_details[:10]):
            print(f"{i + 1}. [{detail['file']}] @ {detail['stage']} -> {detail['error']}")

        if len(failure_details) > 10:
            print(f"... 以及另外 {len(failure_details) - 10} 个错误，请检查日志。")

    print("=" * 60)

