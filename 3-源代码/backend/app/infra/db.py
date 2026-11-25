"""数据库连接。整台机器只有这里知道账号密码和库名。"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 格式：mysql+pymysql://用户名:密码@主机:端口/库名?字符集
# 注意：密码里的 @ : / 等符号必须做 URL 编码，@ 要写成 %40
DATABASE_URL = "mysql+pymysql://root:Wy708965@127.0.0.1:3306/dental?charset=utf8mb4"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,     # 取连接前先 ping 一下，防止 MySQL 8 小时超时断开
    pool_recycle=3600,
    echo=False,             # 改成 True 可以在终端看到执行的每条 SQL，调试很有用
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
