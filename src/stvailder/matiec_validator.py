import subprocess
import tempfile
import os
import shutil
from pathlib import Path
from typing import Tuple


class MatiecValidator:
    def __init__(self, iec2c_path: str = "iec2c", st_lib_path: str = ""):
        """
        初始化 Matiec 编译器调用器
        :param iec2c_path: iec2c 可执行文件的路径 (如果已加入环境变量，直接填 "iec2c")
        :param st_lib_path: matiec 的标准库路径 (通常在 matiec/lib/C，用于加载标准定时器、计数器等)
        """
        self.iec2c_path = iec2c_path
        self.st_lib_path = st_lib_path

    def validate(self, st_code: str) -> Tuple[bool, str]:
        """
        调用 Matiec 编译器验证 ST 代码
        返回: (是否通过, 编译器的报错信息)
        """
        if not st_code.strip():
            return False, "Empty code"

        # 1. 创建临时 ST 文件和临时输出目录
        # 使用 tempfile 防止多进程/多线程清洗数据时文件冲突
        fd, temp_st_path = tempfile.mkstemp(suffix=".st", text=True)
        out_dir = tempfile.mkdtemp(prefix="matiec_out_")

        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(st_code)

            # 2. 构造命令行指令
            # 格式: iec2c -T <输出目录> [-I <标准库路径>] <输入文件.st>
            cmd = [self.iec2c_path, "-T", out_dir]
            if self.st_lib_path:
                cmd.extend(["-I", self.st_lib_path])
            cmd.append(temp_st_path)

            # 3. 执行编译并捕获输出
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10  # 防止编译器死锁
            )

            # 4. 判断结果
            if result.returncode == 0:
                return True, "Compiled successfully"
            else:
                # 提取编译器的标准输出和错误输出
                error_msg = result.stdout.strip() + "\n" + result.stderr.strip()
                # 简化错误信息，去掉临时文件路径，防止干扰模型
                error_msg = error_msg.replace(temp_st_path, "source.st")
                return False, error_msg

        except subprocess.TimeoutExpired:
            return False, "Matiec compiler timeout"
        except FileNotFoundError:
            return False, "Matiec compiler (iec2c) not found. Please check PATH."
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
        finally:
            # 5. 清理临时文件 (非常重要，否则磁盘会爆)
            if os.path.exists(temp_st_path):
                os.remove(temp_st_path)
            if os.path.exists(out_dir):
                shutil.rmtree(out_dir)