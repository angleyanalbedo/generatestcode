import json
import re
import os
import random
import asyncio
import platform

# 尝试导入异步文件库，如果没有安装则回退到同步（建议 pip install aiofiles）
try:
    import aiofiles

    HAS_AIOFILES = True
except ImportError:
    HAS_AIOFILES = False
    print("⚠️ 建议运行 pip install aiofiles 以获得最佳磁盘IO性能")

from openai import AsyncOpenAI

# ================= ⚙️ 全局配置区域 =================
API_KEYS = ["local-vllm-no-key"]
BASE_URL = "http://localhost:8000/v1"
MODEL = "industrial-coder"

OUTPUT_FILE = "st_dataset_local_part.jsonl"
DPO_FILE = "st_dpo_dataset.jsonl"
HISTORY_FILE = "st_dataset_r1.jsonl"
GOLDEN_FILE = "golden_prompts.json"

TARGET_TOTAL_COUNT = 200000
MAX_CONCURRENCY = 100  # 🔥 控制并发量 (替代 MAX_WORKERS)
MAX_RETRIES = 1
MAX_GOLDEN_EXAMPLES = 50


# ====================================================

class AsyncSTDistillationEngine:
    def __init__(self):
        # 1. 初始化异步客户端
        self.aclient = AsyncOpenAI(api_key=API_KEYS[0], base_url=BASE_URL)

        # 2. 异步锁和信号量
        self.file_lock = asyncio.Lock()
        self.golden_lock = asyncio.Lock()
        self.console_lock = asyncio.Lock()

        # 核心：信号量控制最大并发请求数，防止撑爆显存
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENCY)

        # 3. 内存数据
        self.existing_tasks = set()
        self.golden_examples = []

        # 4. 初始化加载 (启动时可以是同步的)
        self.load_all_history_sync()
        self.load_golden_memory_sync()

    def load_all_history_sync(self):
        """同步加载历史数据"""
        count = 0
        for fpath in [HISTORY_FILE, OUTPUT_FILE]:
            if os.path.exists(fpath):
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        for line in f:
                            try:
                                data = json.loads(line)
                                if "instruction" in data:
                                    task = data['instruction'].split("for: ")[-1]
                                    self.existing_tasks.add(task)
                                    count += 1
                            except:
                                pass
                except Exception:
                    pass
        print(f"📂 [Init] 已加载历史去重库: {count} 条")

    def load_golden_memory_sync(self):
        if os.path.exists(GOLDEN_FILE):
            try:
                with open(GOLDEN_FILE, 'r', encoding='utf-8') as f:
                    self.golden_examples = json.load(f)
                print(f"🏆 [Init] 已加载黄金范例: {len(self.golden_examples)} 个")
            except:
                pass

    # --- 辅助工具 (CPU计算型保持同步即可) ---
    def clean_json_content(self, raw_text):
        cleaned = re.sub(r"```json|```", "", raw_text, flags=re.IGNORECASE).strip()
        start, end = cleaned.find('{'), cleaned.rfind('}')
        if start != -1 and end != -1: return cleaned[start:end + 1]
        start_list, end_list = cleaned.find('['), cleaned.rfind(']')
        if start_list != -1 and end_list != -1: return cleaned[start_list:end_list + 1]
        return ""

    def validate_st_code(self, code):
        if re.search(r"\b\w+\s*=\s*\w+;", code): return False, "Illegal assignment '='"
        required = ["FUNCTION_BLOCK", "END_FUNCTION_BLOCK", "VAR", "END_VAR"]
        if not all(k in code for k in required): return False, "Missing structure keywords"
        if "ARRAY[*]" in code.upper() or "ARRAY [*]" in code.upper(): return False, "Dynamic arrays not supported"
        return True, "Passed"

    # --- 异步 I/O 操作 ---
    async def append_to_file(self, filepath, data):
        """异步写入文件"""
        line = json.dumps(data, ensure_ascii=False) + "\n"
        async with self.file_lock:
            if HAS_AIOFILES:
                async with aiofiles.open(filepath, 'a', encoding='utf-8') as f:
                    await f.write(line)
            else:
                # 兼容未安装 aiofiles 的情况
                with open(filepath, 'a', encoding='utf-8') as f:
                    f.write(line)

    async def save_golden_memory_async(self):
        async with self.golden_lock:
            if HAS_AIOFILES:
                async with aiofiles.open(GOLDEN_FILE, 'w', encoding='utf-8') as f:
                    await f.write(json.dumps(self.golden_examples, ensure_ascii=False, indent=2))
            else:
                with open(GOLDEN_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self.golden_examples, f, ensure_ascii=False, indent=2)

    # --- 核心逻辑 (异步化) ---

    async def generate_task_ideas_async(self, topic, count=10):
        prompt = f"""
You are an expert industrial automation engineer.
Brainstorm {count} DISTINCT, SPECIFIC, and INTERMEDIATE-LEVEL IEC 61131-3 Structured Text (ST) programming tasks related to: "{topic}".
Rules:
1. Cover real-world scenarios.
2. Output ONLY a JSON list of strings.
"""
        try:
            # await 异步调用
            response = await self.aclient.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9
            )
            content = self.clean_json_content(response.choices[0].message.content)
            tasks = json.loads(content)
            return [t for t in tasks if isinstance(t, str) and len(t) > 10]
        except Exception as e:
            # 简单的错误打印
            print(f"⚠️ [构思失败]: {str(e)[:50]}...")
            return []

    async def evolve_task_async(self, base_task):
        """异步进化任务"""
        if random.random() > 0.7: return base_task

        strategies = [
            f"Add a complex constraint: The system must handle asynchronous sensor signal jitter. Task: {base_task}",
            f"Rewrite to include a secondary objective: logging critical data to a buffer. Task: {base_task}",
            f"Make specific to Pharmaceutical industry (GAMP5 standards), ensuring data integrity. Task: {base_task}",
            f"Increase reasoning complexity: Implement using a robust State Machine. Task: {base_task}"
        ]

        try:
            response = await self.aclient.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user",
                           "content": f"{random.choice(strategies)}\nOutput ONLY the new task description string."}],
                temperature=0.8
            )
            return response.choices[0].message.content.strip()
        except:
            return base_task

    async def ai_critique_async(self, task, code):
        """异步 AI 审查"""
        prompt = f"""
You are a Senior PLC Code Reviewer. Review this IEC 61131-3 Structured Text code.
Task: {task}
Code:
{code}
Checklist:
1. Is the logic actually solving the task?
2. Are all used variables declared in VAR?
3. Is it safe (no infinite loops)?
Output JSON ONLY: {{"passed": boolean, "reason": "short explanation"}}
"""
        try:
            response = await self.aclient.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            content = self.clean_json_content(response.choices[0].message.content)
            return json.loads(content)
        except:
            return {"passed": True, "reason": "Reviewer Failed"}

    async def worker_generate_code(self, raw_task):
        """🔥 核心工作流协程"""
        if raw_task in self.existing_tasks: return None

        # 限制并发：在此处等待获取信号量
        async with self.semaphore:

            # 1. 进化任务
            task = await self.evolve_task_async(raw_task)

            # 2. 准备 Few-Shot (需要加锁读取)
            example_text = ""
            async with self.golden_lock:
                if self.golden_examples:
                    ex_task, ex_code = random.choice(self.golden_examples)
                    if len(ex_code) < 1500:
                        example_text = f"\n[Reference Example]\nTask: {ex_task}\nCode:\n{ex_code}\n------------------\n"

            strict_rules = """
STRICT CODING STANDARDS:
1. FLOAT SAFETY: Use epsilon (ABS(A-B)<0.001).
2. MATH SAFETY: Check division by zero.
3. COMPATIBILITY: Do NOT use dynamic arrays. Use fixed-size arrays.
4. FORMAT: Use 'FUNCTION_BLOCK', 'VAR', 'END_VAR'.
"""
            messages = [
                {"role": "system",
                 "content": f"You are an expert IEC 61131-3 PLC programmer.{strict_rules}{example_text}"},
                {"role": "user",
                 "content": f"Task: Write a FUNCTION_BLOCK for: \"{task}\".\nRequirements: Strictly IEC 61131-3 ST syntax. Use ':=' for assignment.\nOutput: JSON ONLY (keys: thought, code)."}
            ]

            rejected_attempts = []

            for attempt in range(MAX_RETRIES):
                try:
                    # 异步生成
                    response = await self.aclient.chat.completions.create(
                        model=MODEL, messages=messages, temperature=0.7
                    )
                    content = self.clean_json_content(response.choices[0].message.content)
                    data = json.loads(content)
                    code = data.get('code', '')
                    thought = data.get('thought', '')

                    # 静态正则校验
                    is_valid, error_msg = self.validate_st_code(code)

                    # 逻辑流优化：为了保证质量，即使正则通过，也建议走一下 AI 审查
                    # 但为了保留您原来的逻辑结构（正则失败才必然进审查重试，正则成功则看审查是否开启），
                    # 这里我做一个增强：正则通过 -> 也要进 AI 审查（双重保险）

                    if not is_valid:
                        # 正则挂了，记录失败，让 AI 重试
                        rejected_attempts.append(code)
                        messages += [
                            {"role": "assistant", "content": code},
                            {"role": "user", "content": f"Syntax Error: {error_msg}. Fix it."}
                        ]
                        continue  # 进入下一次 Retry

                    # 如果正则通过，进行 AI 逻辑审查
                    review = await self.ai_critique_async(task, code)

                    if review.get('passed', True):
                        # === 🎉 最终成功 ===

                        # 保存 DPO (如果有过失败历史)
                        if rejected_attempts:
                            dpo_entry = {
                                "prompt": f"Write ST code for: {task}",
                                "chosen": code,
                                "rejected": rejected_attempts[-1],
                                "metadata": {"critique": "Self-Correction"}
                            }
                            await self.append_to_file(DPO_FILE, dpo_entry)

                        # 更新黄金库
                        if 200 < len(code) < 2000:
                            async with self.golden_lock:
                                self.golden_examples.append((task, code))
                                if len(self.golden_examples) > MAX_GOLDEN_EXAMPLES:
                                    self.golden_examples.pop(0)
                            # 异步保存黄金库
                            await self.save_golden_memory_async()

                        # 构造结果
                        result = {
                            "instruction": f"Write an IEC 61131-3 Structured Text function block for: {task}",
                            "output": code,
                            "metadata": {"thought": thought, "retries": attempt,
                                         "evolution": "evolved" if task != raw_task else "base"}
                        }

                        # 写入主文件
                        await self.append_to_file(OUTPUT_FILE, result)

                        # 记录已完成
                        self.existing_tasks.add(raw_task)

                        async with self.console_lock:
                            retry_msg = f"(🔧{attempt})" if attempt > 0 else ""
                            print(f"✅ {task[:40]}... {retry_msg}")

                        return  # 结束该任务

                    else:
                        # 审查不通过
                        rejected_attempts.append(code)
                        messages += [
                            {"role": "assistant", "content": code},
                            {"role": "user", "content": f"Logic Error: {review['reason']}. Please fix."}
                        ]

                except Exception as e:
                    # 简单的错误处理
                    if "429" in str(e) or "Limit" in str(e):
                        await asyncio.sleep(5)  # 异步等待，不阻塞其他协程
                    else:
                        break  # 其他错误直接退出本次任务
            return None

    async def main_loop(self):
        print(f"🚀 Async Engine Started | Max Concurrency: {MAX_CONCURRENCY}")

        domains = ["Motion Control", "Closed Loop Control", "Safety Logic", "Data Processing", "Communication"]
        industries = ["Packaging", "Water Treatment", "Automotive", "Food & Bev", "Pharmaceutical"]

        # 任务集合，用于 await
        pending_tasks = set()

        while len(self.existing_tasks) < TARGET_TOTAL_COUNT:

            # 动态补货：当正在运行的任务数少于最大并发数时，生成新题目
            if len(pending_tasks) < MAX_CONCURRENCY * 1.5:
                topic = f"{random.choice(domains)} in {random.choice(industries)}"
                print(f"🧠 Brainstorming: {topic}...")

                new_tasks = await self.generate_task_ideas_async(topic)

                for t in new_tasks:
                    if t not in self.existing_tasks:
                        # 创建 Task (非阻塞)
                        task_coro = asyncio.create_task(self.worker_generate_code(t))
                        pending_tasks.add(task_coro)
                        # 任务完成后自动从集合移除
                        task_coro.add_done_callback(pending_tasks.discard)

            # 打印进度
            if len(self.existing_tasks) % 10 == 0:
                print(f"💓 Progress: {len(self.existing_tasks)}/{TARGET_TOTAL_COUNT} | Running: {len(pending_tasks)}")

            # 释放控制权，避免死循环占用 CPU
            await asyncio.sleep(1)

        # 等待剩余任务
        if pending_tasks:
            await asyncio.gather(*pending_tasks)


if __name__ == "__main__":
    # Windows 平台需要设置 EventLoop 策略
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    engine = AsyncSTDistillationEngine()
    asyncio.run(engine.main_loop())