import asyncio
import json
import logging
import random
import os
from datetime import datetime
from typing import List, Dict, Set, Optional, Any

from src.llmclient import LLMClient
from src.prompt_manager import PromptManager
from src.config_manager import ConfigManager
# 🟢 引入你早期的正则验证器 (注意保持你的实际路径拼写 stvailder)
from src.stvailder.stvailder import STValidator

try:
    import aiofiles
    HAS_AIOFILES = True
except ImportError:
    HAS_AIOFILES = False

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("DistillEngine")


class IOHandler:
    """【组件化】IO 处理器：负责所有的文件读写操作、内存去重逻辑和 Golden Memory 维护。"""
    def __init__(self, config: ConfigManager):
        self.cfg = config
        
        self.output_file = getattr(config, 'output_file', 'data/st_dataset_local_part.jsonl')
        self.dpo_file = getattr(config, 'dpo_file', 'data/st_dpo_dataset.jsonl')
        self.golden_file = getattr(config, 'golden_file', 'data/st_golden_dataset.json')
        self.history_file = getattr(config, 'history_file', 'data/st_history_dataset.json')
        self.error_log_file = getattr(config, 'error_log_file', 'data/error_records.jsonl')
        self.failed_file = getattr(config, 'failed_file', 'data/failed_tasks.jsonl')

        self.io_lock = asyncio.Lock()
        self.golden_lock = asyncio.Lock()

        self.existing_tasks: Set[str] = set()
        self.golden_examples: List[Dict] = []

        self._load_data_sync()

    def _load_data_sync(self):
        count = 0
        for fpath in [self.history_file, self.output_file]:
            if fpath and os.path.exists(fpath):
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        for line in f:
                            try:
                                data = json.loads(line)
                                if "instruction" in data:
                                    task = data['instruction'].split("for: ")[-1]
                                    self.existing_tasks.add(task)
                                    count += 1
                            except: pass
                except Exception as e:
                    logger.warning(f"Error loading {fpath}: {e}")

        logger.info(f"📂 [Storage] 去重索引库构建完成，共计: {count} 条历史任务。")

        if self.golden_file and os.path.exists(self.golden_file):
            try:
                with open(self.golden_file, 'r', encoding='utf-8') as f:
                    self.golden_examples = json.load(f)
                logger.info(f"🏆 [Storage] 已加载 {len(self.golden_examples)} 个 Golden Examples。")
            except: pass

    async def is_duplicate(self, task: str) -> bool:
        return task in self.existing_tasks

    async def add_task_record(self, task: str):
        self.existing_tasks.add(task)

    async def get_random_golden_example(self) -> Optional[Dict]:
        async with self.golden_lock:
            if not self.golden_examples: return None
            return random.choice(self.golden_examples)

    async def update_golden(self, task: str, code: str):
        if not (200 < len(code) < 2000): return
        async with self.golden_lock:
            self.golden_examples.append({"task": task, "code": code})
            if len(self.golden_examples) > 50: 
                self.golden_examples.pop(0)
            await self._write_json(self.golden_file, self.golden_examples, mode='w')

    async def save_success(self, data: Dict):
        await self._write_line(self.output_file, data)

    async def save_failed_record(self, data: dict):
        record = {
            "timestamp": datetime.now().isoformat(),
            "task_context": data.get("task"),
            "error_type": data.get("type", "exception_failure"),
            "error_detail": data.get("error"),
            "last_code_snippet": data.get("code")
        }
        await self._write_line(self.error_log_file, record)

    async def save_failed_task(self, data: dict):
        data["timestamp"] = datetime.now().isoformat()
        await self._write_line(self.failed_file, data)

    async def save_dpo(self, task: str, chosen: str, rejected: str, metadata: Dict):
        entry = {
            "prompt": f"Write ST code for: {task}",
            "chosen": chosen,
            "rejected": rejected,
            "metadata": metadata
        }
        await self._write_line(self.dpo_file, entry)

    async def _write_line(self, filepath: str, data: Dict):
        line = json.dumps(data, ensure_ascii=False) + "\n"
        async with self.io_lock:
            if HAS_AIOFILES:
                async with aiofiles.open(filepath, 'a', encoding='utf-8') as f:
                    await f.write(line)
            else:
                with open(filepath, 'a', encoding='utf-8') as f:
                    f.write(line)

    async def _write_json(self, filepath: str, data: Any, mode='w'):
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
    """【核心编排者】工业级并发蒸馏引擎"""

    def __init__(self, config: ConfigManager, prompts: PromptManager, client: LLMClient):
        self.cfg = config
        self.prompts = prompts
        self.task_queue = asyncio.Queue(maxsize=500)
        self.use_strict = getattr(config, 'use_strict', True)

        # 🟢 纯粹的正则轻量级校验器
        self.validator = STValidator()

        self.io = IOHandler(config)
        self.llm_client = client

        self.semaphore = asyncio.Semaphore(config.max_concurrency)
        self.running_tasks = set()

    def _validate_st_syntax(self, code: str) -> tuple[bool, str]:
        """封装校验调用，保持代码整洁"""
        # 调用你的正则验证器（如果你的验证器核心方法叫 validate_v2，请自行修改）
        return self.validator.validate(code)

    async def _step_brainstorm(self) -> List[str]:
        """生成新的任务 Idea"""
        domains = ["Motion", "Safety", "Closed Loop", "Data Processing", "Comms"]
        industries = ["Packaging", "Pharma", "Automotive", "Water Treatment"]
        topic = f"{random.choice(domains)} in {random.choice(industries)}"

        try:
            messages = self.prompts.get_brainstorm_messages(topic, count=10)
            response = await self.llm_client.chat(messages=messages, temperature=0.7, json_mode=True)
            
            tasks = []
            if isinstance(response, list):
                tasks = response
            elif isinstance(response, dict):
                tasks = response.get("tasks", []) 
                if not tasks and len(response) > 0:
                    tasks = next(iter(response.values()))

            return [t for t in tasks if isinstance(t, str) and len(t) > 10]
        except Exception as e:
            logger.warning(f"Brainstorm failed: {str(e)[:50]}")
            return []

    async def _task_producer(self):
        """后台生产者：不停地构思新题目"""
        while self.io.current_count() < self.cfg.target_count:
            if self.task_queue.qsize() < 500:
                new_tasks = await self._step_brainstorm()
                for t in new_tasks:
                    if not await self.io.is_duplicate(t):
                        await self.task_queue.put(t)
            else:
                await asyncio.sleep(1)

    async def _step_evolve(self, base_task: str) -> str:
        """任务进化"""
        if random.random() > 0.7: return base_task 
        try:
            messages = self.prompts.get_evolution_prompt(base_task)
            if isinstance(messages, str):
                messages = [{"role": "user", "content": f"{messages}\nOutput ONLY the new task string."}]
            response = await self.llm_client.chat(json_mode=False, messages=messages, temperature=0.8)
            return response.strip()
        except:
            return base_task

    async def _step_critique(self, task: str, code: str) -> Dict:
        """AI 逻辑审查"""
        try:
            messages = self.prompts.get_critique_messages(task, code)
            response = await self.llm_client.chat(messages=messages, temperature=0.1, json_mode=True)
            if isinstance(response, dict):
                return response
            return {"passed": True, "reason": "Reviewer format error, forced pass"}
        except:
            return {"passed": True, "reason": "Reviewer Failed (Default Pass)"}

    async def _process_single_task(self, raw_task: str):
        """🔥 单个任务的全流程处理"""
        if await self.io.is_duplicate(raw_task): return

        async with self.semaphore:
            task = await self._step_evolve(raw_task)
            golden_example = await self.io.get_random_golden_example()
            messages = self.prompts.get_generation_messages(task, golden_example=golden_example)
            rejected_history = []
            
            max_retries = getattr(self.cfg, 'max_retries', 3)

            for attempt in range(max_retries):
                try:
                    # --- 生成阶段 ---
                    response = await self.llm_client.chat(messages=messages, temperature=0.5, json_mode=True)
                    if not isinstance(response, dict):
                        raise ValueError("Model returned invalid JSON structure.")
                        
                    code = response.get('code', '')
                    thought = response.get('thought', '')

                    # --- 校验阶段 1: 静态正则语法 ---
                    is_valid, error_msg = self._validate_st_syntax(code)

                    if not is_valid:
                        rejected_history.append({"code": code, "error": error_msg})
                        messages.append({"role": "assistant", "content": code})
                        messages.append({"role": "user", "content": f"Syntax Error: {error_msg}. Fix it."})
                        continue

                    # --- 校验阶段 2: AI 审查 ---
                    review = await self._step_critique(task, code)

                    if review.get('passed', True):
                        # === 成功路径 ===
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

                        if rejected_history:
                            await self.io.save_dpo(task, code, rejected_history[-1]["code"], {"type": "self_correction"})

                        await self.io.update_golden(task, code)
                        await self.io.add_task_record(raw_task)

                        logger.info(f"✅ Finished: {task[:40]}... (Try {attempt + 1})")
                        return

                    else:
                        # === 失败路径 (Logic) ===
                        rejected_history.append({"code": code, "error": review.get('reason')})
                        messages.append({"role": "assistant", "content": code})
                        messages.append({"role": "user", "content": f"Logic Error: {review['reason']}. Fix it."})

                except Exception as e:
                    error_msg = str(e)
                    
                    # 拦截全局毁灭性错误 (所有 Key 都被榨干)
                    if "ALL_KEYS_EXHAUSTED" in error_msg:
                        logger.error(f"🚨 致命错误：所有 Key 均已耗尽！该任务终止。")
                        break 
                        
                    if attempt == max_retries - 1:
                        logger.error(f"❌ 最终尝试失败: {error_msg[:50]}")
                        if 'code' in locals() and code:
                            await self.io.save_failed_record({
                                "task": task, "code": code, "error": error_msg, "type": "exception_failure"
                            })
                    else:
                        logger.warning(f"⚠️ [重试 {attempt+1}/{max_retries}] 生成遇挫: {error_msg[:50]}")
                        await asyncio.sleep(2)

            # === 彻底失败路径 (跳出循环后) ===
            if rejected_history:
                await self.io.save_failed_task({
                    "instruction": task,
                    "rejected_samples": rejected_history,
                    "final_reason": "Exhausted retries"
                })

    async def run(self):
        """主调度循环"""
        target_count = getattr(self.cfg, 'target_count', 200000)
        logger.info(f"🚀 Engine Started | Target: {target_count} | Concurrency: {self.cfg.max_concurrency}")

        producer_task = asyncio.create_task(self._task_producer())
        pending_tasks = set()

        while self.io.current_count() < target_count:
            if len(pending_tasks) < self.cfg.max_concurrency * 1.5:
                if not self.task_queue.empty():
                    t = await self.task_queue.get()
                    task_coro = asyncio.create_task(self._process_single_task(t))
                    pending_tasks.add(task_coro)
                    task_coro.add_done_callback(pending_tasks.discard)

            if self.io.current_count() % 10 == 0:
                print(f"💓 Progress: {self.io.current_count()}/{target_count} | Running: {len(pending_tasks)}", end='\r')

            await asyncio.sleep(0.5)

        if pending_tasks:
            await asyncio.gather(*pending_tasks)
        logger.info("🎉 Distillation Complete!")