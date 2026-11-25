"""基础数据接口：给小程序下拉框用。只读，不含业务判断。"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.infra.db import SessionLocal
from app.infra.meta_repository import MetaRepository

router = APIRouter(prefix="/api", tags=["基础数据"])


class ChairOut(BaseModel):
    chair_id: int
    code: str


class PatientOut(BaseModel):
    patient_id: int
    name: str
    remark: str | None = None


def _run(fn) -> Any:
    session = SessionLocal()
    try:
        return fn(MetaRepository(session))
    finally:
        session.close()


@router.get("/chairs", response_model=list[ChairOut], summary="牙椅列表")
def list_chairs() -> Any:
    return _run(lambda repo: repo.list_chairs())


@router.get("/patients", response_model=list[PatientOut], summary="患者列表")
def list_patients() -> Any:
    return _run(lambda repo: repo.list_patients())
