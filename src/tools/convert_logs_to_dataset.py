import json
import argparse
from pathlib import Path


def convert_logs_to_dataset(input_path: str, output_path: str = None):
    input_file = Path(input_path)
    if output_path:
        output_file = Path(output_path)
    else:
        # 默认保存为原文件名 + _converted
        output_file = input_file.with_name(f"{input_file.stem}_converted.json")

    print(f"📖 正在读取日志文件: {input_file} ...")

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    except json.JSONDecodeError:
        print("❌ JSON 格式错误，请检查文件是否完整")
        return

    converted_data = []
    stats = {
        "total_entries": len(raw_data),
        "extracted_samples": 0,
        "skipped_empty": 0
    }

    for entry in raw_data:
        instruction = entry.get("instruction", "")

        # 遍历该条目下所有被拒绝的样本
        rejected_list = entry.get("rejected_samples", [])

        for sample in rejected_list:
            code = sample.get("code", "")
            error_msg = sample.get("error", "")

            # 过滤掉空代码
            if not code or not code.strip():
                stats["skipped_empty"] += 1
                continue

            # 构建标准格式
            new_item = {
                "instruction": instruction,
                "input": "",  # ST 通常不需要 input，留空
                "output": code,
                # 💡 额外保留原始报错信息，方便后续分析（清洗脚本通常会忽略多余字段）
                "original_error": error_msg
            }

            converted_data.append(new_item)
            stats["extracted_samples"] += 1

    # 保存文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(converted_data, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 40)
    print(f"✅ 转换完成！")
    print(f"原始日志条目: {stats['total_entries']}")
    print(f"提取样本数量: {stats['extracted_samples']}")
    print(f"跳过空代码数: {stats['skipped_empty']}")
    print(f"💾 输出文件: {output_file.absolute()}")
    print("=" * 40)
    print("\n👉 现在你可以把这个文件喂给 stdataclean 了！")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="将 failed_tasks 日志转换为标准数据集格式")
    parser.add_argument("input_file", help="输入的 JSON 日志文件路径")
    parser.add_argument("-o", "--output", help="输出文件路径 (可选)")

    args = parser.parse_args()
    convert_logs_to_dataset(args.input_file, args.output)