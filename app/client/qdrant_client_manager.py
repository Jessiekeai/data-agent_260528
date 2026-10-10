"""
  @Author:jiexi
  @Time:2026/10/1
  @Desc:
"""
import asyncio
from typing import Optional

from qdrant_client import AsyncQdrantClient, models

from app.conf.app_config import QdrantConfig, app_config


class QdrantClientManager:
    def __init__(self, config: QdrantConfig):
        self.config = config
        self.client: Optional[AsyncQdrantClient] = None

    def _get_url(self):
        return f"http://{self.config.host}:{self.config.port}"

    def init_client(self):
        self.client = AsyncQdrantClient(self._get_url())

    async def close(self):
        await self.client.close()


qdrant_client_manager = QdrantClientManager(app_config.qdrant)

if __name__ == "__main__":
    async def test():
        qdrant_client_manager.init_client()

        client = qdrant_client_manager.client

        collection_name = "my_collection"

        # Create a collection
        if await client.collection_exists(collection_name):
            await client.delete_collection(collection_name)
        await client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=10, distance=models.Distance.COSINE),
        )

        # Insert a vector
        from random import random
        await client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=i,
                    payload={
                        "color": "red" if i % 2 == 0 else "blue",
                    },
                    vector=[random() for _ in range(10)],
                ) for i in range(20)
            ],
        )

        # Search for nearest neighbors
        result = await client.query_points(
            collection_name=collection_name,
            query=[random() for _ in range(10)],
            limit=4,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(key="color",match=models.MatchValue(value="red"))
                ]
            ),
            score_threshold=0.7
        )

        points=result.points
        print(points)
        print(type(points))
        for point in points:
            print(point.payload)
            print(type(point.payload))

        await qdrant_client_manager.close()

    asyncio.run(test())
