from pathlib import Path
from typing import Tuple, List, Dict
import json
from tqdm import tqdm

from ..stvailder import STValidator
from ..stvailder import MatiecValidator
from ..stvailder import FastValidator
from ..utils import auto_repair


class STDataCleaner:
    def __init__(self, input_dir: str, output_dir: str, iec2c_path: str = "iec2c", st_lib_path: str="lib", use_matiec: bool=False,ext: str = ".json"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.ext = ext
        self.use_matiec = use_matiec

        # 初始化漏斗组件
        self.fast_validator = FastValidator()
        self.matiec_validator = MatiecValidator(iec2c_path=iec2c_path,st_lib_path=st_lib_path)
        self.validator = STValidator()

        self.stats = {
            "total_files": 0, "processed_files": 0, "total_samples": 0,
            "golden": 0,  # Matiec 编译通过的真金数据
            "matiec_error": 0,  # 编译器报错 (高级逻辑错/类型错)
            "basic_error": 0,  # 第一层被拦截的低级错误
            "empty": 0  # 纯废话
        }


    def process_single_file(self, file_path: Path) -> Dict[str, List[Dict]]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            return {}
        if not isinstance(data, list): return {}

        categorized_data = {"golden": [], "matiec_error": [], "basic_error": [], "empty": []}

        for item in data:
            self.stats["total_samples"] += 1
            original_code = item.get("output", "")
            repaired_code = auto_repair(original_code)

            if repaired_code != original_code:
                item["output"] = repaired_code
                item["was_repaired"] = True

            status = "golden"
            error_reason = None

            if not repaired_code:
                status = "empty"
                error_reason = "No code found"
            else:
                # 🚀 漏斗第一层：极速文本校验
                is_valid_s1, msg1 = self.fast_validator.validate(repaired_code)
                if not is_valid_s1:
                    status = "basic_error"
                    error_reason = msg1
                else:
                    # 🚀 漏斗第二层：真正的编译器校验
                    if self.use_matiec:
                        is_valid_s2, msg2 = self.matiec_validator.validate(repaired_code)
                    else:
                        is_valid_s2, msg2 = self.validator.validate_v2(repaired_code)
                    if not is_valid_s2:
                        status = "matiec_error"
                        error_reason = msg2

            item["st_metadata"] = {"quality": status, "error": error_reason}
            categorized_data[status].append(item)
            self.stats[status] += 1

        return categorized_data

    def run(self):
        files = list(self.input_dir.rglob(f"*{self.ext}"))
        self.stats["total_files"] = len(files)
        if not files: return
        if self.use_matiec:
            print(f"🚀 发现 {len(files)} 个文件，启动 MatIEC 级联清洗...")
        else:
            print(f"🚀 发现 {len(files)} 个文件，启动 Anltr4 级联清洗...")

        for file_path in tqdm(files, desc="Compiling & Validating"):
            categorized_data = self.process_single_file(file_path)
            if not categorized_data: continue
            self.stats["processed_files"] += 1

            file_out_dir = self.output_dir / file_path.stem
            file_out_dir.mkdir(parents=True, exist_ok=True)

            for status, items in categorized_data.items():
                if items:
                    out_file = file_out_dir / f"{status}.json"
                    with open(out_file, 'w', encoding='utf-8') as f:
                        json.dump(items, f, ensure_ascii=False, indent=2)

        self.print_report()

    def print_report(self):
        t = self.stats["total_samples"]
        g, me, be, e = self.stats["golden"], self.stats["matiec_error"], self.stats["basic_error"], self.stats["empty"]

        print("\n" + "=" * 60)
        if self.use_matiec:
            print("🛡️ 基于 MatIEC 编译器的 ST 数据清洗报告")
        else:
            print("🛡️ 基于 Anltr4 编译器的 ST 数据清洗报告")
        print("=" * 60)
        if t > 0:
            print(f"🥇 Golden (编译完美通过, 可做 SFT):   {g:6d} ({(g / t * 100):.2f}%)")
            print(f"🥈 Matiec Error (编译器报错, 绝佳 DPO): {me:6d} ({(me / t * 100):.2f}%)")
            print(f"🥉 Basic Error (格式残缺/低级错):       {be:6d} ({(be / t * 100):.2f}%)")
            print(f"🗑️ Empty (无效废弃数据):                {e:6d} ({(e / t * 100):.2f}%)")
        print("-" * 60)
        print(f"📁 结果已分类存放至: {self.output_dir.absolute()}")
        print("=" * 60)