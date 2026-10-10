"""
  @Author:jiexi
  @Time:2026/9/30
  @Desc:MYSQL数据库的客户端管理器
"""
import asyncio
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession

from app.conf.app_config import DBConfig, app_config


class MySQLClientManager:
    def __init__(self, config: DBConfig):
        self.config = config
        self.client: Optional[AsyncEngine] = None

    def _get_url(self):
        return f"mysql+asyncmy://{self.config.user}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}?charset=utf8mb4"

    def init_client(self):
        self.client = create_async_engine(
            self._get_url(),
            pool_size=10,#连接池大小，初始化的常驻连接数，默认是5
            max_overflow=5#最大临时连接数，默认是10
        )
        """
        当获取连接时，返回常驻连接，如果常驻连接用满，创建临时连接，如果临时连接也满了，等待一定时间，如果超时就报错
        """

    async def close(self):
        await self.client.dispose()


# 创建处理dw库的客户端管理器
dw_mysql_client_manager = MySQLClientManager(app_config.db_dw)
# 创建处理meta库的客户端管理器
meta_mysql_client_manager = MySQLClientManager(app_config.db_meta)

# 测试
if __name__ == "__main__":
    async def test():
        # 初始化客户端
        dw_mysql_client_manager.init_client()

        # 创建会话对象
        async with AsyncSession(
                bind=dw_mysql_client_manager.client,
                autobegin=True,#自动开启事务
                autoflush=False,#不自动将未提交的数据更新刷新到暂存区->提交前不能查询到
        ) as session:
            sql = "select * from dim_customer limit 2"
            result = await session.execute(text(sql))

            """
            result.all():返回[Row,Row,Row] row对象包含当前行数的字段值可遍历对象
            result.mappings().all():返回[RowMapping,RowMapping,RowMapping]RowMapping对象包含当前行数的字段名和字段值可遍历对象
            result.scalars().all():返回[val,val,val] val是第一个字段值
            """
            # 读取数据
            # rows=result.all()
            # print(rows)
            # print(type(rows))
            # print(type(rows[0]))
            # for row in rows:
            #     for val in row:
            #         print(val)

            # rows = result.mappings().all()
            # print(rows,type(rows[0]))
            # for row in rows:
            #     for key, value in row.items():
            #         print(key,value)

            rows = result.scalars().all()
            print(rows, type(rows[0]))

        # 关闭
        await dw_mysql_client_manager.close()


    asyncio.run(test())
