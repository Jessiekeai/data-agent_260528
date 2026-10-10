from datetime import datetime

from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState, DateInfoState, DBInfoState
from app.core.log import logger

"""
1.当前日期信息
2.数据库信息:数据库名称和版本
"""


async def add_extra_context(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    runtime.stream_writer({"stage": "添加额外信息"})

    try:
        dw_mysql_repo = runtime.context["dw_mysql_repo"]

        # 1.当前日期信息
        today = datetime.today()
        date = today.strftime("%Y%m%d")
        weekday = f"{today.weekday()}"
        quarter = f"Q{(today.month + 2) // 3}"
        date_info = DateInfoState(
            date=date,
            weekday=weekday,
            quarter=quarter
        )
        """
        1 2 3 -> 1
        4 5 6 -> 2
        """

        db_info_dict: dict = await dw_mysql_repo.get_db_info()
        db_info = DBInfoState(**db_info_dict)
        logger.info(f"添加额外信息成功:date_info={date_info},db_info:{db_info}")
        return {"date_info": date_info, "db_info": db_info}
    except Exception as e:
        logger.error(f"添加额外信息失败：{str(e)}")
        raise
