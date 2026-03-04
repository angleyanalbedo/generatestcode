# Industrial-ST-Distiller 🚀

**Industrial-ST-Distiller** 是一个专为工业自动化领域设计的合成数据生成、蒸馏与**多语言转换**框架。它利用大语言模型（LLM）的高级推理能力，自动化地生成、进化并校验 IEC 61131-3 标准下的 **结构化文本 (ST)** 代码，并具备将其无损转化为**功能块图 (FBD)** 和**梯形图 (LD)** 的能力。

本项目的核心目标是构建高质量的 SFT（有监督微调）和 DPO（偏好优化）数据集，用于训练更懂工业控制逻辑的小型化、垂直化模型（如 **ST-Coder-14B**）。

---

## ✨ 核心特性

* **异步协程驱动**：基于 `asyncio` 和 `Semaphore` 限制，实现极致的并行推理性能，完美压榨 vLLM 推理后端。
* **组件化架构**：遵循“组合优于继承”原则，将调度、存储与提示词策略彻底解耦。
* **Evol-Instruct 策略**：内置任务进化机制，自动将简单的指令转化为复杂的工业场景需求。
* **魔鬼级语法校验**：
* **实时校验**：利用正则进行初步结构拦截。
* **深度质检 (Matiec)**：基于 OpenPLC 的工业级编译器，确保生成的代码 100% 物理可用。


* **全能型 AST 引擎 (ANTLR4 驱动)**：
* 基于强类型的 `dataclass` 构建高精度抽象语法树，支持复杂表达式、多维数组与多 POU（程序组织单元）全量扫描。
* 内置无缝兼容层（`ast_to_dict`），确保新版 AST 与旧版数据流分析工具的完美衔接。


* **跨语言图形化转换 (ST -> FBD -> LD)**：
* 遵循 **IEC 61131-10** XML 标准，突破性地实现了 ST 代码向图形化语言的降维映射。
* **FBDXmlUnparser**：自动分配图元 ID 与坐标，生成合规的连线网络。
* **LDXmlUnparser**：支持纯 XML 层面的极速图元翻译（触点、线圈、电源线自动缝合）。


* **自动 DPO 构造**：通过捕获模型在自我修正过程中的失败样本，自动配对生成 `Chosen/Rejected` 数据。

---

### 💡 核心设计思想的转变

> **Validation vs. Manipulation (校验与操作解耦)**：
> 我们彻底剥离了“代码校验”与“代码操作”的职责。底层 AST (`ASTBuilder`) 不再用于严苛的对错判定，而是专注于它最擅长的代码重构、依赖提取与**跨语言图形渲染**；真伪的判定权则全部交还给真正的工业编译器 (`MatiecValidator`) 和 XML 标准校验器 (`IEC61131Validator`)。

---

## 🏗️ 软件架构

### 核心架构组件 (Architecture Components)

* **ConfigManager**: 统一管理 YAML 配置、模型参数与文件路径，支持多后端的动态路由。
* **PromptManager**: 负责 Jinja2 模板渲染，实现提示词版本化管理与 Few-shot 动态组装。
* **IOHandler**: 处理异步文件写入、内存去重索引，并严格区分**业务逻辑失败**与**系统运行异常**。
* **STValidator (多重校验引擎)**:
* **FastValidator**: 提供极速的启发式结构对齐检查。
* **MatiecValidator**: 集成 `iec2c` 编译器，执行严格的作用域与类型推导检查，输出真实报错用于 RL/DPO 训练。
* **IEC61131Validator**: 严格的 XSD 校验器，确保生成的 FBD/LD XML 结构完美合规。


* **AST 解析与操作引擎**:
* **STAstBuilder**: 基于 ANTLR4 构建的底层语法树分析器。
* **DependencyAnalyzer**: 独立的 AST 数据依赖分析器，精准提取读/写变量集合。
* **STUnparser**: 标准缩进的代码还原器。
* **FBDXmlUnparser / LDXmlUnparser**: 工业级图形化 XML 渲染引擎。
* **FbdToLdConverter**: FBD转LD引擎。


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

