"""后端入口：所有 HTTP 请求从这里进来。"""
from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from app.api.appointment_router import router as appointment_router
from app.api.meta_router import router as meta_router
from app.api.reminder_router import router as reminder_router
from app.api.auth_router import router as auth_router

app = FastAPI(
    title="牙科诊所管理系统 API",
    version="0.1.0",
    description="系统分析与设计课程作业 · 单店牙科诊所",
)

# 小程序联调用：放行所有来源。开发期方便，上线前要改成具体域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(appointment_router)
app.include_router(meta_router)
app.include_router(reminder_router)
app.include_router(auth_router)


@app.get("/api/ping")
def ping():
    return {"ok": True, "service": "dental-backend", "version": "0.1.0"}