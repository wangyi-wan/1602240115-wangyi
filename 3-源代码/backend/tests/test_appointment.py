"""核心域单元测试：不需要数据库、不需要启动服务器。"""
from datetime import datetime, timedelta

import pytest

from app.domain.appointment import (
    Appointment,
    AppointmentStatus,
    DomainError,
)


def make(start_hour: int = 9, chair_id: int = 1, patient_id: int = 1) -> Appointment:
    start = datetime(2026, 11, 2, start_hour, 0)
    return Appointment(
        patient_id=patient_id,
        chair_id=chair_id,
        start_time=start,
        end_time=start + timedelta(minutes=30),
    )


def test_新预约的初始状态是已预约():
    assert make().status is AppointmentStatus.BOOKED


def test_确认后状态变已确认():
    appt = make()
    appt.confirm()
    assert appt.status is AppointmentStatus.CONFIRMED


def test_走完整个流程到达已完成():
    appt = make()
    appt.confirm()
    appt.arrive()
    appt.start_treatment()
    appt.finish()
    assert appt.status is AppointmentStatus.DONE


def test_已完成不能再取消():
    appt = make()
    appt.confirm()
    appt.arrive()
    appt.start_treatment()
    appt.finish()
    with pytest.raises(DomainError):
        appt.cancel_by_patient()


def test_同一牙椅时段重叠被识别():
    a = make(9)
    b = make(9)            # 完全同一时段
    c = Appointment(       # 9:15 开始，跨进来一半
        patient_id=2, chair_id=1,
        start_time=datetime(2026, 11, 2, 9, 15),
        end_time=datetime(2026, 11, 2, 9, 45),
    )
    assert a.overlaps(b) is True
    assert a.overlaps(c) is True


def test_相邻时段不算重叠():
    a = make(9)            # 09:00-09:30
    b = make(10)           # 10:00-10:30
    assert a.overlaps(b) is False


def test_不同牙椅同一时段不算重叠():
    a = make(9, chair_id=1)
    b = make(9, chair_id=2)
    assert a.overlaps(b) is False


def test_改约后冗余列month同步更新():
    appt = make()
    appt.set_start_time(datetime(2026, 12, 1, 9, 0))
    assert appt.month == "2026-12"
    assert appt.end_time == datetime(2026, 12, 1, 9, 30)


def test_结束早于开始被拒绝():
    with pytest.raises(DomainError):
        Appointment(
            patient_id=1, chair_id=1,
            start_time=datetime(2026, 11, 2, 10, 0),
            end_time=datetime(2026, 11, 2, 9, 0),
        )