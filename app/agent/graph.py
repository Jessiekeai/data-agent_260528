import asyncio

from langgraph.constants import START, END
from langgraph.graph import StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.context import DataAgentContext
from app.agent.nodes.add_extra_context import add_extra_context
from app.agent.nodes.correct_sql import correct_sql
from app.agent.nodes.execute_sql import execute_sql
from app.agent.nodes.extract_keywords import extract_keywords
from app.agent.nodes.filter_metric import filter_metric
from app.agent.nodes.filter_table import filter_table
from app.agent.nodes.generate_sql import generate_sql
from app.agent.nodes.merge_retrieved_info import merge_retrieved_info
from app.agent.nodes.recall_column import recall_column
from app.agent.nodes.recall_metric import recall_metric
from app.agent.nodes.recall_value import recall_value
from app.agent.nodes.validate_sql import validate_sql

from app.agent.state import DataAgentState
from app.client.embedding_client_manager import embedding_client_manager
from app.client.es_client_manager import es_client_manager
from app.client.mysql_client_manager import dw_mysql_client_manager, meta_mysql_client_manager
from app.client.qdrant_client_manager import qdrant_client_manager
from app.core.log import logger
from app.repositories.es.value_es_repository import ValueEsRepository
from app.repositories.mysql.dw_mysql_repository import DWMysqlRepository
from app.repositories.mysql.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository

state_graph = StateGraph(
    state_schema=DataAgentState,
    context_schema=DataAgentContext
)

# 添加节点
state_graph.add_node("extract_keywords", extract_keywords)
state_graph.add_node("recall_column", recall_column)
state_graph.add_node("recall_value", recall_value)
state_graph.add_node("recall_metric", recall_metric)
state_graph.add_node("merge_retrieved_info", merge_retrieved_info)
state_graph.add_node("filter_table", filter_table)
state_graph.add_node("filter_metric", filter_metric)
state_graph.add_node("add_extra_context", add_extra_context)
state_graph.add_node("generate_sql", generate_sql)
state_graph.add_node("validata_sql", validate_sql)
state_graph.add_node("correct_sql", correct_sql)
state_graph.add_node("execute_sql", execute_sql)

# 添加边
state_graph.add_edge(START, "extract_keywords")
state_graph.add_edge("extract_keywords", "recall_column")
state_graph.add_edge("extract_keywords", "recall_value")
state_graph.add_edge("extract_keywords", "recall_metric")
state_graph.add_edge("recall_column", "merge_retrieved_info")
state_graph.add_edge("recall_value", "merge_retrieved_info")
state_graph.add_edge("recall_metric", "merge_retrieved_info")
state_graph.add_edge("merge_retrieved_info", "filter_table")
state_graph.add_edge("merge_retrieved_info", "filter_metric")
state_graph.add_edge("filter_table", "add_extra_context")
state_graph.add_edge("filter_metric", "add_extra_context")
state_graph.add_edge("add_extra_context", "generate_sql")
state_graph.add_edge("generate_sql", "validata_sql")

# 添加条件边
state_graph.add_conditional_edges(
    "validata_sql",
    lambda state: "correct_sql" if state.get("error") else "execute_sql",
    {"correct_sql": "correct_sql",
     "execute_sql": "execute_sql"
     }
)

state_graph.add_edge("correct_sql", "execute_sql")
state_graph.add_edge("execute_sql", END)

# 编译
compiled_state_graph = state_graph.compile()

# 得到图形
# print(compiled_state_graph.get_graph().draw_ascii())
# print(compiled_state_graph.get_graph().draw_mermaid())

if __name__ == "__main__":
    async def test():
        state = DataAgentState(query="各个地区iPhone去年卖了多少钱")  # 华北地区销售总额
        # context=DataAgentContext()

        embedding_client_manager.init_client()
        es_client_manager.init_client()
        qdrant_client_manager.init_client()
        dw_mysql_client_manager.init_client()
        meta_mysql_client_manager.init_client()

        try:
            assert dw_mysql_client_manager.session_factory
            async with (
                dw_mysql_client_manager.session_factory() as dw_session,
                meta_mysql_client_manager.session_factory() as meta_session
            ):
                meta_session: AsyncSession

                context = DataAgentContext(
                    dw_mysql_repo=DWMysqlRepository(dw_session),
                    meta_mysql_repo=MetaMysqlRepository(meta_session),
                    value_es_repo=ValueEsRepository(es_client_manager.client),
                    column_qdrant_repo=ColumnQdrantRepository(qdrant_client_manager.client),
                    metric_qdrant_repo=MetricQdrantRepository(qdrant_client_manager.client),
                    embedding_client=embedding_client_manager.client
                )

                # 执行图
                async for chunk in compiled_state_graph.astream(input=state, context=context, stream_mode="custom"):
                    print("-------", chunk)

                # 成功了提交事务
                await meta_session.commit()
        except Exception as e:
            logger.error(f"执行图进行搜索失败：{str(e)}")
            # await dw_session.rollback()
            await meta_session.rollback()
            raise
        finally:
            await es_client_manager.close()
            await qdrant_client_manager.close()
            await dw_mysql_client_manager.close()
            await meta_mysql_client_manager.close()


    asyncio.run(test())
