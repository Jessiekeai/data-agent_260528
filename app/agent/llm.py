import os

from langchain.chat_models import init_chat_model

from app.conf.app_config import app_config

# llm = init_chat_model(
#     model="qwen3.7-max",                                # 通义千问最新旗舰模型
#     model_provider="openai",                             # 使用 OpenAI 兼容接口
#     api_key=os.getenv("aliQwen-api"),                    # 密钥存本地环境变量
#     base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",  # 阿里云接入点
# )

llm = init_chat_model(
    model=app_config.llm.model_name,                                # 通义千问最新旗舰模型
    model_provider="openai",                             # 使用 OpenAI 兼容接口
    api_key=app_config.llm.api_key,                    # 密钥存本地环境变量
    base_url="https://api.deepseek.com",  # 阿里云接入点
)


if __name__ == "__main__":
    response = llm.stream("华北地区销售总额")
    print(f"响应类型：{type(response)}")  # 响应类型：<class 'generator'>
    # 流式打印结果
    for chunk in response:
        # 刷新缓冲区 (无换行符，缓冲区未刷新，内容可能不会立即显示)
        print(chunk.content, end="", flush=True)
    print("\n")