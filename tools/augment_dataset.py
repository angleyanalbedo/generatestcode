import argparse
import json
import os
import random
import copy
from pathlib import Path
from tqdm import tqdm

from src.stparser.st_parser import STParser
from src.stparser.st_parser import STSemanticAnalyzer
from src.stparser.st_parser import STUnparser
from src.strewriter.st_rewriter import STRewriter


class DataAugmenter:
    def __init__(self, input_dir: str, output_dir: str, ext: str = ".json", num_variants: int = 2):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.ext = ext
        self.num_variants = num_variants

        # 初始化核心引擎
        self.parser = STParser()
        self.analyzer = STSemanticAnalyzer()
        self.rewriter = STRewriter(analyzer=self.analyzer, mode="augment")
        self.unparser = STUnparser()

        # 批处理统计
        self.stats = {
            "total_files": 0,
            "processed_files": 0,
            "total_original": 0,
            "total_augmented": 0,
            "parse_errors": 0
        }

    def process_single_file(self, file_path: Path) -> list:
        """处理单个 JSON 文件，返回包含了原数据和增强数据的混合列表"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                dataset = json.load(f)
        except Exception as e:
            print(f"\n⚠️ 警告: 文件读取失败 -> {file_path.name}: {e}")
            return []

        if not isinstance(dataset, list):
            return []

        augmented_dataset = []

        for item in dataset:
            self.stats["total_original"] += 1
            original_code = item.get("output", "")

            # 1. 始终保留原始的真金数据
            augmented_dataset.append(item)

            if not original_code:
                continue

            # 2. 尝试解析成 AST
            parse_res = self.parser.get_ast(original_code)
            if parse_res.get("status") != "success":
                self.stats["parse_errors"] += 1
                continue

            original_ast = parse_res["ast"]

            # 3. 循环生成 N 个变体
            for _ in range(self.num_variants):
                try:
                    # 深拷贝防止污染
                    ast_clone = copy.deepcopy(original_ast)

                    # 变异与反解析
                    mutated_ast = self.rewriter.rewrite(ast_clone)
                    new_code = self.unparser.unparse(mutated_ast)

                    # 确认代码发生了实际变化 (防重复)
                    if new_code.strip() and new_code.strip() != original_code.strip():
                        new_item = copy.deepcopy(item)
                        new_item["output"] = new_code
                        new_item["is_augmented"] = True  # 打上 AI 增强标记
                        augmented_dataset.append(new_item)
                        self.stats["total_augmented"] += 1
                except Exception:
                    # 单次增强失败不影响整体
                    pass

        return augmented_dataset

    def run(self):
        """执行批量增强流程"""
        files = list(self.input_dir.rglob(f"*{self.ext}"))
        self.stats["total_files"] = len(files)

        if not files:
            print(f"❌ 在 {self.input_dir} 中未找到任何 {self.ext} 文件！")
            return

        print(f"🚀 发现 {len(files)} 个文件，启动 AST 批量增强工厂 (裂变系数: x{self.num_variants})...")

        for file_path in tqdm(files, desc="Augmenting Datasets"):
            augmented_data = self.process_single_file(file_path)

            if not augmented_data:
                continue

            self.stats["processed_files"] += 1

            # 🚀 核心改动：创建与原 JSON 同名的文件夹
            # 比如输入是 data/golden_prompts.json，就会在输出目录创建 golden_prompts/ 文件夹
            file_out_dir = self.output_dir / file_path.stem
            file_out_dir.mkdir(parents=True, exist_ok=True)

            # 将增强后的数据存入该专属文件夹
            out_file = file_out_dir / "augmented_golden.json"
            with open(out_file, 'w', encoding='utf-8') as f:
                json.dump(augmented_data, f, ensure_ascii=False, indent=2)

        self.print_report()

    def print_report(self):
        """打印炫酷的流水线战报"""
        orig = self.stats["total_original"]
        aug = self.stats["total_augmented"]
        err = self.stats["parse_errors"]
        total = orig + aug

        print("\n" + "=" * 55)
        print("🧬 AST 数据集增强流水线战报")
        print("=" * 55)
        print(f"📂 扫描文件数: {self.stats['total_files']} (成功处理: {self.stats['processed_files']})")
        print("-" * 55)
        print(f"🌱 原始真金样本: {orig:6d} 条")
        print(f"🌿 AST 裂变样本: {aug:6d} 条 (变异成功！)")
        print(f"⚠️ 解析失败跳过: {err:6d} 条")
        print("-" * 55)
        print(f"📦 最终数据总量: {total:6d} 条")
        print(f"📁 结果已按原文件名分发至: {self.output_dir.absolute()}")
        print("=" * 55)


def parse_args():
    parser = argparse.ArgumentParser(description="ST代码数据集 AST 批量增强工厂")
    parser.add_argument("-i", "--input_dir", type=str, required=True,
                        help="包含原始 Golden JSON 数据集的输入文件夹路径")
    parser.add_argument("-o", "--output_dir", type=str, required=True,
                        help="增强后数据的输出根目录")
    parser.add_argument("-e", "--ext", type=str, default=".json",
                        help="要处理的文件扩展名 (默认: .json)")
    parser.add_argument("-n", "--num", type=int, default=2,
                        help="每条原始数据尝试生成的最大变体数量")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if not os.path.isdir(args.input_dir):
        print(f"❌ 错误: 输入目录 '{args.input_dir}' 不存在！")
        exit(1)

    augmenter = DataAugmenter(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        ext=args.ext,
        num_variants=args.num
    )
    augmenter.run()