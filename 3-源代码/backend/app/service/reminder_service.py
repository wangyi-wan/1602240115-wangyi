"""提醒应用服务：把「预约」和「消息通道」缝在一起。

职责边界：
  - 这里知道「什么时候发、发给谁、失败了怎么办」
  - 它不知道微信怎么发，那件事归 infra/message_gateway.py
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import text

from app.infra.db import SessionLocal
from app.infra.message_gateway import (
    FALLBACK_CHAIN,
    ReminderMessage,
    build_primary_gateway,
)

# 提前多久提醒（文档 UC-003：提前 24 小时）
LEAD_HOURS = 24


def create_plan(appointment_id: int, openid: str = "demo-openid",
                lead_hours: int = LEAD_HOURS) -> dict[str, Any]:
    """预约成功后调一次。同一个预约重复调不会插两遍（UNIQUE 兜底）。"""
    with SessionLocal() as s:
        row = s.execute(
            text("SELECT start_time FROM t_appointment WHERE appointment_id = :id"),
            {"id": appointment_id},
        ).mappings().first()
        if row is None:
            raise ValueError(f"预约 {appointment_id} 不存在")

        start: datetime = row["start_time"]
        send_at = start - timedelta(hours=lead_hours)

        # 已经建过就直接返回，保证幂等
        exist = s.execute(
            text("SELECT plan_id, plan_send_at, status FROM t_reminder_plan WHERE appointment_id = :id"),
            {"id": appointment_id},
        ).mappings().first()
        if exist:
            return {
                "plan_id": exist["plan_id"],
                "plan_send_at": exist["plan_send_at"],
                "status": exist["status"],
                "reused": True,
            }

        res = s.execute(
            text(
                "INSERT INTO t_reminder_plan "
                "(appointment_id, openid, channel, plan_send_at, status) "
                "VALUES (:aid, :openid, 'WECHAT', :send_at, 'PENDING')"
            ),
            {"aid": appointment_id, "openid": openid, "send_at": send_at},
        )
        s.commit()
        return {
            "plan_id": res.lastrowid,
            "plan_send_at": send_at,
            "status": "PENDING",
            "reused": False,
        }


def _load_message(appointment_id: int) -> ReminderMessage | None:
    """把数据库里的预约，翻译成一条待发消息。"""
    with SessionLocal() as s:
        row = s.execute(
            text(
                """
                SELECT a.appointment_id, p.name AS patient_name,
                       a.start_time, c.code AS chair_code, rp.openid
                FROM t_appointment a
                JOIN t_person  p  ON p.person_id  = a.patient_id
                JOIN t_dental_chair c ON c.chair_id = a.chair_id
                JOIN t_reminder_plan rp ON rp.appointment_id = a.appointment_id
                WHERE a.appointment_id = :id
                """
            ),
            {"id": appointment_id},
        ).mappings().first()

    if row is None:
        return None

    start: datetime = row["start_time"]
    return ReminderMessage(
        openid=row["openid"] or "demo-openid",
        patient_name=row["patient_name"],
        visit_time=start.strftime("%Y-%m-%d %H:%M"),
        place=f"{row['chair_code']} 牙椅",
    )


def _write_log(plan_id: int | None, appointment_id: int, channel: str,
               title: str, content: str, result: str, reason: str) -> None:
    with SessionLocal() as s:
        s.execute(
            text(
                "INSERT INTO t_reminder_log "
                "(plan_id, appointment_id, channel, title, content, result, fail_reason) "
                "VALUES (:pid, :aid, :ch, :title, :content, :res, :reason)"
            ),
            {
                "pid": plan_id,
                "aid": appointment_id,
                "ch": channel,
                "title": title,
                "content": content[:250],
                "res": result,
                "reason": (reason or "")[:250],
            },
        )
        s.commit()


def send_one(appointment_id: int, force_fail: bool = False) -> dict[str, Any]:
    """给某个预约发提醒。主通道失败就按降级链往下走。

    force_fail=True 用来演示降级链：假装主通道挂了，
    就能在小程序里看到「微信失败 → 短信 → 人工外呼」三步。
    返回每一步的尝试记录。
    """
    msg = _load_message(appointment_id)
    if msg is None:
        return {"appointment_id": appointment_id, "error": "预约或提醒计划不存在"}

    with SessionLocal() as s:
        plan = s.execute(
            text("SELECT plan_id FROM t_reminder_plan WHERE appointment_id = :id"),
            {"id": appointment_id},
        ).mappings().first()
    plan_id = plan["plan_id"] if plan else None

    content = f"{msg.visit_time} 到 {msg.place} 就诊，请准时到达"
    attempts: list[dict[str, str]] = []
    final = "FAIL"

    gateway = build_primary_gateway()
    result, reason = gateway.send(msg)
    if force_fail:
        result, reason = "FAIL", "（演示用）模拟主通道故障"
    attempts.append({"channel": gateway.channel, "result": result, "reason": reason})
    _write_log(plan_id, appointment_id, gateway.channel, "就诊提醒", content, result, reason)

    # OK 真送达 / STUB 桩送达（等价于送达）→ 到此为止
    if result in ("OK", "STUB"):
        final = result
    else:
        # 主通道失败 → 走降级链（文档 UC-003 扩展路径 6a）
        for fb in FALLBACK_CHAIN:
            r2, why = fb.send(msg)
            if force_fail and r2 != "MANUAL":
                # 演示模式下，除了最后的人工外呼，前面都假装失败，好把整条链走完
                r2, why = "FAIL", "（演示用）模拟该通道故障"
            attempts.append({"channel": fb.channel, "result": r2, "reason": why})
            _write_log(plan_id, appointment_id, fb.channel, "就诊提醒（降级）", content, r2, why)
            final = r2
            if r2 in ("OK", "STUB", "MANUAL"):
                break

    new_status = "SENT" if final in ("OK", "STUB") else ("MANUAL" if final == "MANUAL" else "FAILED")
    with SessionLocal() as s:
        s.execute(
            text(
                "UPDATE t_reminder_plan SET status = :st, channel = :ch "
                "WHERE appointment_id = :id"
            ),
            {"st": new_status, "ch": attempts[-1]["channel"], "id": appointment_id},
        )
        s.commit()

    return {
        "appointment_id": appointment_id,
        "patient_name": msg.patient_name,
        "content": content,
        "final": final,
        "attempts": attempts,
    }


def dispatch_due(now: datetime | None = None, limit: int = 50,
                 force_fail: bool = False) -> dict[str, Any]:
    """扫一遍：把到点该发、还没发的都发出去。

    正常情况由定时任务每小时调一次（手册 9.4）；
    答辩演示时直接调接口手动触发，不用等。
    """
    now = now or datetime.now()
    with SessionLocal() as s:
        rows = s.execute(
            text(
                "SELECT appointment_id FROM t_reminder_plan "
                "WHERE status = 'PENDING' AND plan_send_at <= :now "
                "ORDER BY plan_send_at LIMIT :lim"
            ),
            {"now": now, "lim": limit},
        ).mappings().all()

    sent = [send_one(r["appointment_id"], force_fail=force_fail) for r in rows]
    return {"checked_at": now.isoformat(timespec="seconds"),
            "due_count": len(rows), "results": sent}


def list_outbox(limit: int = 30) -> list[dict[str, Any]]:
    """最近发出去（或降级）的提醒，给小程序展示用。"""
    with SessionLocal() as s:
        rows = s.execute(
            text(
                "SELECT log_id, appointment_id, channel, title, content, "
                "       result, fail_reason, sent_at "
                "FROM t_reminder_log ORDER BY log_id DESC LIMIT :lim"
            ),
            {"lim": limit},
        ).mappings().all()
    return [
        {
            "log_id": r["log_id"],
            "appointment_id": r["appointment_id"],
            "channel": r["channel"],
            "title": r["title"],
            "content": r["content"],
            "result": r["result"],
            "fail_reason": r["fail_reason"],
            "sent_at": r["sent_at"].strftime("%m-%d %H:%M:%S"),
        }
        for r in rows
    ]
