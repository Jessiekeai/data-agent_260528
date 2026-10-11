from pydantic import BaseModel


# 定义数据模型类,需要继承 BaseModel 的类。
class QuerySchema(BaseModel):
    query: str
