from elasticsearch import AsyncElasticsearch

from app.models.es.value_info_es import ValueInfoES


class ValueEsRepository():
    index_name = "data-agent_values_index"

    def __init__(self, client: AsyncElasticsearch):
        self.client = client

    async def _ensure_index(self):
        client = self.client
        index_name = self.index_name
        if await client.indices.exists(index=index_name):
            await client.indices.delete(index=index_name)
        await client.indices.create(
            index=index_name,
            mappings={
                "dynamic": False,
                "properties": {
                    "id": {
                        "type": "keyword"
                    },
                    "value": {
                        "type": "text",
                        "analyzer": "ik_max_word"
                    },
                    "type": {
                        "type": "keyword"
                    },
                    "column_id": {
                        "type": "keyword"
                    },
                    "column_name": {
                        "type": "keyword"
                    },
                    "table_id": {
                        "type": "keyword"
                    },
                    "table_name": {
                        "type": "keyword"
                    }
                }
            },
        )

    async def save_values(self, value_infos: list[ValueInfoES]):
        client = self.client
        index_name = self.index_name
        await self._ensure_index()

        batch_size = 20
        for i in range(0, len(value_infos), batch_size):
            batch_values_infos = value_infos[i:i + batch_size]

            operations = []
            for value_info in batch_values_infos:
                operations.append({
                    "index": {
                        "_index": index_name,
                    }
                })
                operations.append(value_info)

            await client.bulk(operations=operations)

    async def search(self, keyword):
        client = self.client
        index_name = self.index_name
        resp = await client.search(
            index=index_name,
            query={
                "match": {
                    "value": keyword
                }
            },
        )
        # print(resp)
        # print(resp["hits"]["hits"][0]["_source"])

        return [ValueInfoES(**item["_source"]) for item in resp["hits"]["hits"]]
