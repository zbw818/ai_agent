from rich.console import Console
from rich.markup import escape
from rich.panel import Panel

from tools.tool_functions import tools
from tools.tool_executor import tool_executor
from config.config_loader import agent_config
from src.reflect import reflection
from src.client import client


# 用 rich 美化轨迹输出，关掉自动高亮
console = Console(highlight=False)


def chat(user_message: str, history: list) -> str:
    """
    ReAct 主循环 + 轨迹收集与渲染
    """
    messages = [
        {"role": "system", "content": agent_config.get_system_prompt()},
    ]
    messages.extend(history)
    messages.append(
        {"role": "user", "content": user_message}
    )

    for iteration in range(agent_config.get_max_iteration()):
        # 本轮轨迹收集器
        trace_lines = []

        response = client.chat.completions.create(
            model=agent_config.get_model(),
            messages=messages,
            tools=tools,
        )
        message = response.choices[0].message

        # 分支一：模型不调用工具
        if not message.tool_calls:
            return message.content

        # 分支二：模型调用工具
        # 模型可能在content写入了思考过程（行为准则作用）
        thought = message.content or "(模型未输出思考)"  # content可能为None，必须兜底机制
        trace_lines.append(f"[bold yellow]【Thought】[/bold yellow]：{escape(thought)}")

        # 把模型待tool_calls的回复原样留存
        messages.append(message)

        # 遍历工具调用
        for tool_call in message.tool_calls:
            name = tool_call.function.name
            arguments = tool_call.function.arguments
            trace_lines.append(f"[bold cyan]【工具调用】[/bold cyan] [cyan]{escape(name)}({escape(arguments)})[/cyan]")

            # 工具调用
            result = tool_executor(name, arguments)

            trace_lines.append(f"[bold green]【Observation】[/bold green]：{escape(result[:100])}")  # 截断长结果，刷屏保护
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })

        # 调用 reflect()，打印 [Reflection]，并把反省内容以 assistant 角色追加进 messages
        reflection_content = reflection(messages)
        trace_lines.append(f"[bold magenta]【Reflection】[/bold magenta]：{escape(reflection_content)}")
        messages.append({
            "role": "assistant",
            "content": reflection_content
        })

        # 本轮轨迹整块渲染
        console.print(Panel(
            "\n".join(trace_lines),
            title=f"[bold]第 {iteration + 1} 轮推理[/bold]",
            border_style="yellow",
            title_align="left",
        ))

    # for 循环正常走完 = 模型迭代了 10 轮还没给最终答案 → 保险丝熔断
    return "⚠️达到最大迭代次数，任务未完成"
