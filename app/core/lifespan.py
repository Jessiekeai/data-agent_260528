from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.client.embedding_client_manager import embedding_client_manager
from app.client.es_client_manager import es_client_manager
from app.client.mysql_client_manager import dw_mysql_client_manager, meta_mysql_client_manager
from app.client.qdrant_client_manager import qdrant_client_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("应用启动时执行一次，用来一次性的初始化操作，比如：初始化客户端")
    embedding_client_manager.init_client()
    es_client_manager.init_client()
    qdrant_client_manager.init_client()
    dw_mysql_client_manager.init_client()
    meta_mysql_client_manager.init_client()
    yield
    print("应用退出前执行一次，用来做收尾的操作，比如：关闭客户端")
    await es_client_manager.close()
    await qdrant_client_manager.close()
    await dw_mysql_client_manager.close()
    await meta_mysql_client_manager.close()

