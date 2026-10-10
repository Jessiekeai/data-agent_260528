import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.client.embedding_client_manager import embedding_client_manager
from app.client.es_client_manager import es_client_manager
from app.client.mysql_client_manager import dw_mysql_client_manager, meta_mysql_client_manager
from app.client.qdrant_client_manager import qdrant_client_manager
from app.conf.meta_config import meta_config
from app.core.log import logger
from app.repositories.es.value_es_repository import ValueEsRepository
from app.repositories.mysql.dw_mysql_repository import DWMysqlRepository
from app.repositories.mysql.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.services.meta_knowledge_service import MetaKnowledgeService


# 启动知识库的构建函数
async def start_build():
    logger.info("准备开始构建知识库")
    embedding_client_manager.init_client()
    es_client_manager.init_client()
    qdrant_client_manager.init_client()
    dw_mysql_client_manager.init_client()
    meta_mysql_client_manager.init_client()

    try:
        assert dw_mysql_client_manager.session_factory
        async with (
            dw_mysql_client_manager.session_factory() as dw_session,
            meta_mysql_client_manager.session_factory() as meta_session
        ):
            meta_session: AsyncSession

            service = MetaKnowledgeService(
                dw_mysql_repo=DWMysqlRepository(dw_session),
                meta_mysql_repo=MetaMysqlRepository(meta_session),
                value_es_repo=ValueEsRepository(es_client_manager.client),
                column_qdrant_repo=ColumnQdrantRepository(qdrant_client_manager.client),
                metric_qdrant_repo=MetricQdrantRepository(qdrant_client_manager.client),
                embedding_client=embedding_client_manager.client
            )
            await service.build(meta_config)

            # await dw_session.commit()
            await meta_session.commit()
            logger.info("构建知识库成功")
    except Exception as e:
        logger.error(f"构建知识库失败：{str(e)}")
        # await dw_session.rollback()
        await meta_session.rollback()
        raise
    finally:
        await es_client_manager.close()
        await qdrant_client_manager.close()
        await dw_mysql_client_manager.close()
        await meta_mysql_client_manager.close()




if __name__ == '__main__':
    asyncio.run(start_build())
