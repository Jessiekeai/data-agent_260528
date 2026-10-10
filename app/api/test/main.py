"""
技术点1: 处理不同类型的请求
技术点2：获取不同类型的参数
技术点3：使用路由器
技术点4：SSE流式响应
技术点5：生命周期
技术点6：中间件
技术点7：依赖注入
"""
import uvicorn
from fastapi import FastAPI

app=FastAPI()
"""测试1: 测试不同类型的请求"""
# 注册路由接口
# 当这个路由路径被请求时，会自动调用路由函数
@app.get("/xxx")
async def test_get():
    print("处理 /xxx get的请求。。。")
    return {"get message": "Hello World2222333"}  # response：服务器端给浏览器端的响应数据

@app.post("/xxx")
async def test_post():
    print("处理 /xxx post 的请求。。。")
    return {"post message": "Hello World2222333"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)