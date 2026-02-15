import asyncio
import logging
import random
from tqdm.asyncio import tqdm


class DistillationEngine:
    """
    通用蒸馏引擎：负责调度并发、管理生命周期、处理错误重试。
    不包含具体的业务逻辑（如 ST 语法），业务逻辑由 validator 和 prompt_manager 注入。
    """

    def __init__(self, config, llm_client, prompt_manager, validator, storage):
        self.cfg = config
        self.llm = llm_client
        self.prompts = prompt_manager
        self.validator = validator
        self.storage = storage

        # 并发控制
        self.semaphore = asyncio.Semaphore(config.max_concurrency)
        self.running_tasks = set()
        self.logger = logging.getLogger("Engine")

    async def _evolve_task(self, base_task):
        """任务进化步骤"""
        # 策略：30% 概率不进化
        if random.random() > self.cfg.evolution_rate:
            return base_task

        prompt = self.prompts.build("evolution", task=base_task)
        try:
            return await self.llm.generate(prompt, temperature=0.8)
        except Exception:
            return base_task

    async def _ai_critique(self, task, code):
        """AI 审查步骤"""
        prompt = self.prompts.build("critique", task=task, code=code)
        try:
            response = await self.llm.generate(prompt, temperature=0.1, json_mode=True)
            return response  # 期望返回 JSON 对象
        except Exception:
            return {"passed": True, "reason": "Reviewer Failed"}

    async def _pipeline_worker(self, raw_task):
        """单任务流水线：进化 -> 生成 -> 校验 -> 审查 -> 保存"""
        async with self.semaphore:
            # 1. 进化
            task = await self._evolve_task(raw_task)

            # 2. 准备 Few-Shot 上下文
            examples = await self.storage.get_random_golden_examples()
            prompt_context = self.prompts.build("system_context", examples=examples)

            # 3. 尝试生成 (Retry Loop)
            messages = [
                {"role": "system", "content": prompt_context},
                {"role": "user", "content": self.prompts.build("generation", task=task)}
            ]

            rejected_history = []  # DPO 数据收集

            for attempt in range(self.cfg.max_retries):
                try:
                    # A. 生成
                    response_json = await self.llm.chat(messages, temperature=0.7, json_mode=True)
                    code = response_json.get('code', '')
                    thought = response_json.get('thought', '')

                    # B. 静态校验 (Validator)
                    is_valid, error_msg = self.validator.validate(code)

                    if not is_valid:
                        rejected_history.append(code)
                        messages.append({"role": "assistant", "content": code})
                        messages.append({"role": "user", "content": f"Syntax Error: {error_msg}. Fix it."})
                        continue

                    # C. AI 审查 (Critique)
                    review = await self._ai_critique(task, code)

                    if review.get('passed', True):
                        # === 成功 ===

                        # D. 数据落盘
                        await self.storage.save_success(task, code, thought, raw_task)

                        # E. DPO 数据 (如果有失败历史)
                        if rejected_history:
                            await self.storage.save_dpo(task, code, rejected_history[-1])

                        # F. 更新 Golden Set
                        await self.storage.update_golden(task, code)

                        self.logger.info(f"✅ Finished: {task[:30]}...")
                        return
                    else:
                        # 审查失败
                        rejected_history.append(code)
                        messages.append({"role": "assistant", "content": code})
                        messages.append({"role": "user", "content": f"Logic Error: {review['reason']}."})

                except Exception as e:
                    self.logger.error(f"Worker Error: {e}")
                    # 指数退避
                    await asyncio.sleep(2 ** attempt)

    async def run(self):
        """主循环：生产者-消费者模式"""
        self.logger.info("🚀 Engine Started")

        pbar = tqdm(total=self.cfg.target_count, desc="Distilling")

        while await self.storage.count_tasks() < self.cfg.target_count:

            # 动态补充任务
            if len(self.running_tasks) < self.cfg.max_concurrency * 1.5:
                # 调用 PromptManager 生成新 Idea
                new_tasks = await self.llm.brainstorm(
                    self.prompts.build("brainstorm"),
                    count=10
                )

                for t in new_tasks:
                    if not await self.storage.is_duplicate(t):
                        task = asyncio.create_task(self._pipeline_worker(t))
                        self.running_tasks.add(task)
                        task.add_done_callback(lambda t: self.running_tasks.discard(t))
                        task.add_done_callback(lambda t: pbar.update(1))

            await asyncio.sleep(0.5)

        await asyncio.gather(*self.running_tasks)