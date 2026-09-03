import configparser
import os


class Config:
    """
    专门用于加载和管理应用程序配置的类
    """

    def __init__(self, config_path="config.conf"):
        self.config_path = config_path
        self.parser = configparser.ConfigParser()

        self.current_path = os.path.dirname(os.path.abspath(__file__))

        # 加载配置文件
        self._load_config()

    def _load_config(self):
        """
        内部方法：读取文件
        """
        self.config_path = os.path.abspath(os.path.join(self.current_path, 'config.conf'))
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"找不到配置文件{self.config_path}，请检查路径")

        self.parser.read(self.config_path, encoding="utf-8")

    def _read_prompt(self, filename: str) -> str:
        """
        从 prompts/ 目录读取纯文本 prompt
        """
        prompts_dir = os.path.join(os.path.dirname(self.current_path), "prompts")
        path = os.path.join(prompts_dir, filename)

        if not os.path.exists(path):
            raise FileNotFoundError(f"找不到 prompt 文件：{path}")

        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()

    def get_model(self) -> str:
        # 如果 conf 里没有这个参数，这里会直接抛出清晰的异常，不会污染其他参数
        return self.parser.get('agent', 'MODEL', fallback='qwen-plus')

    def get_max_iteration(self) -> int:
        # 如果 conf 里没有这个参数，这里会直接抛出清晰的异常，不会污染其他参数
        return self.parser.getint('agent', 'MAX_ITERATION', fallback=10)

    def get_max_history(self) -> int:
        # 如果 conf 里没有这个参数，这里会直接抛出清晰的异常，不会污染其他参数
        return self.parser.getint('agent', 'MAX_HISTORY', fallback=20)

    def get_system_prompt(self) -> str:
        return self._read_prompt("system_prompt.md")

    def get_reflection_prompt(self) -> str:
        return self._read_prompt("reflection_prompt.md")


agent_config = Config()