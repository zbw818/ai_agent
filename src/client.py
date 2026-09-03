from openai import OpenAI
import os


client = OpenAI(
	api_key = os.environ["DASHSCOPE_API_KEY"],
	base_url = "https://ws-x39l6wnx07rbkm2m.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
)