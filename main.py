from rich.markdown import Markdown
from rich.console import Console
from rich.panel import Panel

from config import agent_config
from src.chat import chat


# 用 rich 美化轨迹输出，关掉自动高亮
console = Console(highlight=False)


def main():
	history = []
	console.print(Panel(
		"会话开启，输入 [bold red]exit[/bold red] 退出",
		title="[bold]AI Agent[/bold]",
		border_style="green",
		title_align="left",
	))
	while True:
		user_input = input("\n你: ").strip()
		if not user_input:
			continue
		if user_input.lower() in ("exit", "quit"):
			print("再见，期待再次对话！")
			break

		reply = chat(user_input, history)
		history.append({"role": "user", "content": user_input})
		history.append({"role": "assistant", "content": reply})

		history[:] = history[agent_config.get_max_history():]

		# # console.print()默认在输出末尾追加换行符, end = ""把结尾字符改成空串——不换行
		# console.print("[bold blue]助手[/bold blue]：", end ="")
		# console.print(Markdown(reply))
		console.print(Panel(Markdown(reply), title="[bold blue]助手[/bold blue]", border_style="blue", title_align="left"))


if __name__ == "__main__":
	main()	
		
