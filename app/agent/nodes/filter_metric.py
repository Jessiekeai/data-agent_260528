import yaml
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt_file

"""
1.取出需要的query和metric_infos,交给大模型处理,得到必须的表名和字段名的列表
2.对metric_infos进行过滤,过滤掉不必要的表和字段信息
3.返回过滤后的metric_infos
"""


async def filter_metric(state: DataAgentState):
    try:
        query = state["query"]
        metric_infos = state["metric_infos"]

        # 1.取出需要的query和metric_infos,交给大模型处理,得到必须的表名和字段名的列表
        prompt_template = PromptTemplate(
            template=load_prompt_file("filter_metric_info"),
            input_variables=["query", "metric_infos"]
        )
        parser = JsonOutputParser()
        chain = prompt_template | llm | parser
        result = chain.invoke({
            "query": query,
            "metric_infos": yaml.dump(
                metric_infos,
                allow_unicode=True,  # 保留原本中文，不要转换为unicode编码
                sort_keys=False,  # 保留字典对象中原本顺序
            )
        })
        logger.info(f"filter_metric llm result={result}")
        # 2.对metric_infos进行过滤, 过滤掉不必要的表和字段信息
        for metric_info in metric_infos[:]:
            metric_name = metric_info["name"]
            if metric_name not in result:
                metric_infos.remove(metric_info)

        logger.info(f"过滤指标完成:{metric_infos}")
        # 3.返回过滤后的metric_infos
        return {"metric_infos": metric_infos}
    except Exception as e:
        logger.error(f"过滤指标信息失败:{str(e)}")
        raise
