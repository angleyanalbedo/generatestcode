import argparse
import json
import random
import copy
from pathlib import Path
from tqdm import tqdm

from src.stparser.st_parser import STParser
from src.stparser.st_parser import STSemanticAnalyzer
from src.stparser.st_parser import STUnparser
from src.strewriter.st_rewriter import STRewriter


class DataAugmenter:
    def __init__(self):
        self.parser = STParser()
        self.analyzer = STSemanticAnalyzer()
        self.rewriter = STRewriter(analyzer=self.analyzer)
        self.unparser = STUnparser()

    def run(self, input_file: str, output_file: str, variants_per_sample: int = 2):
        print(f"📦 正在加载 SFT 数据集: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            dataset = json.load(f)

        augmented_dataset = []
        success_count = 0
        error_count = 0

        print(f"🚀 开始进行 AST 级数据增强 (每条衍生 {variants_per_sample} 个变体)...")

        for item in tqdm(dataset, desc="Augmenting"):
            original_code = item.get("output", "")
            if not original_code:
                continue

            # 1. 原数据无条件保留
            augmented_dataset.append(item)

            # 2. 尝试解析成 AST
            parse_res = self.parser.get_ast(original_code)
            if parse_res["status"] != "success":
                error_count += 1
                continue

            original_ast = parse_res["ast"]

            # 3. 生成 N 个变体
            for _ in range(variants_per_sample):
                try:
                    # ⚠️ 必须深拷贝，否则会污染原 AST
                    ast_clone = copy.deepcopy(original_ast)

                    # AST 变异
                    mutated_ast = self.rewriter.rewrite(ast_clone)

                    # 反解析为 ST 代码
                    new_code = self.unparser.unparse(mutated_ast)

                    # 如果重排后代码有变化，存入新数据集
                    if new_code.strip() != original_code.strip():
                        new_item = copy.deepcopy(item)
                        new_item["output"] = new_code
                        new_item["is_augmented"] = True  # 打上增强标记
                        augmented_dataset.append(new_item)
                        success_count += 1
                except Exception as e:
                    # 容错处理：即使某个变体生成失败，也不影响整个流水线
                    pass

        # 落盘
        out_path = Path(output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(augmented_dataset, f, ensure_ascii=False, indent=2)

        print("\n" + "=" * 50)
        print("🎉 数据增强完成！")
        print("=" * 50)
        print(f"原始数据量: {len(dataset)}")
        print(f"成功增强量: {success_count} (解析失败跳过: {error_count})")
        print(f"最终数据量: {len(augmented_dataset)}")
        print(f"💾 已保存至: {out_path.absolute()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ST代码数据集 AST 增强工厂")
    parser.add_argument("-i", "--input", required=True, help="输入的 Golden JSON 数据集")
    parser.add_argument("-o", "--output", required=True, help="输出的增强后 JSON 数据集")
    parser.add_argument("-n", "--num", type=int, default=2, help="每条原始数据生成的变体数量")
    args = parser.parse_args()

    augmenter = DataAugmenter()
    augmenter.run(args.input, args.output, args.num)