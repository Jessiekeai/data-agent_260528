"""
  @Author:jiexi
  @Time:2026/10/2
  @Desc:
"""
import asyncio
from _contextvars import ContextVar, Token


_req_context_var = ContextVar("req_id", default="")


def set_req_id(request_id: str) -> Token:
    return _req_context_var.set(request_id)


def get_req_id() -> str:
    return _req_context_var.get()


def reset_req_id(token: Token):
    _req_context_var.reset(token)


if __name__ == "__main__":
    async def test_req1():
        print(f"before req1 req_id={get_req_id()}")
        token = set_req_id("111")
        await asyncio.sleep(1)
        print(f"after req1 req_id={get_req_id()}")
        await asyncio.sleep(1)
        reset_req_id(token)
        print(f"after reset req1 req_id={get_req_id()}")

    async def test_req2():
        print(f"before req2 req_id={get_req_id()}")
        token = set_req_id("222")
        await asyncio.sleep(1)
        print(f"after req2 req_id={get_req_id()}")
        await asyncio.sleep(1)
        # reset_req_id(token)
        print(f"after reset req2 req_id={get_req_id()}")

    async def test():
        await asyncio.gather(test_req1(), test_req2())

    asyncio.run(test())

