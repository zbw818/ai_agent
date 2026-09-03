# AI Agent 学习项目

一个从零手写、基于**通义千问（DashScope OpenAI 兼容接口）**的命令行 ReAct 智能体。
项目源自一份 10 天 AI 应用开发学习计划（见文末学习路线），目标是**学习与实践兼顾**：
每一天产出一个可运行的机制，最终演进为带长期记忆的多 Agent 系统。

> 当前进度：Phase 1 核心机制完成（Day 0-3），Day 4 打磨中。

---

## 核心特性

- **ReAct 循环**：Thought → Action → Observation → Reflection 四段式推理轨迹，终端实时可视化
- **Function Calling 完整闭环**：模型生成工具意图 → 程序侧真实执行 → 结果回传 → 模型组装最终回答
- **反思机制（Reflection）**：每轮工具执行后发起一次**无工具**的独立调用，让模型自我反省并影响后续决策
- **迭代保险丝**：最多 10 轮工具循环，防止模型无限调用烧 token
- **显式思考（Thought）**：通过 system prompt 要求模型在调用工具前写出推理过程，黑盒变白盒
- **模块化架构**：入口 / 核心循环 / 工具 / 配置 / prompt 五层分离，依赖单向无循环
- **prompt 热更新**：prompt 存为独立文本文件，修改后无需重启程序，下一轮对话自动生效
- **rich 美化输出**：四色轨迹标签 + Panel 分轮分组 + Markdown 渲染最终回答

---

## 快速开始

### 环境要求

- Python 3.10+（开发环境为 3.12）
- macOS / Linux
- 一个 DashScope API Key（通义千问，OpenAI 兼容模式）

### 安装与运行

```bash
# 1. 配置 API Key 环境变量（切勿硬编码进代码）
export DASHSCOPE_API_KEY="你的key"

# 2. 创建并激活虚拟环境
cd ai_agent
python3 -m venv .venv
source .venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行（建议在真实终端中运行以获得彩色输出）
python main.py
```

输入 `exit` 或 `quit` 退出会话。

> **注意**：在 IDE 内置运行窗口中 rich 可能检测不到终端色彩能力而降级为纯文本，
> 请在 Terminal / iTerm2 等真实终端中运行。

---

## 项目架构

```
ai_agent/
├── main.py                  # 入口层：会话循环、history 维护、最终回答渲染
├── src/
│   ├── client.py            # 基础设施层：OpenAI 兼容客户端单例
│   ├── chat.py              # 核心层：ReAct 主循环 + 轨迹收集与渲染
│   └── reflect.py           # 核心层：反思调用（无工具的独立 API 请求）
├── tools/
│   └── tool_functions.py    # 能力层：工具函数实现 + JSON Schema + 名字→函数注册表
├── config/
│   ├── config_loader.py     # 配置层：Config 类 + 全局单例 agent_config
│   └── config.conf          # 短配置值：模型名、最大迭代次数
├── prompts/
│   ├── system_prompt.md     # 系统提示词（含 Thought 行为准则）
│   └── reflection_prompt.md # 反思提示词
├── memory/                  # 预留：Phase 2 长期记忆系统（ChromaDB）
└── requirements.txt         # 依赖清单
```

**依赖方向**（单向，无循环）：

```
main → src.chat → { src.reflect, src.client, tools, config }
```

---

## 核心机制说明

### 1. Function Calling 闭环（一次工具调用 = 两次 API 调用）

```
第 1 次调用：messages(含 user) + tools 说明书
        → 模型返回 tool_calls（意图：工具名 + JSON 字符串参数）
程序侧：  json.loads 解析参数 → 查注册表 → 真正执行函数
第 2 次调用：messages + 模型回复(带 tool_calls) + role="tool" 结果(带 tool_call_id)
        → 模型组装最终自然语言回答
```

关键契约：
- `role="tool"` 消息必须携带 `tool_call_id` 与调用配对（并行调用时的唯一凭证）
- 模型带 `tool_calls` 的回复必须**原样追加**进 messages（`messages.append(message)`）
- schema 与函数签名是一对契约，改一个必须同步改另一个

### 2. ReAct 轨迹示例（真实运行输出）

```
╭─ 第 1 轮推理 ────────────────────────────────────────────╮
│ 【Thought】：我需要先获取当前时间，然后提取小时数并乘以3。 │
│ 【工具调用】get_current_time({})                          │
│ 【Observation】：2026-09-02 15:07:07                      │
│ 【Reflection】：结果符合预期，小时数为15。15 × 3 = 45，    │
│                可直接回答。                               │
╰──────────────────────────────────────────────────────────╯
╭─ 助手 ───────────────────────────────────────────────────╮
│ 当前时间为15点，15 × 3 = 45。                              │
╰──────────────────────────────────────────────────────────╯
```

### 3. 反思机制的三个设计决策

