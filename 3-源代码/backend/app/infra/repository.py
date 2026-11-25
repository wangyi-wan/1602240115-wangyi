"""仓储：唯一允许写 SQL 的地方（数据层）。"""
from __future__ import annotations

from datetime import datetime
from typing import Protocol

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.appointment import Appointment, AppointmentStatus


class AppointmentRepository(Protocol):
    """领域层只认识这个接口，不关心底下是 MySQL 还是内存。"""

    def find_overlapping(self, chair_id: int, start: datetime, end: datetime) -> list[Appointment]: ...

    def add(self, appt: Appointment) -> Appointment: ...


class SqlAppointmentRepository:
    """MySQL 实现。"""

    def __init__(self, session: Session) -> None:
        self.session = session

    def find_overlapping(self, chair_id: int, start: datetime, end: datetime) -> list[Appointment]:
        rows = self.session.execute(
            text(
                """
                SELECT appointment_id, patient_id, chair_id,
                       start_time, end_time, status, version
                FROM t_appointment
                WHERE chair_id = :chair_id
                  AND status NOT IN ('CANCELLED')
                  AND start_time < :end
                  AND end_time   > :start
                """
            ),
            {"chair_id": chair_id, "start": start, "end": end},
        ).mappings().all()
        return [self._to_domain(r) for r in rows]

    def add(self, appt: Appointment) -> Appointment:
        result = self.session.execute(
            text(
                """
                INSERT INTO t_appointment
                    (patient_id, chair_id, start_time, end_time, status, month, version)
                VALUES
                    (:patient_id, :chair_id, :start_time, :end_time, :status, :month, 0)
                """
            ),
            {
                "patient_id": appt.patient_id,
                "chair_id": appt.chair_id,
                "start_time": appt.start_time,
                "end_time": appt.end_time,
                "status": appt.status.value,
                "month": appt.month,
            },
        )
        appt.appointment_id = result.lastrowid
        return appt

    def find_all(self, patient_id=None, date=None, status=None) -> list[dict]:
        """查询预约列表（带患者姓名、牙椅号的富化结果），支持按条件过滤。"""
        sql = """
            SELECT a.appointment_id, a.patient_id, p.name AS patient_name,
                   a.chair_id, c.code AS chair_code,
                   a.start_time, a.end_time, a.status, a.version
            FROM t_appointment a
            LEFT JOIN t_patient pt ON pt.patient_id = a.patient_id
            LEFT JOIN t_person p   ON p.person_id = pt.patient_id
            LEFT JOIN t_dental_chair c ON c.chair_id = a.chair_id
            WHERE 1=1
        """
        params: dict = {}
        if patient_id is not None:
            sql += " AND a.patient_id = :patient_id"
            params["patient_id"] = patient_id
        if date is not None:
            sql += " AND DATE(a.start_time) = :date"
            params["date"] = date
        if status is not None:
            sql += " AND a.status = :status"
            params["status"] = status
        sql += " ORDER BY a.start_time DESC"
        rows = self.session.execute(text(sql), params).mappings().all()
        return [dict(r) for r in rows]

    def get_by_id(self, appointment_id: int):
        row = self.session.execute(
            text(
                """
                SELECT appointment_id, patient_id, chair_id,
                       start_time, end_time, status, version
                FROM t_appointment
                WHERE appointment_id = :appointment_id
                """
            ),
            {"appointment_id": appointment_id},
        ).mappings().first()
        return self._to_domain(row) if row else None

    def update_status(self, appointment_id: int, new_status: str, old_version: int) -> bool:
        """推进状态机：乐观锁更新，version 不匹配返回 False（并发冲突）。"""
        result = self.session.execute(
            text(
                """
                UPDATE t_appointment
                SET status = :status, version = version + 1
                WHERE appointment_id = :appointment_id AND version = :version
                """
            ),
            {
                "status": new_status,
                "appointment_id": appointment_id,
                "version": old_version,
            },
        )
        return result.rowcount > 0

    @staticmethod
    def _to_domain(row) -> Appointment:
        return Appointment(
            appointment_id=row["appointment_id"],
            patient_id=row["patient_id"],
            chair_id=row["chair_id"],
            start_time=row["start_time"],
            end_time=row["end_time"],
            status=AppointmentStatus(row["status"]),
            version=row["version"],
        )
