import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from tqdm.asyncio import tqdm


class BaseDistillationEngine(ABC):
    """
    【核心抽象层】
    定义了模型蒸馏的标准流水线 (Pipeline) 和并发调度器 (Scheduler)。
    具体的 LLM 调用、Prompt 获取、存储逻辑由子类实现。
    """

    def __init__(self, max_concurrency: int = 10, target_count: int = 1000):
        self.max_concurrency = max_concurrency
        self.target_count = target_count

        # 核心调度组件
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.running_tasks = set()
        self.logger = logging.getLogger(self.__class__.__name__)

    # ==========================================
    # 🧩 必须由子类实现的接口 (Abstract Methods)
    # ==========================================

    @abstractmethod
    async def call_llm(self, messages: List[Dict], temperature: float = 0.7, json_mode: bool = False) -> Dict:
        """底层 LLM 调用接口"""
        pass

    @abstractmethod
    def get_prompt(self, stage: str, **kwargs) -> Any:
        """获取 Prompt (stage: 'brainstorm', 'evolution', 'generation', 'critique')"""
        pass

    @abstractmethod
    async def validate_syntax(self, code: str) -> tuple[bool, str]:
        """静态代码校验 (正则/AST)"""
        pass

    @abstractmethod
    async def save_data(self, data_type: str, **kwargs):
        """数据持久化 (data_type: 'success', 'dpo', 'golden')"""
        pass

    @abstractmethod
    async def is_task_duplicate(self, task: str) -> bool:
        """去重检查"""
        pass

    @abstractmethod
    async def get_golden_examples(self, count: int = 1) -> List[Dict]:
        """获取 Few-Shot 样本"""
        pass

    @abstractmethod
    async def current_count(self) -> int:
        """获取当前进度"""
        pass

    # ==========================================
    # ⚙️ 核心调度逻辑 (Template Methods)
    # 这部分逻辑被锁定，子类复用即可，无需重写
    # ==========================================

    async def _step_brainstorm(self) -> List[str]:
        """步骤 0: 头脑风暴生成新题目"""
        prompt = self.get_prompt("brainstorm", count=10)
        try:
            # 假设 LLM 返回的是 JSON list
            response = await self.call_llm([{"role": "user", "content": prompt}], temperature=0.9, json_mode=True)
            return response if isinstance(response, list) else []
        except Exception as e:
            self.logger.warning(f"Brainstorm failed: {e}")
            return []

    async def _step_evolve(self, base_task: str) -> str:
        """步骤 1: 任务进化"""
        prompt = self.get_prompt("evolution", task=base_task)
        # 如果 Prompt Manager 决定不进化 (返回了原字符串)，则跳过
        if prompt == base_task:
            return base_task
        try:
            resp = await self.call_llm([{"role": "user", "content": prompt}], temperature=0.8)
            return resp.get("content", base_task)  # 假设返回字典包含 content
        except:
            return base_task

    async def _step_pipeline(self, raw_task: str):
        """🔥 核心流水线：定义了蒸馏的标准步骤"""

        # 0. 去重检查
        if await self.is_task_duplicate(raw_task):
            return

        async with self.semaphore:
            # 1. Evolve (进化)
            task = await self._step_evolve(raw_task)

            # 2. Context (准备上下文)
            examples = await self.get_golden_examples(1)
            system_prompt = self.get_prompt("system", examples=examples)
            user_prompt = self.get_prompt("generation", task=task)

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            rejected_history = []

            # 3. Loop (生成-校验循环)
            for attempt in range(3):  # Max Retries
                try:
                    # A. Generate
                    response = await self.call_llm(messages, temperature=0.7, json_mode=True)
                    code = response.get('code', '')
                    thought = response.get('thought', '')

                    # B. Validate (Syntax)
                    is_valid, err_msg = await self.validate_syntax(code)
                    if not is_valid:
                        rejected_history.append(code)
                        messages.append({"role": "assistant", "content": code})
                        messages.append({"role": "user", "content": f"Syntax Error: {err_msg}. Fix it."})
                        continue

                    # C. Critique (Logic Review)
                    critique_prompt = self.get_prompt("critique", task=task, code=code)
                    review = await self.call_llm([{"role": "user", "content": critique_prompt}], temperature=0.1,
                                                 json_mode=True)

                    if review.get('passed', True):
                        # === Success Path ===
                        await self.save_data("success", task=task, code=code, thought=thought, raw_task=raw_task)

                        if rejected_history:
                            await self.save_data("dpo", task=task, chosen=code, rejected=rejected_history[-1])

                        await self.save_data("golden", task=task, code=code)

                        self.logger.info(f"✅ Finished: {task[:30]}...")
                        return
                    else:
                        # === Fail Path ===
                        rejected_history.append(code)
                        messages.append({"role": "assistant", "content": code})
                        messages.append({"role": "user", "content": f"Logic Error: {review.get('reason')}."})

                except Exception as e:
                    self.logger.error(f"Pipeline Error: {e}")
                    await asyncio.sleep(2 ** attempt)

    async def run(self):
        """🚀 主调度器：生产者-消费者模式"""
        self.logger.info(f"Engine Started | Target: {self.target_count}")
        pbar = tqdm(total=self.target_count)

        # 恢复进度条
        current = await self.current_count()
        pbar.update(current)

        while (await self.current_count()) < self.target_count:

            # 动态补货策略
            if len(self.running_tasks) < self.max_concurrency * 1.5:
                new_tasks = await self._step_brainstorm()

                for t in new_tasks:
                    if not await self.is_task_duplicate(t):
                        # 调度任务
                        task_coro = asyncio.create_task(self._step_pipeline(t))
                        self.running_tasks.add(task_coro)
                        # 清理回调
                        task_coro.add_done_callback(lambda t: self.running_tasks.discard(t))
                        task_coro.add_done_callback(lambda t: pbar.update(1))

            await asyncio.sleep(1)

        # 等待剩余任务完成
        await asyncio.gather(*self.running_tasks)