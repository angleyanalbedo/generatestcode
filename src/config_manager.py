import os
import yaml
from dotenv import load_dotenv

# 加载 .env 文件到环境变量
load_dotenv()


class ConfigManager:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.cfg = yaml.safe_load(f)

    @property
    def api_key(self):
        # 优先从环境变量读取，安全！
        return os.getenv("OPENAI_API_KEY", "local-no-key")

    @property
    def base_url(self):
        return self.cfg['generation']['base_url']

    @property
    def model(self):
        return self.cfg['generation']['model']

    @property
    def max_concurrency(self):
        return self.cfg['generation']['max_concurrency']
    @property
    def output_file(self):
        return self.cfg['generation']['output_file']
    @property
    def dpo_file(self):
        return self.cfg['generation']['dpo_file']
    @property
    def gloden_file(self):
        return self.cfg['generation']['gloden_file']


    # ... 其他属性封装 ...
    def get_path(self, key):
        return self.cfg['project'].get(key, "")