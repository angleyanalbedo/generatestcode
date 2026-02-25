import argparse
import json
import os
from pathlib import Path
from typing import Tuple, List, Dict

from tqdm import tqdm

from src.stvailder import STValidator


class STDataCleaner:
    def __init__(self, input_dir: str, output_dir: str, ext: str = ".json"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.ext = ext
        self.validator = STValidator()

        # 准备输出目录结构
        self.valid_dir = self.output_dir / "valid"
        self.invalid_dir = self.output_dir / "invalid"
        self.valid_dir.mkdir(parents=True, exist_ok=True)
        self.invalid_dir.mkdir(parents=True, exist_ok=True)

        # 统计数据
        self.stats = {
            "total_files": 0,
            "processed_files": 0,
            "total_samples": 0,
            "valid_samples": 0,
            "invalid_samples": 0
        }

    def process_single_file(self, file_path: Path) -> Tuple[List[Dict], List[Dict]]:
        """处理单个 JSON 文件，返回 (合格列表, 淘汰列表)"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print(f"\n⚠️ 警告: 文件解析失败，跳过 -> {file_path.name}")
            return [], []

        if not isinstance(data, list):
            print(f"\n⚠️ 警告: 数据格式非数组，跳过 -> {file_path.name}")
            return [], []

        valid_data, invalid_data = [], []

        for item in data:
            self.stats["total_samples"] += 1
            # 假设你的目标代码在 "output" 字段，兼容可能在其他字段的情况
            code = item.get("output", "")
            if not code:
                item["error_reason"] = "Missing or empty 'output' field"
                invalid_data.append(item)
                continue

            # 阶段 1：静态正则校验
            is_valid, msg = self.validator.validate(code)
            if not is_valid:
                item["error_reason"] = f"Regex_Check_Failed: {msg}"
                invalid_data.append(item)
                continue

            # 阶段 2：AST 语义校验
            is_valid, msg = self.validator.validate_v2(code)
            if not is_valid:
                item["error_reason"] = f"AST_Check_Failed: {msg}"
                invalid_data.append(item)
                continue

            # 全部通过
            valid_data.append(item)

        self.stats["valid_samples"] += len(valid_data)
        self.stats["invalid_samples"] += len(invalid_data)
        return valid_data, invalid_data

    def run(self):
        """执行批量清洗流程"""
        # 查找所有匹配的文件
        files = list(self.input_dir.rglob(f"*{self.ext}"))
        self.stats["total_files"] = len(files)

        if not files:
            print(f"❌ 在 {self.input_dir} 中未找到任何 {self.ext} 文件！")
            return

        print(f"🚀 发现 {len(files)} 个文件，开始批量清洗...")

        # 带进度条遍历文件
        for file_path in tqdm(files, desc="Processing Files"):
            valid_list, invalid_list = self.process_single_file(file_path)

            # 只有处理成功才算一个有效文件
            if valid_list or invalid_list:
                self.stats["processed_files"] += 1

                # 分别落盘保存 (保持原文件名)
                if valid_list:
                    out_valid = self.valid_dir / file_path.name
                    with open(out_valid, 'w', encoding='utf-8') as f:
                        json.dump(valid_list, f, ensure_ascii=False, indent=2)

                if invalid_list:
                    out_invalid = self.invalid_dir / f"rejected_{file_path.name}"
                    with open(out_invalid, 'w', encoding='utf-8') as f:
                        json.dump(invalid_list, f, ensure_ascii=False, indent=2)

        self.print_report()

    def print_report(self):
        """打印最终统计报告"""
        total = self.stats["total_samples"]
        valid = self.stats["valid_samples"]
        invalid = self.stats["invalid_samples"]
        pass_rate = (valid / total * 100) if total > 0 else 0

        print("\n" + "=" * 50)
        print("📊 ST 数据集批量清洗报告")
        print("=" * 50)
        print(f"📂 扫描文件数: {self.stats['total_files']} (成功处理: {self.stats['processed_files']})")
        print(f"📦 总样本数:   {total}")
        print(f"✅ 合格样本:   {valid} ({pass_rate:.2f}%)")
        print(f"❌ 淘汰样本:   {invalid} ({(100 - pass_rate):.2f}%)")
        print("-" * 50)
        print(f"📁 黄金数据存放至: {self.valid_dir.absolute()}")
        print(f"📁 垃圾数据存放至: {self.invalid_dir.absolute()}")
        print("=" * 50)


def parse_args():
    parser = argparse.ArgumentParser(description="ST代码数据集批量清洗工具 (ST Validator CLI)")
    parser.add_argument("-i", "--input_dir", type=str, required=True,
                        help="包含原始 JSON 数据集的输入文件夹路径")
    parser.add_argument("-o", "--output_dir", type=str, required=True,
                        help="清洗后数据的输出根目录")
    parser.add_argument("-e", "--ext", type=str, default=".json",
                        help="要处理的文件扩展名 (默认: .json)")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # 检查输入目录是否存在
    if not os.path.isdir(args.input_dir):
        print(f"❌ 错误: 输入目录 '{args.input_dir}' 不存在！")
        exit(1)

    cleaner = STDataCleaner(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        ext=args.ext
    )
    cleaner.run()