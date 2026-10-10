"""
  @Author:jiexi
  @Time:2026/9/30
  @Desc:MYSQL数据库的客户端管理器
"""
import asyncio
from typing import Optional

from app.models.mysql.table_info_mysql import TableInfoMySQL
from sqlalchemy import text, Select
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession, async_sessionmaker

from app.conf.app_config import DBConfig, app_config


class MySQLClientManager:
    def __init__(self, config: DBConfig):
        self.config = config
        self.client: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker] = None

    def _get_url(self):
        return f"mysql+asyncmy://{self.config.user}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}?charset=utf8mb4"

    def init_client(self):
        self.client = create_async_engine(
            self._get_url(),
            pool_size=10,  # 连接池大小，初始化的常驻连接数，默认是5
            max_overflow=5  # 最大临时连接数，默认是10
        )
        """
        当获取连接时，返回常驻连接，如果常驻连接用满，创建临时连接，如果临时连接也满了，等待一定时间，如果超时就报错
        """
        self.session_factory = async_sessionmaker(
            bind=self.client,
            autobegin=True,  # 自动开启事务
            autoflush=True,  # 不自动将未提交的数据更新刷新到暂存区->提交前不能查询到
        )

    async def close(self):
        await self.client.dispose()


# 创建处理dw库的客户端管理器
dw_mysql_client_manager = MySQLClientManager(app_config.db_dw)
# 创建处理meta库的客户端管理器
meta_mysql_client_manager = MySQLClientManager(app_config.db_meta)

# 测试
if __name__ == "__main__":
    async def test_orm2():
        meta_mysql_client_manager.init_client()

        assert meta_mysql_client_manager.session_factory is not None
        async with meta_mysql_client_manager.session_factory() as session:
            table_info = await session.get(TableInfoMySQL, "dim_customer1")

            table_info.description="abc"

            await session.delete(table_info)

            await session.commit()

        await meta_mysql_client_manager.close()



    async def test_orm1():
        meta_mysql_client_manager.init_client()

        assert meta_mysql_client_manager.session_factory
        async with meta_mysql_client_manager.session_factory() as session:
            # 插入单条数据

            table_info1 = TableInfoMySQL(
                id="dim_customer1",
                name="dim_customer1",
                role="dim",
                description="客户信息表1"
            )
            session.add(table_info1)

            table_info2 = TableInfoMySQL(
                id="dim_customer2",
                name="dim_customer2",
                role="dim",
                description="客户信息表2"
            )

            table_info3 = TableInfoMySQL(
                id="dim_customer3",
                name="dim_customer3",
                role="dim",
                description="客户信息表3"
            )

            session.add_all([table_info2, table_info3])

            await session.commit()

            table_info = await session.get(TableInfoMySQL, "dim_customer1")
            print(table_info, type(table_info))
            print(table_info.name)

            print("=" * 60)

            result = await session.execute(Select(TableInfoMySQL).limit(2))
            rows = result.scalars().all()
            print(rows)
            print(rows[0].description)
            print(rows[0].id)
            print(rows[0].name)
            print(rows[0].role)


        await meta_mysql_client_manager.close()


    async def test():
        # 初始化客户端
        dw_mysql_client_manager.init_client()

        # 创建会话对象
        async with dw_mysql_client_manager.session_factory() as session:
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
