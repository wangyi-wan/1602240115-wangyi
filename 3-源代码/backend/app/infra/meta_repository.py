"""基础数据仓储：牙椅、患者等下拉列表的只读查询（无业务规则，不经过领域层）。"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


class MetaRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_chairs(self) -> list[dict]:
        rows = self.session.execute(
            text("SELECT chair_id, code FROM t_dental_chair ORDER BY chair_id")
        ).mappings().all()
        return [dict(r) for r in rows]

    def list_patients(self) -> list[dict]:
        rows = self.session.execute(
            text(
                """
                SELECT pt.patient_id, p.name, pt.remark
                FROM t_patient pt
                JOIN t_person p ON p.person_id = pt.patient_id
                ORDER BY pt.patient_id
                """
            )
        ).mappings().all()
        return [dict(r) for r in rows]
