from typing import List

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mysql.column_info_mysql import ColumnInfoMySQL
from app.models.mysql.column_metric_mysql import ColumnMetricMySQL
from app.models.mysql.metric_info_mysql import MetricInfoMySQL
from app.models.mysql.table_info_mysql import TableInfoMySQL

"""
操作meta库的持久层模块
"""


class MetaMysqlRepository():
    def __init__(self, session: AsyncSession):
        self.session = session

    # 添加多个表信息
    def save_table_infos(self, table_infos: List[TableInfoMySQL]):
        self.session.add_all(table_infos)

    # 添加多个字段信息
    def save_column_infos(self, column_infos: List[ColumnInfoMySQL]):
        self.session.add_all(column_infos)

    # 添加多个指标信息
    def save_metric_infos(self, metric_infos: List[MetricInfoMySQL]):
        self.session.add_all(metric_infos)

    # 向column_metric表中插入多条数据
    def save_column_metrics(self, column_metrics: list[ColumnMetricMySQL]):
        self.session.add_all(column_metrics)

    async def get_column_info_by_id(self, column_id):
        return await self.session.get(ColumnInfoMySQL, column_id)

    async def get_key_column_infos_by_table_id(self, table_id: str) -> List[ColumnInfoMySQL]:
        result = await self.session.execute(
            Select(ColumnInfoMySQL)
            .where(ColumnInfoMySQL.table_id == table_id)
            .where(ColumnInfoMySQL.role.in_(["primary_key", "foreign_key"]))
        )
        return result.scalars().all()

    async def get_table_info_by_id(self, table_id):
        return await self.session.get(TableInfoMySQL, table_id)
