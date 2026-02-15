import json
import re
import time
import os
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from email.contentmanager import raw_data_manager

# ================= ⚙️ 全局配置区域 =================
# ================= ⚙️ 全局配置区域 =================
# 1. API Key 池 (本地 vLLM 通常不需要 Key，但为了兼容 SDK 请随便填一个字符串)
API_KEYS = ["local-vllm-no-key"]

# 2. 修改为 vLLM 默认地址和端口
# 如果你的 vLLM 部署在另一台机器，请将 localhost 换成对应的 IP
BASE_URL = "http://localhost:8000/v1"

# 3. 修改为你启动 vLLM 时定义的 --served-model-name
# 或者直接填写模型在本地的绝对路径
MODEL = "industrial-coder"

# 2. 文件路径
OUTPUT_FILE = "st_dataset_local_part.jsonl"
HISTORY_FILE = "st_dataset_r1.jsonl"
GOLDEN_FILE = "golden_prompts.json"

# 3. 运行参数 (🚀 本地模式可以更激进)
TARGET_TOTAL_COUNT = 200000
MAX_WORKERS = 100  # vLLM 的高并发能力很强，你可以根据显存情况增加线程数
MAX_RETRIES =  1  # 本地调用通常很稳定，重试次数可以减少
MAX_GOLDEN_EXAMPLES = 50
# ====================================================

try:
    from openai import OpenAI
except ImportError:
    print("❌ 错误: 缺少依赖库，请运行 -> pip install openai")
    exit()


