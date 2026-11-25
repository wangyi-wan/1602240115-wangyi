"""对外接口：只做参数校验 + 调用服务 + 转错误码，不写业务判断。"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.domain.appointment import DomainError
from app.infra.db import SessionLocal
from app.infra.repository import SqlAppointmentRepository
from app.service.appointment_service import AppointmentService

router = APIRouter(prefix="/api/appointments", tags=["预约"])


class BookRequest(BaseModel):
    patient_id: int = Field(gt=0, description="患者ID")
    chair_id: int = Field(gt=0, description="牙椅ID")
    start_time: datetime = Field(description="开始时间，如 2026-11-02T09:00:00")
    minutes: int = Field(default=30, ge=10, le=240, description="时长(分钟)")


class AppointmentResponse(BaseModel):
    appointment_id: int
    patient_id: int
    chair_id: int
    start_time: datetime
    end_time: datetime
    status: str


@router.post("", response_model=AppointmentResponse, status_code=201, summary="新建预约")
def create_appointment(req: BookRequest) -> AppointmentResponse:
    session = SessionLocal()
    try:
        service = AppointmentService(SqlAppointmentRepository(session))
        appt = service.book(req.patient_id, req.chair_id, req.start_time, req.minutes)
        session.commit()
        return AppointmentResponse(
            appointment_id=appt.appointment_id or 0,
            patient_id=appt.patient_id,
            chair_id=appt.chair_id,
            start_time=appt.start_time,
            end_time=appt.end_time,
            status=appt.status.value,
        )
    except DomainError as exc:
        session.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class AppointmentListItem(BaseModel):
    appointment_id: int
    patient_id: int
    patient_name: str | None = None
    chair_id: int
    chair_code: str | None = None
    start_time: datetime
    end_time: datetime
    status: str


class EventRequest(BaseModel):
    event: str  # CONFIRM / PATIENT_ARRIVE / START_TREATMENT / FINISH / PATIENT_CANCEL / MARK_NO_SHOW


@router.get("", response_model=list[AppointmentListItem], summary="查询预约列表")
def list_appointments(
    patient_id: int | None = None,
    date: str | None = None,
    status: str | None = None,
) -> list[dict]:
    """按患者 / 日期 / 状态过滤；都不传则返回全部（带患者姓名、牙椅号）。"""
    session = SessionLocal()
    try:
        repo = SqlAppointmentRepository(session)
        return repo.find_all(patient_id=patient_id, date=date, status=status)
    finally:
        session.close()


@router.post("/{appointment_id}/event", response_model=AppointmentResponse, summary="推进预约状态机")
def advance_appointment(appointment_id: int, body: EventRequest) -> AppointmentResponse:
    """UC-002 等：触发一个事件，按文档 4.2.3 的状态迁移表推进。

    不合法的迁移（如 DONE 再 FINISH）或并发冲突都返回 409。
    """
    session = SessionLocal()
    try:
        service = AppointmentService(SqlAppointmentRepository(session))
        appt = service.handle_event(appointment_id, body.event)
        session.commit()
        return AppointmentResponse(
            appointment_id=appt.appointment_id or 0,
            patient_id=appt.patient_id,
            chair_id=appt.chair_id,
            start_time=appt.start_time,
            end_time=appt.end_time,
            status=appt.status.value,
        )
    except DomainError as exc:
        session.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    finally:
        session.close()
