import yaml
import random
from jinja2 import Template


class PromptManager:
    def __init__(self, config_path="prompts.yaml"):
        self.config_path = config_path
        self.load_config()

    def load_config(self):
        """加载或重载配置文件"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.data = yaml.safe_load(f)

    def render(self, key, **kwargs):
        """通用渲染函数"""
        template_str = self.data.get(key, "")
        if not template_str:
            return f"[Error: Prompt key '{key}' not found]"
        template = Template(template_str)
        return template.render(**kwargs)

    def get_system_prompt(self, golden_example=None):
        """获取 System Prompt，支持动态插入 Few-Shot"""
        return self.render("system_prompt", golden_example=golden_example)

    def get_evolution_prompt(self, base_task):
        """随机选择一种进化策略"""
        strategies = self.data.get("evolution_strategies", [])
        if not strategies:
            return base_task

        # 30% 概率不进化 (可以在 yaml 里配置这个概率吗？当然可以)
        if random.random() > 0.7:
            return base_task

        selected_strategy = random.choice(strategies)
        return Template(selected_strategy).render(task=base_task)

    def get_generation_messages(self, task, golden_example=None):
        """组装完整的请求 Messages"""
        return [
            {"role": "system", "content": self.get_system_prompt(golden_example)},
            {"role": "user", "content": self.render("generation_template", task=task)}
        ]

    def get_critique_messages(self, task, code):
        """组装审查 Messages"""
        return [
            {"role": "user", "content": self.render("critique_template", task=task, code=code)}
        ]

    def get_brainstorm_messages(self, topic, count=10):
        """组装头脑风暴 Messages"""
        return [
            {"role": "user", "content": self.render("brainstorm_template", topic=topic, count=count)}
        ]