class STDistillationEngine:
    def __init__(self):
        # 始终指向第 0 个 Key
        self.api_keys = API_KEYS
        self.current_key_index = 0
        self.key_lock = threading.Lock()

        self.existing_tasks = set()
        self.golden_examples = []

        # 线程锁
        self.file_lock = threading.Lock()
        self.console_lock = threading.Lock()
        self.examples_lock = threading.Lock()

        # 初始化
        self.load_all_history()
        self.load_golden_memory()

    def get_current_client(self):
        """获取当前激活的 Client"""
        with self.key_lock:
            current_key = self.api_keys[self.current_key_index]
        return OpenAI(api_key=current_key, base_url=BASE_URL)

    def switch_api_key(self, error_msg=""):
        """单 Key 模式下，这个函数仅用于打印'休息'日志"""
        with self.key_lock:
            # 不做切换，只打印
            print(f"\n⏳ [单Key死磕] 触发限制 ({error_msg})，全员暂停休息...", flush=True)

    def load_all_history(self):
        files_to_check = [HISTORY_FILE, OUTPUT_FILE]
        count = 0
        for fpath in files_to_check:
            if os.path.exists(fpath):
                with open(fpath, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            data = json.loads(line)
                            if "instruction" in data:
                                task = data['instruction'].split("for: ")[-1]
                                self.existing_tasks.add(task)
                                count += 1
                        except:
                            pass
        print(f"📂 已加载历史去重库: {count} 条", flush=True)

    def load_golden_memory(self):
        if os.path.exists(GOLDEN_FILE):
            try:
                with open(GOLDEN_FILE, 'r', encoding='utf-8') as f:
                    self.golden_examples = json.load(f)
                print(f"🏆 已加载黄金范例库: {len(self.golden_examples)} 个", flush=True)
            except:
                self.golden_examples = []

    def save_golden_memory(self):
        try:
            with open(GOLDEN_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.golden_examples, f,
                          ensure_ascii=False, indent=2)
        except:
            pass

    def clean_json_content(self, raw_text):
        cleaned = re.sub(r"```json|```", "", raw_text,
                         flags=re.IGNORECASE).strip()
        start = cleaned.find('{')
        end = cleaned.rfind('}')
        if start != -1 and end != -1:
            return cleaned[start:end+1]
        start_list = cleaned.find('[')
        end_list = cleaned.rfind(']')
        if start_list != -1 and end_list != -1:
            return cleaned[start_list:end_list+1]
        return ""

    def validate_st_code(self, code):
        if re.search(r"\b\w+\s*=\s*\w+;", code):
            return False, "Illegal assignment '='"
        required = ["FUNCTION_BLOCK", "END_FUNCTION_BLOCK", "VAR", "END_VAR"]
        if not all(k in code for k in required):
            return False, "Missing structure keywords"
        if "ARRAY[*]" in code.upper() or "ARRAY [*]" in code.upper():
            return False, "Dynamic arrays not supported"

        lines = [l.strip() for l in code.split('\n') if l.strip(
        ) and not l.strip().startswith('//') and not l.strip().startswith('(*')]
        if len(lines) > 5:
            valid_lines_count = sum(1 for l in lines if not any(k in l.upper() for k in [
                                    "FUNCTION", "VAR", "IF", "CASE", "FOR", "WHILE", "END_"]))
            semi_count = sum(1 for l in lines if l.endswith(';'))
            if valid_lines_count > 0 and (semi_count / valid_lines_count) < 0.5:
                return False, "Missing semicolons ';'"
        return True, "Passed"

    def generate_task_ideas(self, topic, count=10):
        client = self.get_current_client()
        prompt = f"""
You are an expert industrial automation engineer.
Brainstorm {count} DISTINCT, SPECIFIC, and INTERMEDIATE-LEVEL IEC 61131-3 Structured Text (ST) programming tasks related to: "{topic}".
Rules:
1. Cover real-world scenarios.
2. Output ONLY a JSON list of strings.
"""
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9
            )
            content = self.clean_json_content(
                response.choices[0].message.content)
            tasks = json.loads(content)
            return [t for t in tasks if isinstance(t, str) and len(t) > 10]
        except Exception as e:
            err_str = str(e)
            if "403" in err_str or "401" in err_str or "429" in err_str or "402" in err_str:
                # 打印休息日志，并执行避让
                self.switch_api_key(error_msg="额度/速率限制")
                time.sleep(20)  # 强制休息 20 秒
            elif "503" in err_str:
                print(f"🚧 [API 拥堵] 避让 5 秒...", flush=True)
                time.sleep(5)
            else:
                print(f"⚠️ [构思失败]: {err_str[:50]}...", flush=True)
            return []

    def evolve_task(self, base_task):
        """🔥 核心升级：Evol-Instruct 进化策略"""
        strategies = [
            # 1. 深度进化 (增加约束)
            f"Add a complex constraint to this task: The system must handle asynchronous sensor signal jitter and signal debouncing. Task: {base_task}",
            # 2. 广度进化 (增加功能)
            f"Rewrite this task to include a secondary objective: logging critical process data to a circular buffer for traceability. Task: {base_task}",
            # 3. 具体化 (特定场景)
            f"Make this task specific to the Pharmaceutical industry (GAMP5 standards), ensuring data integrity and audit trails. Task: {base_task}",
            # 4. 逻辑增强 (状态机)
            f"Increase reasoning complexity: Implement this using a robust State Machine pattern with error recovery states. Task: {base_task}"
        ]

        # 30% 的概率保持原样 (保留简单样本)，70% 的概率进化
        if random.random() > 0.7:
            return base_task

        prompt = random.choice(strategies)
        try:
            client = self.get_current_client()
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": f"{prompt}\nOutput ONLY the new task description string."}],
                temperature=0.8
            )
            return response.choices[0].message.content.strip()
        except:
            return base_task

    def ai_critique(self, task, code):
            """🕵️ 核心升级：LLM 逻辑审查"""
            prompt = f"""
    You are a Senior PLC Code Reviewer. Review this IEC 61131-3 Structured Text code.
    Task: {task}
    Code:
    {code}

    Checklist:
    1. Is the logic actually solving the task?
    2. Are there potential infinite loops (e.g., inside WHILE)?
    3. Are all used variables declared in VAR?
    4. Is it safe for industrial use?

    Output JSON ONLY: {{"passed": boolean, "reason": "short explanation"}}
    """
            try:
                client = self.get_current_client()
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1  # 审查需要严谨
                )
                content = self.clean_json_content(response.choices[0].message.content)
                return json.loads(content)
            except:
                return {"passed": True, "reason": "Reviewer Failed"}  # 审查挂了默认放行
            # 在 __init__ 中增加 self.dpo_file_lock = threading.Lock()

    def save_dpo_pair(self, task, chosen_code, rejected_code, critique):
        """💎 核心升级：保存偏好数据"""
        entry = {
            "prompt": f"Write ST code for: {task}",
            "chosen": chosen_code,
            "rejected": rejected_code,
            "metadata": {"critique": critique}
        }
        with self.file_lock:  # 复用文件锁
            with open("st_dpo_dataset.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    def worker_generate_code(self, raw_task):
        if raw_task in self.existing_tasks:
            return None
        task = self.evolve_task(raw_task)
        # 临时记录失败样本
        rejected_attempts = []
        example_text = ""
        with self.examples_lock:
            if self.golden_examples:
                ex_task, ex_code = random.choice(self.golden_examples)
                if len(ex_code) < 1500:
                    example_text = f"\n[Reference Example]\nTask: {ex_task}\nCode:\n{ex_code}\n------------------\n"

        strict_rules = """
STRICT CODING STANDARDS (MUST FOLLOW):
1. FLOAT SAFETY: NEVER compare REAL values directly (e.g. 'A=B'). Use epsilon (ABS(A-B)<0.001).
2. MATH SAFETY: Check division by zero.
3. COMPATIBILITY: Do NOT use dynamic arrays. Use fixed-size arrays.
4. TIME INTEGRATION: For physics, prefer 'CycleTime' input over system TIME().
5. FORMAT: Use 'FUNCTION_BLOCK', 'VAR', 'END_VAR'.
"""
        messages = [
            {"role": "system", "content": f"You are an expert IEC 61131-3 PLC programmer.{strict_rules}{example_text}"},
            {"role": "user", "content": f"Task: Write a FUNCTION_BLOCK for: \"{raw_task}\".\nRequirements: Strictly IEC 61131-3 ST syntax. Use ':=' for assignment.\nOutput: JSON ONLY (keys: thought, code)."}
        ]

        for attempt in range(MAX_RETRIES):
            try:
                client = self.get_current_client()

                response = client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    temperature=0.7
                )
                content = self.clean_json_content(
                    response.choices[0].message.content)
                data = json.loads(content)
                code = data.get('code', '')
                thought = data.get('thought', '')

                is_valid, error_msg = self.validate_st_code(code)

                if is_valid:
                    if 200 < len(code) < 2000:
                        with self.examples_lock:
                            if len(self.golden_examples) >= MAX_GOLDEN_EXAMPLES:
                                self.golden_examples.pop(0)
                            self.golden_examples.append((raw_task, code))
                            self.save_golden_memory()

                    return {
                        "instruction": f"Write an IEC 61131-3 Structured Text function block for: {raw_task}",
                        "input": "",
                        "output": code,
                        "metadata": {"thought": thought, "topic": "Generated", "retries": attempt}
                    }
                else:
                    review = self.ai_critique(task, code)

                    if review['passed']:

                        # 如果有失败记录，保存为 DPO 数据
                        if rejected_attempts:
                            self.save_dpo_pair(task, code, rejected_attempts[-1], "Syntax/Logic Error")

                        # 保存 SFT 数据 (原逻辑)
                        return {
                            "instruction": f"Write an IEC 61131-3 Structured Text function block for: {task}",
                            "output": code,
                            "metadata": {"review": review['reason'],
                                         "evolution": "evolved" if task != raw_task else "base"}
                        }
                    else:
                        # 审查不通过，打回重写
                        rejected_attempts.append(code)
                        messages.append({"role": "assistant", "content": code})
                        messages.append(
                            {"role": "user", "content": f"Code Review Failed: {review['reason']}. Please fix logic."})

            except Exception as e:
                err_str = str(e)
                if "403" in err_str or "401" in err_str or "429" in err_str or "402" in err_str:
                    print(f"🛑 [Limit] 触发限制，暂停 20 秒后重试...", flush=True)
                    time.sleep(20)  # 休息久一点
                elif "503" in err_str:
                    time.sleep(5)
                else:
                    break
        return None

    def run(self):
        domains = ["Motion Control", "Closed Loop Control", "Safety Logic", "Data Processing",
                   "Communication", "HMI Interaction", "String Manipulation", "File Handling", "Recipe Management"]
        industries = ["Packaging", "Water Treatment", "CNC", "HVAC", "Conveyor",
                      "Semiconductor", "Automotive", "Food & Bev", "Pharmaceutical"]
        complexities = ["Standard", "Robust w/ Error Handling",
                        "High Performance", "Using POINTERs", "State Machine"]
        constraints = ["use CASE statement", "use ARRAY iteration", "avoid floating point",
                       "use STRUCT", "handle sensor noise", "optimize cpu cycles"]

        print(f"🚀 [V13 Single-Key Aggressive] 单Key火力全开 | Target: {TARGET_TOTAL_COUNT} | Threads: {MAX_WORKERS}", flush=True)
        print(f"🔑 当前 Key: {API_KEYS[0][:15]}...", flush=True)
        print("="*60, flush=True)

        last_heartbeat = time.time()

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            while len(self.existing_tasks) < TARGET_TOTAL_COUNT:

                if time.time() - last_heartbeat > 30:
                    print(f"💓 [系统存活] 进度: {len(self.existing_tasks)}/{TARGET_TOTAL_COUNT} | 死磕中...", flush=True)
                    last_heartbeat = time.time()

                specific_topic = f"{random.choice(domains)} in {random.choice(industries)}, {random.choice(complexities)}, constraint: {random.choice(constraints)}"

                print(f"🧠 [构思中] 请求: {specific_topic[:40]}...", flush=True)

                new_tasks = self.generate_task_ideas(specific_topic, count=15)
                todo_tasks = [t for t in new_tasks if t not in self.existing_tasks]

                if not todo_tasks:
                    print(f"💤 暂无新题，冷却 2 秒...", flush=True)
                    time.sleep(2)
                    continue

                future_to_task = {executor.submit(
                    self.worker_generate_code, t): t for t in todo_tasks}

                for future in as_completed(future_to_task):
                    task_name = future_to_task[future]
                    try:
                        result = future.result()
                        if result:
                            with self.file_lock:
                                with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
                                    f.write(json.dumps(result, ensure_ascii=False) + "\n")
                                self.existing_tasks.add(task_name)
                                curr_len = len(self.existing_tasks)

                            retry_msg = f"(🔧{result['metadata']['retries']})" if result['metadata']['retries'] > 0 else ""
                            thought_text = result['metadata'].get('thought', '')
                            thought_preview = thought_text[:150].replace('\n', ' ') + "..." if thought_text else "No thought provided"

                            with self.console_lock:
                                print(f"✅ [{curr_len}/{TARGET_TOTAL_COUNT}] {task_name[:40]}... {retry_msg}", flush=True)
                                print(f"   └── 💭 思维: {thought_preview}", flush=True)

                    except Exception as e:
                        pass

                    if len(self.existing_tasks) >= TARGET_TOTAL_COUNT:
                        print(f"\n🎉 目标达成！已停止。数据保存在 {OUTPUT_FILE}", flush=True)
                        return


if __name__ == "__main__":
    engine = STDistillationEngine()
    engine.run()
