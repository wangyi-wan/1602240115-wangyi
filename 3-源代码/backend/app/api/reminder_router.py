"""消息提醒相关接口。

POST /api/reminders/plan      预约成功后建一条提醒计划
POST /api/reminders/dispatch  立即扫描并发送（演示用，不用等定时任务）
POST /api/reminders/send/{id} 给指定预约发一次
GET  /api/reminders/outbox    最近记录，小程序里直接看
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.infra.message_gateway import WX_TEMPLATE_ID, build_primary_gateway
from app.service import reminder_service

router = APIRouter(prefix="/api/reminders", tags=["reminder"])


class PlanIn(BaseModel):
    appointment_id: int
    openid: str = "demo-openid"
    lead_hours: int = 24


@router.post("/plan")
def create_plan(body: PlanIn) -> dict[str, Any]:
    try:
        plan = reminder_service.create_plan(
            body.appointment_id, body.openid, body.lead_hours
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"ok": True, **plan}


@router.post("/dispatch")
def dispatch(force_fail: bool = False) -> dict[str, Any]:
    """force_fail=true 用来演示降级链：假装微信通道挂了。"""
    return {"ok": True, **reminder_service.dispatch_due(force_fail=force_fail)}


@router.post("/send/{appointment_id}")
def send_one(appointment_id: int, force_fail: bool = False) -> dict[str, Any]:
    return {"ok": True, **reminder_service.send_one(appointment_id, force_fail)}


@router.get("/outbox")
def outbox(limit: int = 30) -> dict[str, Any]:
    return {
        "ok": True,
        "channel": build_primary_gateway().channel,
        "template_configured": bool(WX_TEMPLATE_ID),
        "items": reminder_service.list_outbox(limit),
    }
