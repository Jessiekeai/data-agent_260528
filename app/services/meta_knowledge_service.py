import uuid
from typing import List, Dict

from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.conf.meta_config import MetaConfig, TableConfig, MetricConfig
from app.core.log import logger
from app.models.es.value_info_es import ValueInfoES
from app.models.mysql.column_metric_mysql import ColumnMetricMySQL
from app.models.mysql.table_info_mysql import TableInfoMySQL
from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant
from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant
from app.repositories.es.value_es_repository import ValueEsRepository
from app.repositories.mysql.dw_mysql_repository import DWMysqlRepository
from app.repositories.mysql.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.models.mysql.column_info_mysql import ColumnInfoMySQL
from app.models.mysql.metric_info_mysql import MetricInfoMySQL


class MetaKnowledgeService:
    def __init__(
            self,
            dw_mysql_repo: DWMysqlRepository,
            meta_mysql_repo: MetaMysqlRepository,
            value_es_repo: ValueEsRepository,
            column_qdrant_repo: ColumnQdrantRepository,
            metric_qdrant_repo: MetricQdrantRepository,
            embedding_client: HuggingFaceEndpointEmbeddings
    ):
        self.dw_mysql_repo = dw_mysql_repo
        self.meta_mysql_repo = meta_mysql_repo
        self.value_es_repo = value_es_repo
        self.column_qdrant_repo = column_qdrant_repo
        self.metric_qdrant_repo = metric_qdrant_repo
        self.embedding_client = embedding_client

    # 构建知识库的业务方法
    """
    1. 处理表相关的信息
    1.1 将表的信息和字段的信息保存到meta库（tableinfo和column_info表）
    1.2 对所有字段信息建立向量索引
    1.3 对象字段取值建立全文索引
    2. 处理指标信息
    2.1 将指标信息数据保存到meta库（metric_info和culumn_metric表）
    2.2 对指标信息建立向量索引
       """

    async def build(self, config: MetaConfig):
        logger.info("使用各种持久模块进行构造知识库")

        # 1.1将表的信息和字段的信息保存到meta库（table_info和column_info表）
        column_infos: List[ColumnInfoMySQL] = await self._save_table_infos_to_meta(config.tables)
        logger.info("向meta库保存表信息和字段信息完成")
        # 1.2对所有字段信息建立向量索引
        await self._save_column_infos_to_qdrant(column_infos)
        logger.info("向qdrant库保存字段信息完成")
        # 1.3对象字段取值建立全文索引
        await self._save_value_infos_to_es(column_infos, config.tables)
        logger.info("向es库保存字段值完成")

        # 2.处理指标信息
        # 2.1将指标信息数据保存到meta库（metric_info和column_metric表）
        metric_infos: List[MetricInfoMySQL] = await self._save_metric_infos_to_meta(config.metrics)
        logger.info("向meta库保存指标信息完成")
        # 2.2对指标信息建立向量索引
        await self._save_metric_infos_to_qdrant(metric_infos)
        logger.info("向qdrant库保存指标信息完成")

    async def _save_table_infos_to_meta(self, tables: list[TableConfig]) -> List[ColumnInfoMySQL]:
        # 准备用来存储表信息和字段信息的容器
        table_infos: List[TableInfoMySQL] = []
        column_infos: List[ColumnInfoMySQL] = []
        # 遍历tables收集数据
        for table in tables:
            table_infos.append(TableInfoMySQL(
                id=table.name,
                name=table.name,
                role=table.role,
                description=table.description,
            ))
            # 查询得到表中所有字段的类型:dict[字段名,字段类型]
            column_types: dict[str, str] = await self.dw_mysql_repo.get_column_types(table.name)

            for column in table.columns:
                values: List = await self.dw_mysql_repo.get_column_values(table.name, column.name)

                column_infos.append(ColumnInfoMySQL(
                    id=f"{table.name}.{column.name}",
                    name=column.name,
                    type=column_types[column.name],
                    role=column.role,
                    examples=values,
                    description=column.description,
                    alias=column.alias,
                    table_id=table.name
                ))

        # 将表信息列表保存在meta库
        self.meta_mysql_repo.save_table_infos(table_infos)

        # 将字段信息列表保存在meta库
        self.meta_mysql_repo.save_column_infos(column_infos)

        return column_infos

    async def _save_column_infos_to_qdrant(self, column_infos: List[ColumnInfoMySQL]):

        # 收集ids/payloads/texts -> list[dict[id,payload,text]]
        temp_list: list[Dict] = []
        for column_info in column_infos:
            # name
            temp_list.append({
                "id": uuid.uuid4(),
                "text": column_info.name,
                "payload": ColumnInfoQdrant(
                    id=column_info.id,
                    name=column_info.name,
                    type=column_info.type,
                    role=column_info.role,
                    examples=column_info.examples,
                    description=column_info.description,
                    alias=column_info.alias,
                    table_id=column_info.table_id
                )
            })
            # description
            temp_list.append({
                "id": uuid.uuid4(),
                "text": column_info.description,
                "payload": ColumnInfoQdrant(
                    id=column_info.id,
                    name=column_info.name,
                    type=column_info.type,
                    role=column_info.role,
                    examples=column_info.examples,
                    description=column_info.description,
                    alias=column_info.alias,
                    table_id=column_info.table_id
                )
            })
            # alias
            for alia in column_info.alias:
                temp_list.append({
                    "id": uuid.uuid4(),
                    "text": alia,
                    "payload": ColumnInfoQdrant(
                        id=column_info.id,
                        name=column_info.name,
                        type=column_info.type,
                        role=column_info.role,
                        examples=column_info.examples,
                        description=column_info.description,
                        alias=column_info.alias,
                        table_id=column_info.table_id
                    )
                })

        # 取出所有texts进行分批向量化->生成vectors
        texts = [item["text"] for item in temp_list]
        # 需要进行分批向量化处理
        vectors: list[list[float]] = []
        batch_size = 16
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_vectors = await self.embedding_client.aembed_documents(batch_texts)
            vectors.extend(batch_vectors)

        # 取出所有ids和payloads
        ids = [item["id"] for item in temp_list]
        payloads = [item["payload"] for item in temp_list]

        # 调用持久层保存字段信息列表数据 ids payloads vectors
        await self.column_qdrant_repo.save_column_vectors(ids, payloads, vectors)

    async def _save_value_infos_to_es(self, column_infos: List[ColumnInfoMySQL], tables: list[TableConfig]):
        value_infos: list[ValueInfoES] = []

        # 收集tables中所有字段的sync:dict[column_id,bool]
        column_sync_dict: dict[str, bool] = {}
        for table in tables:
            for column in table.columns:
                column_sync_dict[f"{table.name}.{column.name}"] = column.sync

        # 收集需要进行es索引存储的字段值信息对象
        for column_info in column_infos:
            if column_sync_dict[column_info.id]:
                # 查询得到当前字段的所有值
                values:list = await self.dw_mysql_repo.get_column_values(column_info.table_id, column_info.name, 10000)
                # 遍历每个值，创建对应的value_info对象
                for value in values:
                    value_infos.append(ValueInfoES(
                        id=f"{column_info.id}.{value}",
                        value=value,
                        type=column_info.type,
                        column_id=column_info.id,
                        column_name=column_info.name,
                        table_id=column_info.table_id,
                        table_name=column_info.table_id
                    ))
        # 将字段值信息列表保存到es
        await self.value_es_repo.save_values(value_infos)

    async def _save_metric_infos_to_meta(self, metrics: list[MetricConfig]) -> List[MetricInfoMySQL]:
        # 收集数据 metric_infos和column_metrics
        metric_infos: List[MetricInfoMySQL] = []
        column_metrics:list[ColumnMetricMySQL]=[]
        for metric in metrics:
            metric_infos.append(MetricInfoMySQL(
                id=metric.name,
                name=metric.name,
                description=metric.description,
                relevant_columns=metric.relevant_columns,
                alias=metric.alias
            ))
            for column_id in metric.relevant_columns:
                column_metrics.append(ColumnMetricMySQL(
                    column_id=column_id,
                    metric_id=metric.name
                ))

        # 保存到meta库

        self.meta_mysql_repo.save_metric_infos(metric_infos)
        self.meta_mysql_repo.save_column_metrics(column_metrics)

        return metric_infos

    async def _save_metric_infos_to_qdrant(self,  metric_infos: List[MetricInfoMySQL]):
        # 收集ids/payloads/texts -> list[dict[id,payload,text]]
        temp_list: list[Dict] = []
        for metric_info in metric_infos:
            # name
            temp_list.append({
                "id": uuid.uuid4(),
                "text": metric_info.name,
                "payload": MetricInfoQdrant(
                    id=metric_info.id,
                    name=metric_info.name,
                    description=metric_info.description,
                    relevant_columns=metric_info.relevant_columns,
                    alias=metric_info.alias,
                )
            })
            # description
            temp_list.append({
                "id": uuid.uuid4(),
                "text": metric_info.description,
                "payload": MetricInfoQdrant(
                    id=metric_info.id,
                    name=metric_info.name,
                    description=metric_info.description,
                    relevant_columns=metric_info.relevant_columns,
                    alias=metric_info.alias,
                )
            })
            # alias
            for alia in metric_info.alias:
                temp_list.append({
                    "id": uuid.uuid4(),
                    "text": alia,
                    "payload": MetricInfoQdrant(
                    id=metric_info.id,
                    name=metric_info.name,
                    description=metric_info.description,
                    relevant_columns=metric_info.relevant_columns,
                    alias=metric_info.alias,
                )
            })

        # 取出所有texts进行分批向量化->生成vectors
        texts = [item["text"] for item in temp_list]
        # 需要进行分批向量化处理
        vectors: list[list[float]] = []
        batch_size = 16
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_vectors = await self.embedding_client.aembed_documents(batch_texts)
            vectors.extend(batch_vectors)

        # 取出所有ids和payloads
        ids = [item["id"] for item in temp_list]
        payloads = [item["payload"] for item in temp_list]

        # 调用持久层保存字段信息列表数据 ids payloads vectors
        await self.metric_qdrant_repo.save_metric_vectors(ids, payloads, vectors)
