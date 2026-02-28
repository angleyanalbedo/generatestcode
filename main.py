import asyncio
import platform
from src.llmclient import LLMClient
from src.distillation.distillation_engine import AsyncSTDistillationEngine
from src.prompt_manager import PromptManager
from src.config_manager import ConfigManager

async def main():
    print("🚀 正在初始化 Industrial-ST-Distiller 引擎...")
    config = ConfigManager()
    prompt_manager = PromptManager('prompts.yaml')
    
    # 注入解析好的 config.api_keys 列表
    client = LLMClient(
        api_keys=config.api_keys, 
        base_url=config.base_url,
        backend_type=config.backend_type,
        model=config.model
    )
    
    engine = AsyncSTDistillationEngine(config, prompt_manager, client)
    await engine.run()

if __name__ == "__main__":
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())