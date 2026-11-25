"""应用服务：协调领域对象与仓储，一个用例一个方法。"""
from __future__ import annotations

from datetime import datetime, timedelta

from app.domain.appointment import Appointment, AppointmentEvent, DomainError
from app.infra.repository import AppointmentRepository


class AppointmentService:
    def __init__(self, repo: AppointmentRepository) -> None:
        self.repo = repo

    def book(self, patient_id: int, chair_id: int, start: datetime, minutes: int = 30) -> Appointment:
        """UC-001 的预约：先查冲突，再落库。"""
        end = start + timedelta(minutes=minutes)
        candidate = Appointment(
            patient_id=patient_id,
            chair_id=chair_id,
            start_time=start,
            end_time=end,
        )

        # INV-1：同一把牙椅时段互斥
        for other in self.repo.find_overlapping(chair_id, start, end):
            if candidate.overlaps(other):
                raise DomainError(
                    f"牙椅 {chair_id} 在 {start:%H:%M} 已被占用，请换个时段"
                )

        return self.repo.add(candidate)

    def handle_event(self, appointment_id: int, event_name: str) -> Appointment:
        """UC-002 等：推进预约状态机（对应文档 4.2.3 的状态迁移表）。

        event_name 必须是 AppointmentEvent 的合法值（CONFIRM / PATIENT_ARRIVE /
        START_TREATMENT / FINISH / PATIENT_CANCEL / MARK_NO_SHOW），否则抛 DomainError。
        用乐观锁（version）防止并发覆盖，冲突时由调用方转 409。
        """
        appt = self.repo.get_by_id(appointment_id)
        if appt is None:
            raise DomainError(f"预约 {appointment_id} 不存在")
        try:
            event = AppointmentEvent(event_name)
        except ValueError as exc:
            raise DomainError(f"非法事件: {event_name}") from exc
        appt.fire(event)  # 不合法迁移会抛 DomainError
        ok = self.repo.update_status(appointment_id, appt.status.value, appt.version)
        if not ok:
            raise DomainError("数据已被其他人修改，请刷新后重试")
        return appt
