"""消息网关（边界类）。

这一层是「外部系统」的适配器：领域层只认 MessageGateway 这个接口，
不知道微信、短信、人工外呼的存在。换通道 = 换一个实现类，业务代码一行不动。

这正是文档 4.3.2「依赖倒置」和 4.3.3「外系统接口约定」要的东西。

三种实现：
  WechatSubscribeGateway  真实微信订阅消息（需要 AppID + AppSecret + 模板ID）
  StubGateway             桩：只写日志和数据库，不发真实消息
  ManualCallGateway       人工外呼：生成一条待办，由前台打电话

当前你用的是小程序测试号（没有 AppSecret、不能配模板），
所以 MESSAGE_CHANNEL 留空即自动走 StubGateway —— 流程照样完整，只是不实发。
等你注册了正式小程序，把下面三个环境变量填上，同一份代码立刻变成真推送。
"""
from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass

log = logging.getLogger("reminder")

# ------------------------------------------------------------------
# 通道开关：这三个都填了才走真微信，否则自动降级为桩
# Windows 上临时设置（当前窗口有效）：
#   set WX_APPID=wx123
#   set WX_SECRET=xxxx
#   set WX_TEMPLATE_ID=AbC...
# ------------------------------------------------------------------
WX_APPID = os.getenv("WX_APPID", "")
WX_SECRET = os.getenv("WX_SECRET", "")
WX_TEMPLATE_ID = os.getenv("WX_TEMPLATE_ID", "")


@dataclass
class ReminderMessage:
    """要发出去的一条提醒。字段名固定，各通道自己翻译成自己的格式。"""

    openid: str
    patient_name: str
    visit_time: str   # 形如 2026-11-03 09:00
    place: str        # 形如 A1 牙椅


class MessageGateway(ABC):
    """所有消息通道的父类。返回值统一是 (结果, 原因)。"""

    channel = "BASE"

    @abstractmethod
    def send(self, msg: ReminderMessage) -> tuple[str, str]:
        """结果取值：OK / FAIL / STUB / MANUAL"""


class WechatSubscribeGateway(MessageGateway):
    """微信小程序订阅消息（一次性订阅）。

    限制：用户必须在小程序里点过一次「允许」，才能发一条；发完要再授权。
    """

    channel = "WECHAT"
    _token: dict = {"value": None, "expire_at": 0.0}

    def _access_token(self) -> str:
        import time

        if self._token["value"] and time.time() < self._token["expire_at"]:
            return self._token["value"]

        url = (
            "https://api.weixin.qq.com/cgi-bin/token"
            f"?grant_type=client_credential&appid={WX_APPID}&secret={WX_SECRET}"
        )
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if "access_token" not in data:
            raise RuntimeError(f"获取 access_token 失败: {data}")

        self._token["value"] = data["access_token"]
        # 提前 5 分钟过期，避免边界上拿到失效 token
        self._token["expire_at"] = time.time() + data.get("expires_in", 7200) - 300
        return self._token["value"]

    def send(self, msg: ReminderMessage) -> tuple[str, str]:
        if not (WX_APPID and WX_SECRET and WX_TEMPLATE_ID):
            return "FAIL", "未配置 AppID/AppSecret/模板ID"

        payload = {
            "touser": msg.openid,
            "template_id": WX_TEMPLATE_ID,
            "page": "pages/home/home",
            "data": {
                "thing1": {"value": msg.patient_name[:20]},
                "time2": {"value": msg.visit_time},
                "thing3": {"value": msg.place[:20]},
            },
        }
        try:
            token = self._access_token()
            url = (
                "https://api.weixin.qq.com/cgi-bin/message/subscribe/send"
                f"?access_token={token}"
            )
            req = urllib.request.Request(
                url,
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            if data.get("errcode") == 0:
                return "OK", ""
            return "FAIL", f"{data.get('errcode')} {data.get('errmsg')}"
        except (urllib.error.URLError, RuntimeError, TimeoutError) as exc:
            return "FAIL", str(exc)


class StubGateway(MessageGateway):
    """桩通道：只在日志和 t_reminder_log 里留痕，不真的发。

    用途：测试号 / 个人主体没开通订阅消息权限时，用它把整条链路跑通。
    答辩说法：「外部通道以桩实现，接口不变，生产环境填入凭据即生效」。
    """

    channel = "STUB"

    def send(self, msg: ReminderMessage) -> tuple[str, str]:
        text = (
            f"[桩通道] 本应发给 {msg.patient_name}（{msg.openid}）："
            f"{msg.visit_time} 到 {msg.place} 就诊，请准时到达"
        )
        log.warning(text)
        print(text, flush=True)
        return "STUB", "未接入真实通道（测试号/未配置凭据），仅记录"


class SmsGateway(MessageGateway):
    """短信降级通道。真实项目接阿里云/腾讯云短信，这里同样是桩。"""

    channel = "SMS"

    def send(self, msg: ReminderMessage) -> tuple[str, str]:
        text = f"[短信桩] 向 {msg.patient_name} 的手机发送：{msg.visit_time} {msg.place} 就诊提醒"
        log.warning(text)
        print(text, flush=True)
        return "STUB", "短信通道未接入，仅记录"


class ManualCallGateway(MessageGateway):
    """最后兜底：生成人工外呼任务，由前台打电话。"""

    channel = "MANUAL"

    def send(self, msg: ReminderMessage) -> tuple[str, str]:
        text = f"[人工外呼] 请前台致电 {msg.patient_name}，提醒 {msg.visit_time} 到 {msg.place} 就诊"
        log.warning(text)
        print(text, flush=True)
        return "MANUAL", "已生成人工外呼任务"


def build_primary_gateway() -> MessageGateway:
    """主通道：凭据齐全就走真微信，否则自动降级成桩。"""
    if WX_APPID and WX_SECRET and WX_TEMPLATE_ID:
        return WechatSubscribeGateway()
    return StubGateway()


# 降级链：微信失败 → 短信 → 人工外呼。文档 UC-003 扩展路径 6a 写的就是这条链
FALLBACK_CHAIN = [SmsGateway(), ManualCallGateway()]
