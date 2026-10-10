from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime

from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant
from app.prompt.prompt_loader import load_prompt_file

"""
1.将用户提问交给大模型来提取语义化的关键字列表:仅输出 JSON 数组["张三", "李四"]，并与原有关键字去重合并:keywords
2.对keywords进行批量向量化->keywords_vectors:list[list[float]]
3.遍历每个keyword_vectors,去qdrant中搜索得到匹配的字段值列表:list[ColumnInfoQdrant]
4.对得到字段值列表做去重合并->recall_columns:list[ColumnInfoQdrant]
5.返回recall_columns
"""


async def recall_column(state: DataAgentState, runtime: Runtime, config: RunnableConfig):
    try:
        keywords = state["keywords"]
        query = state["query"]
        embedding_client = runtime.context["embedding_client"]
        column_qdrant_repo = runtime.context["column_qdrant_repo"]
        # 1.将用户提问交给大模型来提取语义化的关键字列表，并与原有关键字去重合并: keywords
        prompt_template = PromptTemplate(
            template=load_prompt_file("extend_keywords_for_column_recall"),
            input_variables=["query"]
        )
        parser = JsonOutputParser()
        chain = prompt_template | llm | parser
        result = chain.invoke({"query": query})

        logger.info(result)

        # 并与原有关键字去重合并: keywords
        keywords = list(set(keywords + result))

        # 2.对keywords进行批量向量化->keywords_vectors:list[list[float]]
        keyword_vectors = await embedding_client.aembed_documents(keywords)

        recall_columns: list[ColumnInfoQdrant] = []
        # recall_columns_dict:dict[column_id,payload]
        recall_columns_dict: dict[str, ColumnInfoQdrant] = {}
        # 3.遍历每个keyword_vectors, 去qdrant中搜索得到匹配的字段值列表: list[ColumnInfoQdrant]
        # 4.对得到字段值列表做去重合并->recall_columns: list[ColumnInfoQdrant]
        for keyword_vector in keyword_vectors:
            column_infos: list[ColumnInfoQdrant] = await column_qdrant_repo.search(keyword_vector)
            # recall_columns.extend(column_infos)
            for column_info in column_infos:
                column_id = column_info["id"]
                if column_id not in recall_columns_dict:
                    recall_columns_dict[column_id] = column_info
        recall_columns: list[ColumnInfoQdrant] = list(recall_columns_dict.values())

        # 5.返回recall_columns
        return {"recall_columns": recall_columns}
    except Exception as e:
        logger.error(f"召回指标失败:{str(e)}")
        raise
