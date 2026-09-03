import datetime
import ast
import os


# 白名单：只允许数学表达式节点
_ALLOWED_NODES = (
	ast.Expression,		# 顶层表达式容器
	ast.BinOp,			# 二元运算 + - * /
	ast.UnaryOp,		# 一元运算 -x, +x
	ast.Constant,		# 数字常量（Python 3.8+）
	# 运算符
	ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
	# 一元运算符
	ast.USub, ast.UAdd,
	ast.Call,			# 函数调用（如果允许 sin/cos 等）
	ast.Name,			# 变量名引用（用于允许 math 函数名）
	ast.Load,
)
_ALLOWED_FUNCS = {"abs": abs, "round": round, "min": min, "max": max, "pow": pow}


def get_current_time():
	return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def calculate(expression: str):
	"""
	安全计算数学表达式：AST白名单检验后执行
	字符串表达式 → AST解析 → 白名单校验 → 安全求值
	"""
	# 将字符串解析为抽象语法树AST，mode="eval"表示只允许单个表达式
	tree = ast.parse(expression, mode="eval")

	# 递归遍历 AST 中的每一个节点，包括嵌套的子节点，进行白名单校验
	for node in ast.walk(tree):
		# 节点类型白名单校验
		if not isinstance(node, _ALLOWED_NODES):
			raise ValueError(f"不允许的语法：{type(node).__name__}")

		# Constant 节点的值只允许 int/float（挡住字符串常量如 'a'*3）
		if isinstance(node, ast.Constant) and not isinstance(node.value, (int, float)):
			raise ValueError(f"不允许的常量类型：{type(node.value).__name__}，仅允许int/float")

		# Name 节点只允许出现在 _ALLOWED_FUNCS 里
		if isinstance(node, ast.Name) and node.id not in _ALLOWED_FUNCS:
			raise ValueError(f"不允许的变量名：{node.id!r}")

	# 安全求值（三层防护）：
	# compile(tree, ...)：复用已校验过的AST，避免重新解析字符串
	# {"__builtins__": {}}：清空内置命名空间，使 open、exec、__import__ 等全部不可用
	# _ALLOWED_FUNCS：作为局部命名空间，只暴露允许的函数
	return eval(compile(tree, "<expr>", "eval"), {"__builtins__": {}}, _ALLOWED_FUNCS)

def read_file(filepath):
	if not os.path.exists(filepath):
		return f"错误：文件不存在: {filepath}"
	with open(filepath, "r") as f:
		return f.read()


TOOLS_FUNCTIONS = {
	"get_current_time": get_current_time,
	"calculate": calculate,
	"read_file": read_file,
}


tools = [
	{
		"type": "function",
		"function": {
			"name": "get_current_time",
			"description": "当你想获取当前的时间时非常有用。",
			"parameters": {}
		}
	},
	{
		"type": "function",
		"function": {
			"name": "calculate",
			"description": "当你需要计算数学表达式时非常有用。支持 + - * / // % ** 运算和 abs/round/min/max/pow 函数。",
			"parameters": {
				"type": "object",
				"properties": {
					"expression": {"type": "string", "description": "数学表达式字符串，比如 '(1+2)*4'、'3**7'、'abs(-5)'"}
				},
				"required": ["expression"]
			}
		}
	},
	{
		"type": "function",
		"function": {
			"name": "read_file",
			"description": "当你想读取指定文件内容时非常有用。需要提供文件路径作为参数。",
			"parameters": {
				"type": "object",
				"properties": {
					"filepath": {
						"type": "string",
						"description": "文件路径，比如/home/main.py。"
					}
				},
				"required": ["filepath"]
			}
		}
	}
]
