"""核心域：预约。这一层不知道数据库、HTTP、框架的存在。"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class DomainError(Exception):
    """业务规则被违反时抛出。"""


class AppointmentStatus(str, Enum):
    BOOKED = "BOOKED"            # 已预约
    CONFIRMED = "CONFIRMED"      # 已确认
    ARRIVED = "ARRIVED"          # 已到诊
    IN_PROGRESS = "IN_PROGRESS"  # 诊疗中
    DONE = "DONE"                # 已完成
    CANCELLED = "CANCELLED"      # 已取消
    NO_SHOW = "NO_SHOW"          # 失约


class AppointmentEvent(str, Enum):
    CONFIRM = "CONFIRM"
    PATIENT_ARRIVE = "PATIENT_ARRIVE"
    START_TREATMENT = "START_TREATMENT"
    FINISH = "FINISH"
    PATIENT_CANCEL = "PATIENT_CANCEL"
    MARK_NO_SHOW = "MARK_NO_SHOW"


# 状态迁移表：这就是文档 4.2.3 说的“唯一真相”
_TRANSITIONS: dict[tuple[AppointmentStatus, AppointmentEvent], AppointmentStatus] = {
    (AppointmentStatus.BOOKED, AppointmentEvent.CONFIRM): AppointmentStatus.CONFIRMED,
    (AppointmentStatus.BOOKED, AppointmentEvent.PATIENT_ARRIVE): AppointmentStatus.ARRIVED,
    (AppointmentStatus.BOOKED, AppointmentEvent.PATIENT_CANCEL): AppointmentStatus.CANCELLED,
    (AppointmentStatus.BOOKED, AppointmentEvent.MARK_NO_SHOW): AppointmentStatus.NO_SHOW,
    (AppointmentStatus.CONFIRMED, AppointmentEvent.PATIENT_ARRIVE): AppointmentStatus.ARRIVED,
    (AppointmentStatus.CONFIRMED, AppointmentEvent.PATIENT_CANCEL): AppointmentStatus.CANCELLED,
    (AppointmentStatus.CONFIRMED, AppointmentEvent.MARK_NO_SHOW): AppointmentStatus.NO_SHOW,
    (AppointmentStatus.ARRIVED, AppointmentEvent.START_TREATMENT): AppointmentStatus.IN_PROGRESS,
    (AppointmentStatus.IN_PROGRESS, AppointmentEvent.FINISH): AppointmentStatus.DONE,
}


@dataclass
class Appointment:
    patient_id: int
    chair_id: int
    start_time: datetime
    end_time: datetime
    status: AppointmentStatus = AppointmentStatus.BOOKED
    appointment_id: int | None = None
    version: int = 0
    _fired: list[AppointmentEvent] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        if self.end_time <= self.start_time:
            raise DomainError("结束时间必须晚于开始时间")

    @property
    def month(self) -> str:
        """冗余列 YYYY-MM，只有这一个地方计算它。"""
        return self.start_time.strftime("%Y-%m")

    def overlaps(self, other: "Appointment") -> bool:
        """INV-1：同一把牙椅的时段不能重叠。"""
        if self.chair_id != other.chair_id:
            return False
        return self.start_time < other.end_time and other.start_time < self.end_time

    def fire(self, event: AppointmentEvent) -> None:
        """唯一的状态变更入口：任何迁移都必须过这张表。"""
        key = (self.status, event)
        if key not in _TRANSITIONS:
            raise DomainError(f"状态 {self.status.value} 不接受事件 {event.value}")
        self.status = _TRANSITIONS[key]
        self._fired.append(event)

    def set_start_time(self, start: datetime, minutes: int = 30) -> None:
        """改约。冗余列 month 随之更新，调用方不用管。"""
        if self.status not in (AppointmentStatus.BOOKED, AppointmentStatus.CONFIRMED):
            raise DomainError("只有未到诊的预约才能改时间")
        self.start_time = start
        self.end_time = start + timedelta(minutes=minutes)

    # 对外只暴露“诊所的语言”，事件枚举是内部实现
    def confirm(self) -> None:
        self.fire(AppointmentEvent.CONFIRM)

    def arrive(self) -> None:
        self.fire(AppointmentEvent.PATIENT_ARRIVE)

    def start_treatment(self) -> None:
        self.fire(AppointmentEvent.START_TREATMENT)

    def finish(self) -> None:
        self.fire(AppointmentEvent.FINISH)

    def cancel_by_patient(self) -> None:
        self.fire(AppointmentEvent.PATIENT_CANCEL)

    def mark_no_show(self) -> None:
        self.fire(AppointmentEvent.MARK_NO_SHOW)