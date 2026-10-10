from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant
from app.prompt.prompt_loader import load_prompt_file

"""
1.将用户提问交给大模型来提取语义化的关键字列表，并与原有关键字去重合并:keywords
2.对keywords进行批量向量化->keywords_vectors
3.遍历每个keyword_vectors,去qdrant中搜索得到匹配的指标信息列表:list[MetricInfoQdrant]
4.对得到指标信息列表做去重合并->recall_metrics:list[MetricInfoQdrant]
5.返回recall_metrics
"""


async def recall_metric(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    runtime.stream_writer({"stage": "召回指标"})

    try:
        query = state["query"]
        keywords = state["keywords"]
        embedding_client = runtime.context["embedding_client"]
        metric_qdrant_repo = runtime.context["metric_qdrant_repo"]

        # 1.将用户提问交给大模型来提取语义化的关键字列表，并与原有关键字去重合并: keywords
        prompt_template = PromptTemplate(
            template=load_prompt_file("extend_keywords_for_metric_recall"),
            input_variables=["query"]
        )
        output_parser = JsonOutputParser()
        chain = prompt_template | llm | output_parser
        result = chain.invoke({"query": query})
        print(f"recall_metric llm keywords={result}")

        keywords = list(set(result + keywords))

        # 2.对keywords进行批量向量化->keywords_vectors
        keywords_vectors = await embedding_client.aembed_documents(keywords)

        recall_metrics: list[MetricInfoQdrant] = []

        # dict[metric_id,metricInfoQdrant]
        recall_metrics_dict : dict[str, MetricInfoQdrant] = {}

        # 3.遍历每个keyword_vectors, 去qdrant中搜索得到匹配的指标指标信息列表: list[MetricInfoQdrant]
        # 4.对得到指标指标信息列表做去重合并->recall_metrics: list[MetricInfoQdrant]
        for keyword_vector in keywords_vectors:
            metric_infos: list[MetricInfoQdrant] = await metric_qdrant_repo.search(keyword_vector)
            # recall_metrics.extend(metric_infos)
            for metric_info in metric_infos:
                metric_id = metric_info["id"]
                if metric_id not in recall_metrics_dict:
                    recall_metrics_dict[metric_id] = metric_info

        recall_metrics: list[MetricInfoQdrant] = list(recall_metrics_dict.values())

        logger.info(f"recall_metrics:{recall_metrics}")
        # 5.返回recall_metrics

        return {"recall_metrics": recall_metrics}
    except Exception as e:
        logger.error(f"召回指标失败：{str(e)}")
        raise
