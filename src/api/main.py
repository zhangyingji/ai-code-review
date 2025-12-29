"""
FastAPI应用主文件
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .models.database import init_database
from .routers import reviews, issues, statistics

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="代码评审系统API",
    description="代码评审结果数据存储与查询系统",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应配置具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(reviews.router, prefix="/api/v1")
app.include_router(issues.router, prefix="/api/v1")
app.include_router(statistics.router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    logger.info("初始化数据库...")
    # 数据库路径将从配置中读取，这里使用默认值
    init_database()
    logger.info("数据库初始化完成")


@app.get("/")
async def root():
    """根路径"""
    return {"message": "代码评审系统API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
