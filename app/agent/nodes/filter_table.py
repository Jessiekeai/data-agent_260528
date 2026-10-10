import yaml
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt_file

"""
1.取出需要的query和table_infos,交给大模型处理,得到必须的表名和字段名的列表
2.对table_infos进行过滤,过滤掉不必要的表和字段信息
3.返回过滤后的table_infos
"""

async def filter_table(state: DataAgentState):
    try:
        query = state["query"]
        table_infos = state["table_infos"]

        # 1.取出需要的query和table_infos,交给大模型处理,得到必须的表名和字段名的列表
        prompt_template = PromptTemplate(
            template=load_prompt_file("filter_table_info"),
            input_variables=["query", "table_infos"]
        )
        parser = JsonOutputParser()
        chain = prompt_template | llm | parser
        result = chain.invoke({
            "query": query,
            "table_infos": yaml.dump(
                table_infos,
                allow_unicode=True,  # 保留原本中文，不要转换为unicode编码
                sort_keys=False,  # 保留字典对象中原本顺序
            )
        })
        logger.info(f"filter_table llm result={result}")
        # 2.对table_infos进行过滤, 过滤掉不必要的表和字段信息
        for table_info in table_infos[:]:
            table_name = table_info["name"]
            if table_name not in result:
                table_infos.remove(table_info)
            else:
                for column_info in table_info["columns"]:
                    column_name = column_info["name"]
                    if column_name not in result[table_name]:
                        table_info["columns"].remove(column_info)

        logger.info(f"过滤表和字段完成:{table_infos}")
        # 3.返回过滤后的table_infos
        return {"table_infos": table_infos}
    except Exception as e:
        logger.error(f"过滤表信息失败:{str(e)}")
        raise
