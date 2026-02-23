# Industrial-ST-Distiller 🚀

**Industrial-ST-Distiller** 是一个专为工业自动化领域设计的合成数据生成与蒸馏框架。它利用大语言模型（LLM）的高级推理能力，自动化地生成、进化并校验 IEC 61131-3 标准下的 **结构化文本 (ST)** 代码。

本项目的核心目标是构建高质量的 SFT（有监督微调）和 DPO（偏好优化）数据集，用于训练更懂工业控制逻辑的小型化、垂直化模型。

---

## ✨ 核心特性

* **异步协程驱动**：基于 `asyncio` 和 `Semaphore` 限制，实现极致的并行推理性能，完美压榨 vLLM 推理后端。
* **组件化架构**：遵循“组合优于继承”原则，将调度、存储与提示词策略彻底解耦。
* **Evol-Instruct 策略**：内置任务进化机制，自动将简单的指令转化为复杂的工业场景需求。
* **魔鬼级语法校验**：
* **实时校验**：利用正则进行初步结构拦截。
* **深度质检 (Lark)**：基于 `Lark` 库构建 ST Parser，实现变量定义域检查与嵌套闭合校验。


* **自动 DPO 构造**：通过捕获模型在自我修正过程中的失败样本，自动配对生成 `Chosen/Rejected` 数据。

---

## 🏗️ 软件架构

项目采用模块化设计，确保各组件独立运行且易于扩展：

* **ConfigManager**: 统一管理 YAML 配置、模型参数与文件路径。
* **PromptManager**: 负责 Jinja2 模板渲染，实现提示词版本化管理。
* **IOHandler**: 处理异步文件写入、内存去重索引以及 Golden Memory 维护。
* **STParser**: 基于 Lark 的语法解析核心，负责将代码转化为 AST（抽象语法树）。

---

## 🚀 快速开始

### 1. 环境准备

```bash
uv sync

```

### 2. 配置 `config.yaml`

```yaml
generation:
  model: "industrial-coder"
  base_url: "http://localhost:8000/v1"
  max_concurrency: 100
  max_retries: 3

file_paths:
  output_file: "data/st_sft.jsonl"
  dpo_file: "data/st_dpo.jsonl"
  history_file: "data/history.jsonl"
  golden_file: "config/golden_memory.json"

```

### 3. 运行引擎

```python
import asyncio
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
    engine = AsyncSTDistillationEngine(config, prompt_manager)
    asyncio.run(engine.run())

```

---

## 🛠️ 数据生成流水线

1. **Brainstorm**: 根据工业领域构思初始任务。
2. **Evolve**: 增加约束（如：信号抖动、错误恢复）进化任务。
3. **Generate**: 结合 Golden Memory 生成代码。
4. **Validate**: 语法校验失败记录为 **Rejected**，成功记录为 **Chosen**。

---

## 📅 TODO / 路线图

项目正处于高速迭代中，以下功能正在开发：

* [ ] **STRewriter (代码重构器)**：基于 Lark AST 实现代码变换（如 IF 转 CASE、变量混淆），实现数据量的指数级增强。
* [ ] **STSlicer (代码切片器)**：实现基于数据流的程序切片，用于提取关键逻辑片段，提升模型对长代码的理解力。
* [x] **Semantic Analyzer**: 增加更严格的类型检查与未定义变量扫描。
* [ ] **Multi-Backend Support**: 增加对 Hugging Face TGI 和本地 Llama.cpp 的原生支持。

---

## 📈 数据集格式

### SFT 数据

```json
{
  "instruction": "Write an ST function block for...",
  "output": "FUNCTION_BLOCK ...",
  "metadata": {"thought": "...", "evolution": "evolved"}
}

```

### DPO 数据

```json
{
  "prompt": "Write ST code for: ...",
  "chosen": "FUNCTION_BLOCK ... (Correct)",
  "rejected": "FUNCTION_BLOCK ... (Error)",
  "metadata": {"error": "Missing END_VAR"}
}

```

---

## 📄 开源协议

[MIT License](https://www.google.com/search?q=MIT+License+text)

---

