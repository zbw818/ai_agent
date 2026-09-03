import json

from tools.tool_functions import TOOLS_FUNCTIONS


def tool_executor(name: str, arguments: str) -> str:
    """
    执行工具调用，任何异常都会被转化为可读的错误字符串返回
    """
    function = TOOLS_FUNCTIONS.get(name)
    if function is None:
        return f"【tool_executor】错误：未知工具：{name}，可用工具：{list(TOOLS_FUNCTIONS.keys())}"

    try:
        args = json.loads(arguments)
        return str(function(**args))
    except json.JSONDecodeError as json_decode_error:
        return f"【tool_executor】错误：参数{arguments} JSON解析失败，请检查参数格式后重新调用。具体报错：{json_decode_error}"
    except TypeError as type_error:
        return f"【tool_executor】错误：参数{arguments}不匹配，请确认参数类型或数量无误。具体报错：{type_error}"
    except Exception as err:
        return f"【tool_executor】错误：工具调用出错。具体报错：{type(err).__name__}: {err}"
