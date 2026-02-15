import yaml
import os


class ConfigManager:
    def __init__(self, config_path="config.yaml"):
        # 加载 YAML
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件未找到: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            self._cfg = yaml.safe_load(f)

    # --- Generation Section (对应你的片段) ---

    @property
    def model(self) -> str:
        # 获取 model，如果没有则默认 "industrial-coder"
        return self._cfg.get('generation', {}).get('model', 'industrial-coder')

    @property
    def base_url(self) -> str:
        return self._cfg.get('generation', {}).get('base_url', 'http://localhost:8000/v1')

    @property
    def max_concurrency(self) -> int:
        return self._cfg.get('generation', {}).get('max_concurrency', 10)

    @property
    def max_retries(self) -> int:
        return self._cfg.get('generation', {}).get('max_retries', 3)

    @property
    def api_key(self) -> str:
        # 本地 vLLM 通常不需要 Key，返回默认值即可
        # 如果是 OpenAI，这里可以从环境变量 os.getenv 读取
        return "EMPTY"

        # --- File Paths Section ---

    def get_path(self, key: str) -> str:
        """通用路径获取方法"""
        return self._cfg.get('file_paths', {}).get(key, f"data/{key}")

    @property
    def target_count(self) -> int:
        return self._cfg.get('project', {}).get('target_count', 1000)

    @property
    def output_path(self) -> str:
        return self._cfg.get('file_paths', {}).get('output_path', 'st_dataset_local_part.jsonl')
    @property
    def dpo_file(self) -> str:
        return self._cfg.get('file_paths', {}).get('dpo_file', 'st_dpo_dataset.jsonl')
    @property
    def golden_file(self) -> str:
        return self._cfg.get('file_paths', {}).get('golden_file', 'st_golden_dataset.json')
    @property
    def history_file(self) -> str:
        return self._cfg.get('file_paths', {}).get('history_file', 'st_history_dataset.json')