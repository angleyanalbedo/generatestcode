import json
import re
import os
import random
import asyncio
import platform
from src.prompt_manager import PromptManager
from src.config_manager import ConfigManager
import logging
from typing import List, Dict, Set, Optional, Any
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

class IMAsyncSTDistillationEngine:
    def __init__(self,config:ConfigManager,prompts:PromptManager):
        # 1. 初始化异步客户端
        self.aclient = AsyncOpenAI(api_key=API_KEYS[0], base_url=config.base_url)
        self.prompts = prompts
        self.config = config
        # 2. 异步锁和信号量
        self.file_lock = asyncio.Lock()
        self.golden_lock = asyncio.Lock()
        self.console_lock = asyncio.Lock()

        # 核心：信号量控制最大并发请求数，防止撑爆显存
        self.semaphore = asyncio.Semaphore(config.max_concurrency)

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
        try:
            # await 异步调用
            response = await self.aclient.chat.completions.create(
                model=MODEL,
                messages=self.prompts.get_brainstorm_messages(topic, count),
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
        try:
            response = await self.aclient.chat.completions.create(
                model=MODEL,
                messages=self.prompts.get_evolution_prompt(base_task),
                temperature=0.8
            )
            return response.choices[0].message.content.strip()
        except:
            return base_task

    async def ai_critique_async(self, task, code):
        """异步 AI 审查"""
        try:
            response = await self.aclient.chat.completions.create(
                model=MODEL,
                messages=self.prompts.get_critique_messages(task, code),
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

            messages = self.prompts.get_generation_messages(task, golden_example=self.golden_examples)

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


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("DistillEngine")


class IOHandler:
    """
    负责所有的文件读写操作和内存去重逻辑。
    """

    def __init__(self, config: ConfigManager):
        self.cfg = config
        self.output_file = config.output_file
        self.dpo_file = config.dpo_file
        self.golden_file = config.golden_file

        # 锁
        self.io_lock = asyncio.Lock()
        self.golden_lock = asyncio.Lock()

        # 内存数据
        self.existing_tasks: Set[str] = set()
        self.golden_examples: List[Dict] = []

        # 初始化加载
        self._load_data_sync()

    def _load_data_sync(self):
        """启动时同步加载历史数据"""
        # 1. 加载已有任务去重
        count = 0
        for fpath in [self.cfg.history_file, self.output_file]:
            if os.path.exists(fpath):
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        for line in f:
                            try:
                                data = json.loads(line)
                                if "instruction" in data:
                                    # 提取 Prompt 中的 Task 部分，假设格式固定
                                    task = data['instruction'].split("for: ")[-1]
                                    self.existing_tasks.add(task)
                                    count += 1
                            except:
                                pass
                except Exception as e:
                    logger.warning(f"Error loading {fpath}: {e}")
        logger.info(f"📂 Loaded {count} existing tasks for deduplication.")

        # 2. 加载 Golden Examples
        if os.path.exists(self.golden_file):
            try:
                with open(self.golden_file, 'r', encoding='utf-8') as f:
                    self.golden_examples = json.load(f)
                logger.info(f"🏆 Loaded {len(self.golden_examples)} golden examples.")
            except Exception as e:
                logger.warning(f"Error loading golden file: {e}")

    async def is_duplicate(self, task: str) -> bool:
        return task in self.existing_tasks

    async def add_task_record(self, task: str):
        self.existing_tasks.add(task)

    async def get_random_golden_example(self) -> Optional[Dict]:
        """线程安全地获取一个 Golden Example"""
        async with self.golden_lock:
            if not self.golden_examples:
                return None
            return random.choice(self.golden_examples)

    async def update_golden(self, task: str, code: str):
        """更新 Golden Memory"""
        if not (200 < len(code) < 2000):
            return

        async with self.golden_lock:
            self.golden_examples.append({"task": task, "code": code})
            if len(self.golden_examples) > self.cfg.max_golden_examples:
                self.golden_examples.pop(0)

            # 异步保存
            await self._write_json(self.golden_file, self.golden_examples, mode='w')

    async def save_success(self, data: Dict):
        """保存成功数据"""
        await self._write_line(self.output_file, data)

    async def save_dpo(self, task: str, chosen: str, rejected: str, metadata: Dict):
        """保存 DPO 数据"""
        entry = {
            "prompt": f"Write ST code for: {task}",
            "chosen": chosen,
            "rejected": rejected,
            "metadata": metadata
        }
        await self._write_line(self.dpo_file, entry)

    async def _write_line(self, filepath: str, data: Dict):
        """底层行写入"""
        line = json.dumps(data, ensure_ascii=False) + "\n"
        async with self.io_lock:
            if HAS_AIOFILES:
                async with aiofiles.open(filepath, 'a', encoding='utf-8') as f:
                    await f.write(line)
            else:
                with open(filepath, 'a', encoding='utf-8') as f:
                    f.write(line)

    async def _write_json(self, filepath: str, data: Any, mode='w'):
        """底层 JSON 写入"""
        content = json.dumps(data, ensure_ascii=False, indent=2)
        if HAS_AIOFILES:
            async with aiofiles.open(filepath, mode, encoding='utf-8') as f:
                await f.write(content)
        else:
            with open(filepath, mode, encoding='utf-8') as f:
                f.write(content)

    def current_count(self):
        return len(self.existing_tasks)


class AsyncSTDistillationEngine:
    def __init__(self, config: ConfigManager, prompts: PromptManager):
        self.cfg = config
        self.prompts = prompts

        # 初始化组件
        self.io = IOHandler(config)
        self.aclient = AsyncOpenAI(api_key=config.api_key, base_url=config.base_url)

        # 并发控制
        self.semaphore = asyncio.Semaphore(config.max_concurrency)
        self.running_tasks = set()

    # --- 工具方法 ---
    def _clean_json_content(self, raw_text: str) -> str:
        """从 LLM 输出中提取 JSON"""
        cleaned = re.sub(r"```json|```", "", raw_text, flags=re.IGNORECASE).strip()
        start, end = cleaned.find('{'), cleaned.rfind('}')
        if start != -1 and end != -1: return cleaned[start:end + 1]
        return ""

    def _validate_st_syntax(self, code: str) -> tuple[bool, str]:
        """静态代码分析"""
        if re.search(r"\b\w+\s*=\s*\w+;", code):
            return False, "Illegal assignment operator '=' found. Use ':='."
        required_keywords = ["FUNCTION_BLOCK", "END_FUNCTION_BLOCK", "VAR", "END_VAR"]
        if not all(k in code for k in required_keywords):
            return False, "Missing required structure keywords (FUNCTION_BLOCK, VAR...)."
        if "ARRAY[*]" in code.upper() or "ARRAY [*]" in code.upper():
            return False, "Dynamic arrays 'ARRAY[*]' are not supported."
        return True, "Passed"

    # --- LLM 交互步骤 ---

    async def _step_brainstorm(self) -> List[str]:
        """生成新的任务 Idea"""
        # 随机组合领域
        domains = ["Motion", "Safety", "Closed Loop", "Data Processing", "Comms"]
        industries = ["Packaging", "Pharma", "Automotive", "Water Treatment"]
        topic = f"{random.choice(domains)} in {random.choice(industries)}"

        try:
            messages = self.prompts.get_brainstorm_messages(topic, count=10)
            response = await self.aclient.chat.completions.create(
                model=self.cfg.model,
                messages=messages,
                temperature=0.9
            )
            content = self._clean_json_content(response.choices[0].message.content)
            tasks = json.loads(content)
            return [t for t in tasks if isinstance(t, str) and len(t) > 10]
        except Exception as e:
            logger.warning(f"Brainstorm failed: {e}")
            return []

    async def _step_evolve(self, base_task: str) -> str:
        """任务进化"""
        if random.random() > 0.7:
            return base_task  # 30% 概率保持简单

        messages = self.prompts.get_evolution_prompt(base_task)
        # 假设 PromptManager 返回的是 messages 列表，如果只返回 prompt string，需调整
        if isinstance(messages, str):
            messages = [{"role": "user", "content": f"{messages}\nOutput ONLY the new task string."}]

        try:
            response = await self.aclient.chat.completions.create(
                model=self.cfg.model,
                messages=messages,
                temperature=0.8
            )
            return response.choices[0].message.content.strip()
        except:
            return base_task

    async def _step_critique(self, task: str, code: str) -> Dict:
        """AI 逻辑审查"""
        try:
            messages = self.prompts.get_critique_messages(task, code)
            response = await self.aclient.chat.completions.create(
                model=self.cfg.model,
                messages=messages,
                temperature=0.1
            )
            content = self._clean_json_content(response.choices[0].message.content)
            return json.loads(content)
        except:
            return {"passed": True, "reason": "Reviewer Failed (Default Pass)"}

    async def _process_single_task(self, raw_task: str):
        """🔥 单个任务的全流程处理"""
        if await self.io.is_duplicate(raw_task):
            return

        async with self.semaphore:
            # 1. 任务进化
            task = await self._step_evolve(raw_task)

            # 2. 准备上下文 (Golden Example)
            golden_example = await self.io.get_random_golden_example()

            # 获取生成用的 Messages
            # 注意：这里需要确保 PromptManager 接收单个 dict 或 None
            messages = self.prompts.get_generation_messages(task, golden_example=golden_example)

            rejected_history = []

            for attempt in range(self.cfg.max_retries):
                try:
                    # A. 生成代码
                    response = await self.aclient.chat.completions.create(
                        model=self.cfg.model,
                        messages=messages,
                        temperature=0.7
                    )

                    data = json.loads(self._clean_json_content(response.choices[0].message.content))
                    code = data.get('code', '')
                    thought = data.get('thought', '')

                    # B. 语法校验 (Syntax)
                    is_valid, error_msg = self._validate_st_syntax(code)

                    if not is_valid:
                        rejected_history.append(code)
                        messages.append({"role": "assistant", "content": code})
                        messages.append({"role": "user", "content": f"Syntax Error: {error_msg}. Fix it."})
                        continue

                    # C. 逻辑审查 (Critique)
                    review = await self._step_critique(task, code)

                    if review.get('passed', True):
                        # === 成功路径 ===

                        # 保存成功数据
                        result_data = {
                            "instruction": f"Write an IEC 61131-3 Structured Text function block for: {task}",
                            "output": code,
                            "metadata": {
                                "thought": thought,
                                "retries": attempt,
                                "evolution": "evolved" if task != raw_task else "base"
                            }
                        }
                        await self.io.save_success(result_data)

                        # 保存 DPO 数据 (如果有过错误)
                        if rejected_history:
                            await self.io.save_dpo(
                                task, code, rejected_history[-1],
                                metadata={"type": "self_correction"}
                            )

                        # 更新 Golden Set
                        await self.io.update_golden(task, code)

                        # 内存去重标记
                        await self.io.add_task_record(raw_task)

                        logger.info(f"✅ Finished: {task[:40]}... (Try {attempt + 1})")
                        return

                    else:
                        # === 失败路径 (Logic) ===
                        rejected_history.append(code)
                        messages.append({"role": "assistant", "content": code})
                        messages.append({"role": "user", "content": f"Logic Error: {review['reason']}. Fix it."})

                except Exception as e:
                    if "429" in str(e) or "Limit" in str(e):
                        wait_time = 5 * (attempt + 1)
                        logger.warning(f"⏳ Rate limit, sleeping {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    elif attempt == self.cfg.max_retries - 1:
                        logger.error(f"❌ Task failed after retries: {str(e)[:50]}")
                    else:
                        pass  # 忽略其他错误进行重试

    async def main_loop(self):
        """主调度循环"""
        logger.info(f"🚀 Engine Started | Target: {self.cfg.target_count} | Concurrency: {self.cfg.max_concurrency}")

        pending_tasks = set()

        while self.io.current_count() < self.cfg.target_count:

            # 动态补货策略
            # 当积压的任务数 < 并发数 * 1.5 时，才去生成新题目，避免内存中堆积太多未处理任务
            if len(pending_tasks) < self.cfg.max_concurrency * 1.5:
                new_tasks = await self._step_brainstorm()

                for t in new_tasks:
                    if not await self.io.is_duplicate(t):
                        # 创建 Task 并加入集合
                        task_coro = asyncio.create_task(self._process_single_task(t))
                        pending_tasks.add(task_coro)
                        # 完成后自动移除
                        task_coro.add_done_callback(pending_tasks.discard)

            # 打印进度 (每 5 秒或每 N 个任务)
            if self.io.current_count() % 10 == 0:
                print(f"💓 Progress: {self.io.current_count()}/{self.cfg.target_count} | Running: {len(pending_tasks)}",
                      end='\r')

            await asyncio.sleep(1)

        # 等待所有剩余任务完成
        if pending_tasks:
            await asyncio.gather(*pending_tasks)
        logger.info("🎉 Distillation Complete!")

