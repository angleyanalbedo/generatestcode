import asyncio

from llmclient import LLMClient
from src.distillation.distillation_engine import AsyncSTDistillationEngine
from prompt_manager import PromptManager
from config_manager import ConfigManager
import platform


if __name__ == "__main__":
    # Windows 平台需要设置 EventLoop 策略
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    config = ConfigManager()
    prompt_manager = PromptManager('prompts.yaml')
    client = LLMClient(api_key=config.api_key, base_url=config.base_url,backend_type=config.backend_type,model=config.model)
    engine = AsyncSTDistillationEngine(config,prompt_manager,client)
    asyncio.run(engine.run())