import argparse
import os

from ..staugment.augment_dataset import DataAugmenter


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