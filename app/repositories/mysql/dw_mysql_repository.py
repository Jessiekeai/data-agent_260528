from typing import Dict, List

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class DWMysqlRepository():
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_column_types(self, table_name: str) -> Dict[str, str]:
        sql = f"show columns from {table_name}"
        result = await self.session.execute(text(sql))

        return {row.Field: row.Type for row in result.all()}

    async def get_column_values(self, table_name: str, column_name: str, limit: int = 10) -> List:
        sql = f"select distinct {column_name} from {table_name} limit {limit}"

        result = await self.session.execute(text(sql))

        return result.scalars().all()

    async def get_db_info(self) -> dict[str, str]:
        result = await self.session.execute(text("select version()"))
        version = result.scalar()
        dialect = self.session.get_bind().dialect.name
        return {"version": version, "dialect": dialect}

    async def validate_sql(self, sql: str):
        # 不会真正运行查询,只是检查SQL
        await self.session.execute(text(f"explain {sql}"))

    async def execute_sql(self, sql: str) -> list:
        result = await self.session.execute(text(sql))

        return result.mappings().all()
