"""
  @Author:jiexi
  @Time:2026/10/1
  @Desc:
"""
import asyncio
from typing import Optional

from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.conf.app_config import EmbeddingConfig, app_config


class EmbeddingClientManager:
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self.client: Optional[HuggingFaceEndpointEmbeddings] = None

    def init_client(self):
        self.client = HuggingFaceEndpointEmbeddings(model=f"http://{self.config.host}:{self.config.port}")


embedding_client_manager = EmbeddingClientManager(app_config.embedding)

if __name__ == "__main__":
    async def test():
        embedding_client_manager.init_client()

        result = await embedding_client_manager.client.aembed_query("atguigu")
        print(result)
        print(type(result))
        print(len(result))

        result = await embedding_client_manager.client.aembed_documents(["atguigu", "bigdata"])
        print(result)
        print(type(result))
        print(len(result))

    asyncio.run(test())
