import asyncio
from src.engine import DistillationEngine
from src.components import Config, LLMClient, STValidator, DataManager
from src.prompt_manager import PromptManager  # 假设你已经有了这个


async def main():
    # 1. 加载配置
    cfg = Config("config.yaml")

    # 2. 初始化组件 (Dependency Injection)
    llm = LLMClient(
        api_key="local",
        base_url="http://localhost:8000/v1",
        model="industrial-coder"
    )

    prompts = PromptManager("prompts.yaml")
    validator = STValidator()
    storage = DataManager(
        output_file="data/st_train.jsonl",
        dpo_file="data/st_dpo.jsonl",
        golden_file="data/golden.json"
    )

    # 3. 组装引擎
    engine = DistillationEngine(
        config=cfg,
        llm_client=llm,
        prompt_manager=prompts,
        validator=validator,
        storage=storage
    )

    # 4. 启动
    await engine.run()


if __name__ == "__main__":
    asyncio.run(main())