| 决策 | 原因 |
|------|------|
| 反思调用**不传 `tools`** | 没有工具可用，模型只能输出文本反省，不会反省到一半又去调工具 |
| 反思指令用**临时列表**拼接，不进主 messages | 提问是一次性脚手架，只有反思答案值得留在上下文 |
| 反思结果以 **`assistant`** 角色追加 | 这是模型的"自我心声"；用 `user` 会被当成外部指令去"回应"，思维链断裂 |

实证价值：反思曾让模型主动跳过冗余工具调用（反省时顺手算完直接回答），
也曾在工具返回"文件不存在"时识别异常、诚实告知而非幻觉编造内容。

### 4. 保险丝机制

`for iteration in range(MAX_ITERATION)` 限定工具循环上限；
循环正常走完（模型始终不给最终回答）时返回熔断提示，而非无限烧 token。

---

## 工具清单

| 工具名 | 参数 | 用途 |
|--------|------|------|
| `get_current_time` | 无 | 获取当前时间（`%Y-%m-%d %H:%M:%S`） |
| `calculate` | `a`, `b`（number） | 两数求和（Day 4 计划升级为表达式计算） |
| `read_file` | `filepath`（string） | 读取文本文件，不存在时返回友好错误信息 |

工具扩展方式：在 `tools/tool_functions.py` 中新增函数 → 同步新增 schema →
注册进 `TOOLS_FUNCTIONS` 字典，三步缺一不可。

---

## 配置说明

| 配置项 | 位置 | 说明 |
|--------|------|------|
| `DASHSCOPE_API_KEY` | 环境变量 | API 密钥，**严禁硬编码或提交进 git** |
| `MODEL` | config/config.conf | 模型名，默认 qwen-plus |
| `MAX_ITERATION` | config/config.conf | 工具循环上限，默认 10 |
| system / reflection prompt | prompts/*.md | 纯文本热更新，改完无需重启 |

---

## 学习路线与进度

| 阶段 | 天数 | 内容 | 状态 |
|------|------|------|------|
| Phase 1 | Day 0 | 环境搭建 + ReAct 概念 | ✅ |
| | Day 1 | LLM 基础 + 多轮对话脚本 | ✅ |
| | Day 2 | Function Calling 机制 + 三工具实现 | ✅ |
| | Day 3 | ReAct 循环 + 显式 Thought + 反思机制 | ✅ |
| | Day 4 | 错误处理 + 上下文管理 + 项目打磨 | 🔄 进行中 |
| Phase 2 | Day 5-7 | 长期记忆系统（ChromaDB 向量检索） | ⬜ |
| | Day 8-10 | 记忆修正与遗忘 + 多 Agent 协作 | ⬜ |

核心学习资源：[ReAct 论文](https://arxiv.org/abs/2210.03629)、通义千问 DashScope 文档（Function Calling 章节）。

---

## 实践踩坑记录

开发过程中真实踩过的坑，均为 LLM 应用开发的典型问题：

**契约层（与模型/API 的接口）**
- API 参数名 `messages` 误写为 `message` → SDK 报"Missing required arguments"而非"未知参数"，排查先核对参数名拼写
- `role="tool"` 消息键名误写 `"tool_call.id"`（点号）→ 应为 `tool_call_id`（下划线），API 字段名一字不差
- JSON Schema 使用不存在的类型 `"list"` → 合法类型只有 string/number/integer/boolean/array/object
- schema 与函数签名不一致（单参数 vs 双参数）→ 契约两侧必须同步修改

**本地代码层**
- 变量遮蔽：`message` 先作列表后被模型响应对象覆盖 → 命名规范"复数=列表、单数=对象"
- rich 方括号冲突：模型输出含 `[...]` 被当样式标记 → 动态内容一律 `escape()`
- rich 自动高亮：日期/数字被 ReprHighlighter 意外上色 → `Console(highlight=False)`
- rich 静默降级：IDE 运行窗口无色彩 → 终端能力检测问题，用 `console.is_terminal` 排查

**认知层**
- 模型心算 vs 调工具的取舍由工具 schema 的能力边界决定：工具不匹配时模型会"该调不调"
- prompt 对错别字有容错，但复杂指令的错别字会悄悄改变理解且不报错——prompt 是合同文本

---

## 已知风险与 TODO

- [ ] `read_file` 无路径白名单：模型可读取用户目录下任意文件（本地学习工具可接受，生产化前必须加白名单）
- [ ] 工具执行无 `try/except`：畸形 JSON 参数 / 函数异常会导致程序崩溃（Day 4）
- [ ] history 无上限：长会话将撞上下文窗口（Day 4 实现滑动窗口截断）
- [ ] `calculate` 仅支持两数相加（Day 4 升级为白名单 eval 表达式计算）
- [ ] `chat.py` 循环逻辑与终端渲染耦合（Phase 2 前拆分出 ui 层）
- [ ] Phase 2：ChromaDB 长期记忆、记忆修正与遗忘、多 Agent 协作

---

## 技术栈

通义千问 qwen-plus（DashScope OpenAI 兼容模式）· openai SDK · rich · configparser · 纯手写 ReAct（无 Agent 框架）
