import json
import re
import logging
from openai import AsyncOpenAI
from typing import List, Dict, Any, Union

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, api_key: str, base_url: str, model: str, backend_type: str = "openai"):
        """
        统一的大模型客户端
        :param backend_type: 'openai', 'tgi', 'llamacpp', 'vllm'
        """
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=120.0)
        self.model = model
        self.backend_type = backend_type.lower()

    def _clean_json_content(self, raw_text: str) -> str:
        """从 LLM 输出中提取 JSON（完全使用你之前经过验证的鲁棒代码）"""
        cleaned = re.sub(r"```json|```", "", raw_text, flags=re.IGNORECASE).strip()
        # 优先匹配对象
        start, end = cleaned.find('{'), cleaned.rfind('}')
        if start != -1 and end != -1:
            return cleaned[start:end + 1]
        # 其次匹配数组
        start_list, end_list = cleaned.find('['), cleaned.rfind(']')
        if start_list != -1 and end_list != -1:
            return cleaned[start_list:end_list + 1]
        return ""

    async def chat(self, messages: List[Dict], temperature: float = 0.7, json_mode: bool = False) -> Union[
        str, Dict, List]:
        """核心生成接口，根据后端自动适配参数"""
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }

        # --- 针对不同后端的适配策略 ---
        if json_mode:
            if self.backend_type == "openai":
                # OpenAI 原生支持严格的 JSON Mode
                kwargs["response_format"] = {"type": "json_object"}
            elif self.backend_type == "llamacpp":
                # Llama.cpp 如果配置了 JSON Schema，可以在这里透传
                pass
            elif self.backend_type == "tgi":
                # TGI 通常通过 Prompt 约束，这里可以加一点重复惩罚防止 JSON 崩坏
                kwargs["extra_body"] = {"repetition_penalty": 1.05}

        try:
            # 统一调用
            resp = await self.client.chat.completions.create(**kwargs)
            content = resp.choices[0].message.content

            # 如果要求返回 JSON，自动清洗并解析
            if json_mode:
                cleaned_str = self._clean_json_content(content)
                if not cleaned_str:
                    logger.warning(f"⚠️ 无法从输出中提取 JSON。原始输出: {content[:100]}")
                    return {}  # 或者返回 []
                return json.loads(cleaned_str)

            # 否则直接返回字符串
            return content

        except Exception as e:
            logger.error(f"❌ LLMClient Chat Error ({self.backend_type}): {str(e)}")
            raise e

    async def brainstorm(self, prompt: str, count: int = 1) -> List[Any]:
        """简化的生成接口（直接返回解析好的 JSON 数组/对象）"""
        try:
            # 明确要求模型返回 JSON 数组格式
            system_prompt = f"You must output a JSON array containing exactly {count} items. Do not output any other text."
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]

            # 直接调用 chat 并开启 json_mode
            result = await self.chat(messages, temperature=0.9, json_mode=True)

            # 容错处理：确保返回的是列表
            if isinstance(result, list):
                return result
            elif isinstance(result, dict) and len(result) > 0:
                # 有些模型可能会用 {"tasks": [...]} 包裹
                return next(iter(result.values()))
            return []
        except Exception as e:
            logger.error(f"❌ Brainstorm Error: {str(e)}")
            return []