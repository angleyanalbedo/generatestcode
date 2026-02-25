from pathlib import Path
from typing import Tuple, List, Dict
import json
from tqdm import tqdm

from stvailder.matiec_validator import MatiecValidator
from stvailder.stvailder import FastValidator


class STDataCleaner:
    def __init__(self, input_dir: str, output_dir: str, iec2c_path: str, ext: str = ".json"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.ext = ext
        # 初始化漏斗组件
        self.fast_validator = FastValidator()
        self.matiec_validator = MatiecValidator(iec2c_path=iec2c_path)

        # 详细统计数据字典
        self.stats = {
            "total_files": 0,
            "processed_files": 0,
            "total_samples": 0,
            "golden": 0,  # 完全正确 (可用于 SFT)
            "syntax_error": 0,  # 正则校验失败 (绝佳的 DPO 负样本)
            "ast_error": 0,  # 语义校验失败 (可用于后续大模型修复)
            "empty": 0  # 无法抢救的空数据
        }

    def auto_repair(self, code: str) -> str:
        """尝试自动修复和提取纯净的 ST 代码"""
        if not code:
            return ""

        import re
        # 1. 剥离 Markdown 包装
        md_match = re.search(r"```[a-zA-Z]*\n(.*?)```", code, re.DOTALL | re.IGNORECASE)
        if md_match:
            code = md_match.group(1)

        # 2. 尝试过滤掉开头的自然语言废话
        keywords = ["FUNCTION_BLOCK", "FUNCTION", "PROGRAM", "VAR", "TYPE"]
        first_idx = len(code)
        for kw in keywords:
            idx = code.upper().find(kw)
            if idx != -1 and idx < first_idx:
                first_idx = idx

        if first_idx != len(code) and first_idx > 0:
            code = code[first_idx:]

        return code.strip()

    def process_single_file(self, file_path: Path) -> Dict[str, List[Dict]]:
        """处理单个 JSON 文件，按质量分类返回数据字典"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print(f"\n⚠️ 警告: 文件解析失败，跳过 -> {file_path.name}")
            return {}

        if not isinstance(data, list):
            print(f"\n⚠️ 警告: 数据格式非数组，跳过 -> {file_path.name}")
            return {}

        # 准备分类桶
        categorized_data = {
            "golden": [],
            "syntax_error": [],
            "ast_error": [],
            "empty": []
        }

        for item in data:
            self.stats["total_samples"] += 1
            original_code = item.get("output", "")

            # 🚀 第一步：自动抢救
            repaired_code = self.auto_repair(original_code)
            if repaired_code != original_code:
                item["output"] = repaired_code
                item["was_repaired"] = True

            # 🚀 第二步：级联校验
            status = "golden"
            error_reason = None

            if not repaired_code:
                status = "empty"
                error_reason = "No code found after repair"
            else:
                is_valid_s1, msg1 = self.fast_validator.validate(repaired_code)
                if not is_valid_s1:
                    status = "syntax_error"
                    error_reason = msg1
                else:
                    is_valid_s2, msg2 = self.matiec_validator.validate(repaired_code)
                    if not is_valid_s2:
                        status = "ast_error"
                        error_reason = msg2

            # 🚀 第三步：记录元数据并分装到对应的桶中
            item["st_metadata"] = {
                "quality": status,
                "error": error_reason
            }

            categorized_data[status].append(item)
            self.stats[status] += 1

        return categorized_data

    def run(self):
        """执行批量清洗流程"""
        files = list(self.input_dir.rglob(f"*{self.ext}"))
        self.stats["total_files"] = len(files)

        if not files:
            print(f"❌ 在 {self.input_dir} 中未找到任何 {self.ext} 文件！")
            return

        print(f"🚀 发现 {len(files)} 个文件，开始批量清洗与分类...")

        for file_path in tqdm(files, desc="Processing Files"):
            categorized_data = self.process_single_file(file_path)

            if not categorized_data:
                continue

            self.stats["processed_files"] += 1

            # 🚀 核心改动：创建与原 JSON 同名的文件夹
            # 比如原文件是 github_repo_1.json，那么创建一个 github_repo_1/ 的文件夹
            file_out_dir = self.output_dir / file_path.stem
            file_out_dir.mkdir(parents=True, exist_ok=True)

            # 将不同类别的数据分别存入该文件夹下
            for status, items in categorized_data.items():
                if items:  # 只有该类目下有数据才创建文件
                    out_file = file_out_dir / f"{status}.json"
                    with open(out_file, 'w', encoding='utf-8') as f:
                        json.dump(items, f, ensure_ascii=False, indent=2)

        self.print_report()

    def print_report(self):
        """打印细粒度统计报告"""
        total = self.stats["total_samples"]
        golden = self.stats["golden"]
        syntax_err = self.stats["syntax_error"]
        ast_err = self.stats["ast_error"]
        empty = self.stats["empty"]

        print("\n" + "=" * 55)
        print("📊 ST 数据集深度清洗与分类报告")
        print("=" * 55)
        print(f"📂 扫描文件数: {self.stats['total_files']} (成功处理: {self.stats['processed_files']})")
        print(f"📦 总样本数:   {total}")
        print("-" * 55)

        if total > 0:
            print(f"🥇 Golden (SFT 黄金数据):  {golden:6d} ({(golden / total * 100):.2f}%)")
            print(f"🥈 AST Error (待 AI 修复): {ast_err:6d} ({(ast_err / total * 100):.2f}%)")
            print(f"🥉 Syntax Error (DPO 负样本):{syntax_err:6d} ({(syntax_err / total * 100):.2f}%)")
            print(f"🗑️ Empty (无效废弃数据):  {empty:6d} ({(empty / total * 100):.2f}%)")

        print("-" * 55)
        print(f"📁 分类结果已按原文件名存放至: {self.output_dir.absolute()}")
        print("=" * 55)