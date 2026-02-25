import argparse
import json
import os
from pathlib import Path
from typing import Tuple, List, Dict

from tqdm import tqdm

from src.stvailder import STValidator


class STDataCleaner:
    def __init__(self, input_dir: str, output_dir: str,mode: bool, ext: str = ".json"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.ext = ext
        self.strict_mode = mode
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

    def auto_repair(self, code: str) -> str:
        """尝试自动修复和提取纯净的 ST 代码，防止因为多余的字符导致 AST 解析失败"""
        if not code:
            return ""

        # 1. 剥离 Markdown 包装 (很多数据集带有 ```st ... ```)
        import re
        # 提取 ``` 之间的内容
        md_match = re.search(r"```[a-zA-Z]*\n(.*?)```", code, re.DOTALL | re.IGNORECASE)
        if md_match:
            code = md_match.group(1)

        # 2. 尝试过滤掉开头的自然语言废话 (比如 "Here is the code:\n")
        # 找到第一个关键字的位置
        keywords = ["FUNCTION_BLOCK", "FUNCTION", "PROGRAM", "VAR", "TYPE"]
        first_idx = len(code)
        for kw in keywords:
            idx = code.upper().find(kw)
            if idx != -1 and idx < first_idx:
                first_idx = idx

        if first_idx != len(code) and first_idx > 0:
            code = code[first_idx:]

        return code.strip()

    def process_single_file(self, file_path: Path, strict_mode: bool = False) -> Tuple[List[Dict], List[Dict]]:
        """处理单个 JSON 文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        valid_data, invalid_data = [], []

        for item in data:
            self.stats["total_samples"] += 1
            original_code = item.get("output", "")

            # 🚀 第一步：自动抢救代码格式
            repaired_code = self.auto_repair(original_code)

            # 如果修复后代码有变化，更新回 item
            if repaired_code != original_code:
                item["output"] = repaired_code
                item["was_repaired"] = True

            # 🚀 第二步：级联校验并打标
            status = "golden"
            error_reason = None

            if not repaired_code:
                status = "empty"
                error_reason = "No code found after repair"
            else:
                # 校验阶段 1: 静态正则校验
                is_valid_s1, msg1 = self.validator.validate(repaired_code)
                if not is_valid_s1:
                    status = "syntax_error"
                    error_reason = msg1
                else:
                    # 校验阶段 2: AST 语义校验
                    is_valid_s2, msg2 = self.validator.validate_v2(repaired_code)
                    if not is_valid_s2:
                        status = "ast_error"
                        error_reason = msg2

            # 🚀 第三步：根据模式决定去留
            # 记录元数据
            item["st_metadata"] = {
                "quality": status,
                "error": error_reason
            }

            if strict_mode:
                # 严格模式：稍微有错就扔进 invalid
                if status == "golden":
                    valid_data.append(item)
                else:
                    invalid_data.append(item)
            else:
                # 软模式：全部放进 valid，由后续管线根据 quality 标签自行决定怎么用
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
            valid_list, invalid_list = self.process_single_file(file_path,self.strict_mode)

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
    parser.add_argument("--strict", action="store_true",
                        help="开启严格模式：丢弃所有未通过校验的数据。不加此参数则为软打标模式。")
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
        ext=args.ext,
        mode=args.strict
    )
    cleaner.run()