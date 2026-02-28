import yaml
import os
from dotenv import load_dotenv

load_dotenv(override=True)

class ConfigManager:
    def __init__(self, config_path="config.yaml"):
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件未找到: {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            self._cfg = yaml.safe_load(f)

    @property
    def model(self) -> str:
        return os.getenv("MODEL_NAME", self._cfg.get('generation', {}).get('model', 'industrial-coder'))

    @property
    def base_url(self) -> str:
        return os.getenv("API_BASE_URL", self._cfg.get('generation', {}).get('base_url', 'http://localhost:8000/v1'))

    @property
    def max_concurrency(self) -> int:
        return int(os.getenv("MAX_CONCURRENCY", self._cfg.get('generation', {}).get('max_concurrency', 10)))

    @property
    def max_retries(self) -> int:
        return int(os.getenv("MAX_RETRIES", self._cfg.get('generation', {}).get('max_retries', 3)))

    @property
    def api_keys(self) -> list:
        raw_keys = os.getenv("API_KEYS", "")
        if raw_keys:
            return [k.strip() for k in raw_keys.split(",") if k.strip()]
        return [os.getenv("OPENAI_API_KEY", "EMPTY")]

    @property
    def backend_type(self) -> str:
        return self._cfg.get('backend', {}).get('type', 'openai')

    @property
    def target_count(self) -> int:
        return int(os.getenv("TARGET_COUNT", self._cfg.get('project', {}).get('target_count', 1000)))
        
    @property
    def use_strict(self) -> bool:
        return str(os.getenv("USE_STRICT_VALIDATION", "True")).lower() == "true"

    def get_path(self, key: str) -> str:
        return self._cfg.get('file_paths', {}).get(key, f"data/{key}")

    @property
    def output_file(self) -> str: return self.get_path('output_file')
    @property
    def dpo_file(self) -> str: return self.get_path('dpo_file')
    @property
    def golden_file(self) -> str: return self.get_path('golden_file')
    @property
    def history_file(self) -> str: return self.get_path('history_file')
    @property
    def failed_file(self) -> str: return self.get_path('failed_file')
    @property
    def error_log_file(self) -> str: return self.get_path('error_log_file')