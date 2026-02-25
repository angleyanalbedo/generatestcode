import argparse

import os

from src.stdatacleaner.stcleaner import STDataCleaner


def parse_args():
    parser = argparse.ArgumentParser(description="ST代码数据集清洗与分类工具")
    parser.add_argument("-i", "--input_dir", type=str, required=True,
                        help="包含原始 JSON 数据集的输入文件夹路径")
    parser.add_argument("-o", "--output_dir", type=str, required=True,
                        help="清洗后数据的输出根目录")
    parser.add_argument("-e", "--ext", type=str, default=".json",
                        help="要处理的文件扩展名 (默认: .json)")
    parser.add_argument("--iec2c", type=str, default="resource/MatIEC/iec2c", help="iec2c 编译器的绝对路径 (默认: iec2c)")
    parser.add_argument("-I", "--st_lib", type=str, default="resource/MatIEC/lib", help="Matiec 标准库 lib 文件夹的路径")
    parser.add_argument("-s","--strict",type=bool, default=False,help="是否使用MatIEC编译器进行严格检查")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if not os.path.isdir(args.input_dir):
        print(f"❌ 错误: 输入目录 '{args.input_dir}' 不存在！")
        exit(1)

    cleaner = STDataCleaner(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        ext=args.ext,
        iec2c_path=args.iec2c,
        st_lib_path=args.st_lib,
        use_matiec=args.strict
    )
    cleaner.run()