### 3. 运行核心引擎

```python
import asyncio
from src.distillation.distillation_engine import AsyncSTDistillationEngine
from prompt_manager import PromptManager
from config_manager import ConfigManager
import platform

if __name__ == "__main__":
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
3. **Generate**: 结合 Golden Memory 生成 ST 代码。
4. **Validate**: 经过 Matiec 编译校验，失败记录为 **Rejected**，成功记录为 **Chosen**。
5. **Transform (可选)**: 将通过校验的 ST 代码输入 Unparser，生成对应的 FBD 和 LD XML 文件。

---

## 📅 TODO / 路线图

项目正处于高速迭代中：

* [x] **Semantic Analyzer**: 增加更严格的类型检查与未定义变量扫描。
* [x] **MatIEC Support**: 增加 MatIEC 作为编译器检查。
* [x] **Multi-Backend Support**: 增加对 Hugging Face TGI 和本地 Llama.cpp 的原生支持。
* [x] **ST to FBD/LD Pipeline**: 完成 IEC 61131-10 标准下的图形化代码无损转换。
* [ ] **STSlicer (代码切片器)**：持续优化基于数据流的程序切片，提取关键逻辑片段以提升长代码理解力。

---

## 📈 模型与数据集

* **数据集格式**:
* SFT 与 DPO 数据集提供标准 JSONL 格式。
* **许可协议**: 遵循 **CC BY-NC 4.0** 协议，仅供教育与非商业用途使用，商业用途需另行授权。



---

## 🧰 工具链 (Toolchain)

`tools/` 目录包含了一系列用于数据清洗、批量格式转换和微调准备的工程化脚本。

| 工具名称 | 核心功能 | 使用场景 |
| --- | --- | --- |
| **`clean_st_matiec.py`** | **[核心]** 基于 Matiec 编译器的工业级双漏斗数据清洗。 | 离线处理 ST 数据集，分流 `golden` 与 `matiec_error`。 |
| **`augment_dataset.py`** | **[核心]** 基于 AST 与数据依赖分析的无损 ST 代码增强（乱序、混淆）。 | 扩充 SFT 训练集，提升泛化能力。 |
| **`test_st_to_fbd_pipeline.py`** | 批量执行 ST -> FBD XML 的转换与 XSD 合规性校验。 | 自动化测试并生成 FBD 语料库。 |
| **`convert_fbd_to_ld.py`** | 基于 XML 标签映射，极速将 FBD 转换为 LD（梯形图）。 | 图形化数据集的一键扩容。 |
| **`check_json_schema.py`** | 快速扫描 `.jsonl` / `.json`，校验字段完整性。 | 数据集入库前的值守校验。 |
| **`fix_json_schema.py`** | 自动修复因 LLM 截断导致的 JSON 结构损坏。 | 抢救大批量生成任务中的损坏数据。 |

> **⚠️ 运行依赖提醒**:
> 运行编译清理强依赖 OpenPLC 的 `iec2c`。请确保 `iec2c.exe` 及其 `lib/` 文件夹路径配置正确。图形化转换依赖 `IEC61131_10_Ed1_0.xsd` 校验文件。

---

## 📄 开源协议

* **代码框架**: [MIT License](https://www.google.com/search?q=MIT+License+text)
* **衍生数据集**: [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)

## Credit

* [angleyanalbedo/ST_Slicing](https://www.google.com/search?q=https://github.com/angleyanalbedo/ST_Slicing) - 核心切片与 AST 灵感来源
* [AICPS/PLCBEAD_PLCEmbed](https://github.com/AICPS/PLCBEAD_PLCEmbed)
* [blank734](https://github.com/blank374) - 蒸馏部分基础框架

---
