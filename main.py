import asyncio
from src.distillation_engine import AsyncSTDistillationEngine
from src.prompt_manager import PromptManager
from src.config_manager import ConfigManager
import platform


if __name__ == "__main__":
    # Windows 平台需要设置 EventLoop 策略
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    config = ConfigManager()
    prompt_manager = PromptManager('prompts.yaml')
    engine = AsyncSTDistillationEngine(config,prompt_manager)
    asyncio.run(engine.run())