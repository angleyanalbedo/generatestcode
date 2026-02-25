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
* ### 💡 核心设计思想的转变 


> **Validation vs. Manipulation (校验与操作解耦)**：
> 我们彻底剥离了“代码校验”与“代码操作”的职责。Lark AST (`STParser`) 不再用于严苛的对错判定（因为容易漏判或误杀），而是专注于它最擅长的代码重构与依赖分析；真伪的判定权则全部交还给真正的工业编译器 (`MatiecValidator`)。


---

## 🏗️ 软件架构

### 更新后的核心架构组件 (Architecture Components)

* **ConfigManager**: 统一管理 YAML 配置、模型参数与文件路径，支持多后端的动态路由。
* **PromptManager**: 负责 Jinja2 模板渲染，实现提示词版本化管理与 Few-shot 动态组装。
* **IOHandler**: 处理异步文件写入、内存去重索引，并严格区分**业务逻辑失败 (DataOps/DPO 负样本挖掘)** 与**系统运行异常 (DevOps 监控)**，实现数据的颗粒度归档。
* **STValidator (双漏斗校验引擎)**: 数据质量的终极守门员。
* **FastValidator**: 提供极速的启发式正则与结构对齐检查，秒级拦截残缺代码。
* **MatiecValidator**: 深度集成 OpenPLC (`iec2c`) 工业级 C++ 编译器，执行严格的作用域与类型推导检查，确保放行的代码 100% 物理可用，并输出真实编译器报错用于 RL/DPO 训练。
* **STParser (AST 操作引擎)**: 基于 Lark 构建的底层语法树分析器。现已专职负责代码的解构与重组，包含数据依赖分析 (`STSlicer` 核心逻辑切片) 与无损数据增强 (`STRewriter` 乱序重写)。

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
* [x] **MatIEC Support**: 增加MatIEC作为编译器检查。
* [x] **Multi-Backend Support**: 增加对 Hugging Face TGI 和本地 Llama.cpp 的原生支持。

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
## 🧰 工具链 (Toolchain)

`tools/` 目录包含了一系列用于数据清洗、格式校验和模型微调准备的工程化脚本。

| 工具名称 | 核心功能 | 使用场景 |
| :--- | :--- | :--- |
| **`clean_st_matiec.py`** | **[核心]** 基于 Matiec 编译器的工业级双漏斗数据清洗工具。 | 离线处理爬取的 ST 数据集。将数据按质量分流为 `golden` (SFT 级) 和 `matiec_error` (DPO 负样本级)。 |
| **`check_json_schema.py`** | 快速扫描 `.jsonl` / `.json` 数据集，校验字段完整性（Instruction/Output 等）。 | 数据集入库前的值守校验。 |
| **`fix_json_schema.py`** | 自动尝试修复因 LLM 截断或转义错误导致的 JSON 结构损坏。 | 抢救大批量生成任务中的损坏数据。 |
| **`convert_deepseek_format.py`** | 将标准化 ST 数据集转换为 DeepSeek / LLaMA 等主流大模型的微调（SFT）指令格式。 | 模型训练前的数据格式准备。 |

> **⚠️ 注意 (关于 Matiec 编译器)**: 
> 运行 `clean_st_matiec.py` 强依赖 OpenPLC 的 `iec2c` 编译器。请确保已将 `iec2c.exe` 及其配套的 `lib/` 标准库文件夹放置在正确路径，或通过 `-I` 参数指定库位置。
---

## 📄 开源协议

[MIT License](https://www.google.com/search?q=MIT+License+text)

---

