import re
import json
import yaml
import aiofiles
from openai import AsyncOpenAI
from jinja2 import Template


# --- 配置管理 ---
class Config:
    def __init__(self, path="config.yaml"):
        with open(path) as f:
            self._data = yaml.safe_load(f)

    def __getattr__(self, name):
        return self._data.get(name)


# --- LLM 客户端 ---
class LLMClient:
    def __init__(self, api_key, base_url, model):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    async def chat(self, messages, temperature=0.7, json_mode=False):
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        resp = await self.client.chat.completions.create(**kwargs)
        content = resp.choices[0].message.content
        return json.loads(content) if json_mode else content

    async def brainstorm(self, prompt, count):
        # 简化的生成接口
        try:
            resp = await self.chat([{"role": "user", "content": prompt}], temperature=0.9)
            # 这里需要一个 clean_json 的辅助函数
            return json.loads(resp)
        except:
            return []


# --- 校验器 ---
class STValidator:
    """专门负责 ST 语言的校验逻辑"""

    def validate(self, code):
        if re.search(r"\b\w+\s*=\s*\w+;", code):
            return False, "Illegal assignment '='"
        required = ["FUNCTION_BLOCK", "END_VAR"]
        if not all(k in code for k in required):
            return False, "Missing keywords"
        return True, "Passed"


# --- 存储管理 ---
import os
import json
import asyncio
import aiofiles
from typing import List, Dict, Optional


class DataManager:
    """
    数据持久化层：负责所有文件 IO、去重逻辑和样本库维护。
    遵循：单例文件锁、异步非阻塞写入。
    """

    def __init__(self, output_file: str, dpo_file: str, golden_file: str, max_golden_size: int = 50):
        self.output_file = output_file
        self.dpo_file = dpo_file
        self.golden_file = golden_file
        self.max_golden_size = max_golden_size

        # 细粒度锁：将 IO 锁和内存数据锁分开，提升并发性能
        self.io_lock = asyncio.Lock()  # 负责写文件
        self.golden_lock = asyncio.Lock()  # 负责维护 Golden 队列

        # 内存状态
        self.existing_tasks = set()
        self.golden_examples: List[Dict] = []

        # 🔥 初始化：同步加载已有数据 (构造函数中不建议用 async，所以这里只是触发加载逻辑)
        self._load_existing_data()

    def _load_existing_data(self):
        """同步加载历史数据（仅在启动时运行一次）"""
        # 1. 加载去重库
        count = 0
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            data = json.loads(line)
                            if "instruction" in data:
                                # 假设 instruction 是 "Write ST code for: {task}"
                                # 这里做简单的字符串提取，或者直接存完整 instruction
                                task = data['instruction']
                                self.existing_tasks.add(task)
                                count += 1
                        except:
                            pass
            except Exception as e:
                print(f"⚠️ Load History Failed: {e}")
        print(f"📂 [Storage] Loaded {count} existing tasks.")

        # 2. 加载黄金样本
        if os.path.exists(self.golden_file):
            try:
                with open(self.golden_file, 'r', encoding='utf-8') as f:
                    self.golden_examples = json.load(f)
            except:
                self.golden_examples = []
        print(f"🏆 [Storage] Loaded {len(self.golden_examples)} golden examples.")

    async def is_duplicate(self, task: str) -> bool:
        """检查任务是否已存在"""
        # 注意：这里假设 instruction 格式是固定的
        formatted_task = task  # 或者加上前缀 f"Write ST code for: {task}"
        return formatted_task in self.existing_tasks

    async def get_random_golden_examples(self, count: int = 1) -> List[Dict]:
        """随机获取 N 个优质样本用于 Few-Shot"""
        import random
        async with self.golden_lock:
            if not self.golden_examples:
                return []
            # 防止样本不够
            k = min(len(self.golden_examples), count)
            return random.sample(self.golden_examples, k)

    async def save_success(self, task: str, code: str, thought: str, raw_task: str):
        """保存清洗后的 SFT 数据 (Supervised Fine-Tuning)"""
        record = {
            "instruction": raw_task,  # 或者加上 Prompt 前缀
            "output": code,
            "metadata": {
                "thought": thought,
                "type": "synthetic_st"
            }
        }

        line = json.dumps(record, ensure_ascii=False) + "\n"

        async with self.io_lock:
            # 使用 aiofiles 进行异步追加写入
            async with aiofiles.open(self.output_file, 'a', encoding='utf-8') as f:
                await f.write(line)
            # 更新内存去重集合
            self.existing_tasks.add(raw_task)

    # ================= 🚀 补全部分开始 =================

    async def save_dpo(self, task: str, chosen: str, rejected: str, metadata: dict = None):
        """
        保存 DPO 偏好数据 (Direct Preference Optimization)。
        当生成的代码经过 Review 失败后，被视为 Rejected (负样本)。
        """
        entry = {
            "prompt": f"Write IEC 61131-3 Structured Text for: {task}",
            "chosen": chosen,  # 最终通过校验的代码
            "rejected": rejected,  # 之前失败的代码
            "metadata": metadata or {"source": "self-correction"}
        }

        line = json.dumps(entry, ensure_ascii=False) + "\n"

        async with self.io_lock:
            async with aiofiles.open(self.dpo_file, 'a', encoding='utf-8') as f:
                await f.write(line)

    async def update_golden(self, task: str, code: str):
        """
        更新内存中的 Golden Set，并异步持久化到磁盘。
        策略：FIFO 队列，保持固定大小。
        """
        # 1. 简单的质量过滤 (太短或太长都不适合做 Few-Shot)
        if not (200 < len(code) < 2000):
            return

        new_entry = {"task": task, "code": code}

        async with self.golden_lock:
            # 2. 更新内存队列
            self.golden_examples.append(new_entry)

            # 如果超过容量，移除最早的 (FIFO)
            if len(self.golden_examples) > self.max_golden_size:
                self.golden_examples.pop(0)

                # 3. 持久化 (这里是覆盖写入 JSON Array，不是追加)
            # 为了数据安全，这里也可以考虑写临时文件再 rename，但 Demo 级别直接写即可
            try:
                content = json.dumps(self.golden_examples, indent=2, ensure_ascii=False)
                async with aiofiles.open(self.golden_file, 'w', encoding='utf-8') as f:
                    await f.write(content)
            except Exception as e:
                print(f"❌ Error saving golden prompts: {e}")

    async def count_tasks(self):
        """返回当前已完成的任务总数"""
        return len(self.existing_tasks)