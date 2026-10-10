from qdrant_client import AsyncQdrantClient, models
from qdrant_client.http import model

from app.conf.app_config import app_config
from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant


class ColumnQdrantRepository():
    collection_name = "data-agent_column_col"

    def __init__(self, client: AsyncQdrantClient):
        self.client = client

    # 确保集合在
    async def _ensure_collection(self):
        client = self.client
        collection_name = self.collection_name

        # Create a collection
        if await client.collection_exists(collection_name):
            await client.delete_collection(collection_name)
        await client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=app_config.qdrant.embedding_size, distance=models.Distance.COSINE),
        )

    async def save_column_vectors(self, ids: list[str], payloads: list[ColumnInfoQdrant], vectors: list[list[float]]):
        client = self.client
        collection_name = self.collection_name

        await self._ensure_collection()

        # 对数据进行分批处理
        batch_size = 10
        # 对数据进行分批
        for i in range(0, len(ids), batch_size):
            # 取出当前批次的数据
            batch_ids = ids[i:i + batch_size]
            batch_payloads = payloads[i:i + batch_size]
            batch_vectors = vectors[i:i + batch_size]

            # 批量插入当前批次的多个向量数据
            await client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=batch_ids[i],
                        payload=batch_payloads[i],
                        vector=batch_vectors[i]
                    ) for i in range(len(batch_ids))
                ],
            )

    async def search(self, keyword_vector: list[float],score_threshold=0.6) -> list[ColumnInfoQdrant]:
        client = self.client
        result = await client.query_points(
            collection_name=self.collection_name,
            query=keyword_vector,
            score_threshold=score_threshold
        )

        points = result.points
        return [ColumnInfoQdrant(**point.payload) for point in points]
