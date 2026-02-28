import json
import re
import logging
import asyncio
from openai import AsyncOpenAI
from typing import List, Dict, Any, Union

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, api_keys: Union[str, List[str]], base_url: str, model: str, backend_type: str = "openai"):
        """
        统一的大模型客户端（顺序榨干策略：一直用一个Key，直到死掉才换下一个）
        """
        if isinstance(api_keys, str):
            api_keys = [api_keys]
            
        if not api_keys:
            raise ValueError("❌ 必须提供至少一个 API Key！")

        self.api_keys = api_keys
        self.base_url = base_url
        self.model = model
        self.backend_type = backend_type.lower()
        
        # 核心状态记录
        self.current_key_index = 0
        self.client_lock = asyncio.Lock()
        
        # 初始化第一个客户端
        self._init_active_client()
        logger.info(f"🚀 启动顺序榨干模式！共载入 {len(self.api_keys)} 个 Key。")

    def _init_active_client(self):
        """初始化或重新初始化当前激活的客户端"""
        current_key = self.api_keys[self.current_key_index]
        self.client = AsyncOpenAI(api_key=current_key, base_url=self.base_url, timeout=120.0)
        safe_key = f"{current_key[:8]}***"
        logger.info(f"🔄 当前服役的 API Key: {safe_key} (第 {self.current_key_index + 1}/{len(self.api_keys)} 个)")

    async def _handle_key_death(self, failed_index: int):
        """处理 Key 阵亡的逻辑（带有高并发防抖保护）"""
        async with self.client_lock:
            # 防抖：只有第一个发现当前 Key 死掉的协程负责切换
            if self.current_key_index == failed_index:
                self.current_key_index += 1
                
                # 检查是否所有 Key 都死光了
                if self.current_key_index >= len(self.api_keys):
                    logger.error("🚨 弹尽粮绝！所有的 API Key 都已耗尽或被封禁！")
                    raise Exception("ALL_KEYS_EXHAUSTED")
                
                # 切换到下一个 Key
                self._init_active_client()

    def _clean_json_content(self, raw_text: str) -> str:
        """从 LLM 输出中提取 JSON（增强版：专治思考模型和语法错误）"""
        if "</think>" in raw_text:
            raw_text = raw_text.split("</think>")[-1]
            
        cleaned = re.sub(r"```(?:json)?|```", "", raw_text, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r',\s*]', ']', cleaned)
        cleaned = re.sub(r',\s*}', '}', cleaned)

        start_dict, end_dict = cleaned.find('{'), cleaned.rfind('}')
        start_list, end_list = cleaned.find('['), cleaned.rfind(']')

        def try_parse(chunk):
            try:
                json.loads(chunk)
                return True
            except json.JSONDecodeError:
                return False

        if start_dict != -1 and end_dict != -1:
            dict_str = cleaned[start_dict:end_dict + 1]
            if try_parse(dict_str): return dict_str

        if start_list != -1 and end_list != -1:
            list_str = cleaned[start_list:end_list + 1]
            if try_parse(list_str): return list_str

        if start_dict != -1 and end_dict != -1 and (start_list == -1 or start_dict < start_list):
            return cleaned[start_dict:end_dict + 1]
        if start_list != -1 and end_list != -1:
            return cleaned[start_list:end_list + 1]

        return cleaned

    async def chat(self, messages: List[Dict], temperature: float = 0.7, json_mode: bool = False) -> Union[str, Dict, List]:
        """核心生成接口 (内部自动处理 Key 的死亡和切换)"""
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 8192 
        }

        if json_mode:
            if self.backend_type == "tgi":
                kwargs["extra_body"] = {"repetition_penalty": 1.05}

        # 内部重试次数等于 Key 的总数，确保能轮询一遍
        max_internal_retries = len(self.api_keys) + 1 
        
        for _ in range(max_internal_retries):
            attempt_index = self.current_key_index 
            
            try:
                resp = await self.client.chat.completions.create(**kwargs)
                content = resp.choices[0].message.content

                if json_mode:
                    cleaned_str = self._clean_json_content(content)
                    if not cleaned_str:
                        logger.warning(f"⚠️ 无法提取 JSON。原始输出片段: {content[:100]}")
                        return {}
                    return json.loads(cleaned_str)

                return content

            except Exception as e:
                # 1. 获取完整错误信息并全部转为小写，防止大小写不匹配
                error_msg = str(e).lower()
                
                # 2. 扩充“阵亡关键词”词库 (涵盖限流、封号、欠费、无权限等各种花式报错)
                death_keywords = [
                    "429", "rate limit", "too many requests", 
                    "401", "403", "invalid token", "unauthorized", 
                    "insufficient", "quota", "balance", "arrears", 
                    "not enough", "api key"
                ]
                
                # 3. 如果命中任何一个关键词，或者属于特定的 HTTP 错误，果断切 Key
                if any(k in error_msg for k in death_keywords):
                    safe_key = f"{self.api_keys[self.current_key_index][:8]}***"
                    logger.warning(f"⚠️ Key [{safe_key}] 触发额度/封禁限制! 准备无缝切换下一个...")
                    
                    # 触发安全切换逻辑
                    await self._handle_key_death(attempt_index)
                    
                    # 停顿 1.5 秒，给新 Key 一点建立连接的缓冲时间
                    await asyncio.sleep(1.5)
                    continue  # 进入下一次循环，会自动使用新的 Key 重新发送请求
                    
                else:
                    # 如果真的不是 Key 的问题（比如大模型平台服务器炸了，或者返回了乱码）
                    logger.error(f"❌ LLMClient 发生非额度致命错误: {str(e)[:100]}")
                    raise e
                    
        raise Exception("内部重试次数耗尽，未能成功获取结果。")

    async def brainstorm(self, prompt: str, count: int = 1) -> List[Any]:
        """简化的生成接口"""
        try:
            system_prompt = f"You must output a JSON array containing exactly {count} items. Do not output any other text. Do NOT use double quotes inside strings."
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            result = await self.chat(messages, temperature=0.7, json_mode=True)

            if isinstance(result, list):
                return result
            elif isinstance(result, dict) and len(result) > 0:
                return next(iter(result.values()))
            return []
        except Exception as e:
            logger.error(f"❌ Brainstorm Error: {str(e)}")
            return []