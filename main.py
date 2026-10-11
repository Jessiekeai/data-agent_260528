import uuid

import uvicorn
from fastapi import FastAPI
from starlette.requests import Request

from app.api.routers.query_router import query_router
from app.core.context import set_req_id
from app.core.lifespan import lifespan

app = FastAPI(lifespan=lifespan)

# 注册路由器
app.include_router(query_router)

# 注册请求中间件
@app.middleware("http")
async def set_req_id_middleware(request: Request, call_next):
    # 在处理请求前，创建请求id并保存
    set_req_id(str(uuid.uuid4()))
    # 调用下一个中间件或路由
    # 返回响应给浏览器端
    return await call_next(request)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)