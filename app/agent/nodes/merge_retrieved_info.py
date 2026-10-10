from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState, ColumnInfoState, TableInfoState, MetricInfoState
from app.core.log import logger
from app.models.mysql.column_info_mysql import ColumnInfoMySQL
from app.models.mysql.table_info_mysql import TableInfoMySQL
from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant
from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant

"""
1.收集一个最完整的字段信息列表,去重合并 dict[column_id,ColumnInfoQdrant]
1.1收集召回的字段信息列表
1.2收集召回的指标信息列表关联的字段信息列表
1.3收集召回的字段值信息列表对应的字段信息列表 将字段值保存到字段的值的样例表中
1.4收集相关表的主键和外键字段信息列表
2.根据收集所有字段信息列表生成:带字段信息列表的表信息列表
2.1对收集的字段信息列表进行按表id进行分组:dict[table_id,list[ColumnInfoQdrant]]
2.2生成带字段信息列表的表信息列表->table_infos:list[TableInfoState]
    根据表id查询meta:table_info得到表信息
    根据当前字段信息列表来生成ColumnInfoState类型的字段信息
"""


def _convert_column_info_mysql_to_qdrant(column_info_mysql: ColumnInfoMySQL) -> ColumnInfoQdrant:
    return ColumnInfoQdrant(
        id=column_info_mysql.id,
        name=column_info_mysql.name,
        type=column_info_mysql.type,
        role=column_info_mysql.role,
        examples=column_info_mysql.examples,
        description=column_info_mysql.description,
        alias=column_info_mysql.alias,
        table_id=column_info_mysql.table_id
    )


def _convert_column_info_qdrant_to_state(column_info: ColumnInfoQdrant) -> ColumnInfoState:
    return ColumnInfoState(
        name=column_info["name"],
        type=column_info["type"],
        role=column_info["role"],
        examples=column_info["examples"],
        description=column_info["description"],
        alias=column_info["alias"]
    )


def _convert_metric_info_qdrant_to_state(metric_info: MetricInfoQdrant) -> MetricInfoState:
    return MetricInfoState(
        name=metric_info["name"],
        description=metric_info["description"],
        relevant_columns=metric_info["relevant_columns"],
        alias=metric_info["alias"]
    )


async def merge_retrieved_info(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    runtime.stream_writer({"stage": "召回合并"})

    try:
        recall_columns = state["recall_columns"]
        recall_metrics = state["recall_metrics"]
        recall_values = state["recall_values"]
        meta_mysql_repo = runtime.context["meta_mysql_repo"]

        column_info_dict: dict[str, ColumnInfoQdrant] = {}
        # 1.收集一个最完整的字段信息列表, 去重合并    dict[column_id, ColumnInfoQdrant]
        # 1.1收集召回的字段信息列表
        for column_info in recall_columns:
            column_id = column_info["id"]
            if column_id not in column_info_dict:
                column_info_dict[column_id] = column_info

        # 1.2收集召回的指标信息列表关联的字段信息列表
        for metric_info in recall_metrics:
            relevant_columns = metric_info["relevant_columns"]
            for relevant_column in relevant_columns:
                column_id = relevant_column
                if column_id not in column_info_dict:
                    # 查询字段信息
                    column_info_mysql: ColumnInfoMySQL = await meta_mysql_repo.get_column_info_by_id(column_id)
                    column_info_dict[column_id] = _convert_column_info_mysql_to_qdrant(column_info_mysql)

        # 1.3收集召回的字段值信息列表对应的字段信息列表   将字段值保存到字段的值的样例表中
        for value_info in recall_values:
            column_id = value_info["column_id"]
            if column_id not in column_info_dict:
                # 查询字段信息
                column_info_mysql: ColumnInfoMySQL = await meta_mysql_repo.get_column_info_by_id(column_id)
                column_info_dict[column_id] = _convert_column_info_mysql_to_qdrant(column_info_mysql)

                # 将字段值保存到字段的值的样例表中
                value = value_info["value"]
                if value not in column_info_dict[column_id]["examples"]:
                    column_info_dict[column_id]["examples"].append(value)

        table_column_infos_dict: dict[str, list[ColumnInfoQdrant]] = {}
        table_infos: list[TableInfoState]=[]
        # 2.根据收集所有字段信息列表生成: 带字段信息列表的表信息列表
        # 2.1对收集的字段信息列表进行按表id进行分组: dict[table_id, list[ColumnInfoQdrant]]
        for column_info in column_info_dict.values():
            table_id = column_info["table_id"]
            if table_id not in table_column_infos_dict:
                table_column_infos_dict[table_id] = []
                table_column_infos_dict[table_id].append(column_info)

        # 1.4收集相关表的主键和外键字段信息列表
        for table_id, column_infos in table_column_infos_dict.items():
            key_columns: list[ColumnInfoMySQL] = await meta_mysql_repo.get_key_column_infos_by_table_id(table_id)
            for key_column in key_columns:
                if key_column.id not in table_column_infos_dict:
                    column_infos.append(_convert_column_info_mysql_to_qdrant(key_column))

            # 2.2生成带字段信息列表的表信息列表->table_infos: list[TableInfoState]
            # 根据表id查询meta: table_info得到表信息
            table_info: TableInfoMySQL = await meta_mysql_repo.get_table_info_by_id(table_id)

            # 根据当前字段信息列表来生成ColumnInfoState类型的字段信息
            columns: list[ColumnInfoState] = [
                _convert_column_info_qdrant_to_state(column_info)
                for column_info in column_infos
            ]

            table_infos.append(TableInfoState(
                    name=table_info.name,
                    role=table_info.role,
                    description=table_info.description,
                    columns=columns
                ))


        # 整理metric_infos
        metric_infos: list[MetricInfoState] = [
            _convert_metric_info_qdrant_to_state(metric_info)
            for metric_info in recall_metrics
        ]

        return {"table_infos": table_infos, "metric_infos": metric_infos}
    except Exception as e:
        logger.error(f"召回合并失败:{str(e)}")
        raise
