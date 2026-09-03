from config.config_loader import agent_config
from src.client import client


def reflection(messages):
	"""
	发起一次无工具的调用，让模型反省当前进展
	"""
	reflect_messages = messages + [
		{"role": "user", "content": agent_config.get_reflection_prompt()},
    ]

	response = client.chat.completions.create(
        model  = agent_config.get_model(),
        messages = reflect_messages,
    )

	return response.choices[0].message.content