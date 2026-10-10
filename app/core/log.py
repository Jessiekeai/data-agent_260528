"""
  @Author:jiexi
  @Time:2026/10/2
  @Desc:
"""
import asyncio
import sys

from loguru import logger

from app.conf.app_config import app_config
from app.core.context import get_req_id, set_req_id

# 配置日志格式
log_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<magenta>request_id - {extra[request_id]}</magenta> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

# 移除默认的配置
logger.remove()


def reject_request_id(record):
    # print("="*20)
    req_id = get_req_id()
    record["extra"]["request_id"] = req_id


logger = logger.patch(reject_request_id)

# 添加控制台日志输出其->输出到控制台
if app_config.logging.console.enable:
    logger.add(
        sink=sys.stdout,  # 输出到控制台
        level=app_config.logging.console.level,  # 控制台输出级别
        format=log_format
    )

# 添加控制台日志输出器->输出到日志文件
if app_config.logging.file.enable:
    logger.add(
        sink="logs/app.log",  # 输出到控制台
        level=app_config.logging.file.level,  # 控制台输出级别
        format=log_format,
        rotation=app_config.logging.file.rotation,
        retention=app_config.logging.file.retention,
        encoding="utf-8"
    )

if __name__ == '__main__':

    # set_req_id("111")
    #
    # logger.trace("这是 TRACE 级别的调试信息")  # 不会输出到控制台（控制台是 INFO），但会输出到文件
    # logger.debug("这是 DEBUG 级别的调试信息")  # 同上
    # logger.info("服务启动成功")  # 控制台+文件都输出
    # logger.success("数据同步完成")  # Loguru 独有级别
    # logger.warning("内存使用率超过 80%")
    # logger.error("接口调用失败：超时")
    # logger.critical("数据库连接中断，服务停止")

    async def test_req1():
        logger.info(f"before req1 req_id={get_req_id()}")
        token = set_req_id("111")
        await asyncio.sleep(1)
        logger.info(f"after req1 req_id={get_req_id()}")


    async def test_req2():
        logger.info(f"before req2 req_id={get_req_id()}")
        token = set_req_id("222")
        await asyncio.sleep(1)
        logger.info(f"after req2 req_id={get_req_id()}")

    async def test():
        await asyncio.gather(test_req1(), test_req2())

    asyncio.run(test())
