"""登录接口：小程序用 wx.login 拿 code，后端换 openid。

为什么需要它：微信订阅消息必须发给「真实 openid」。
之前作业简化版登录只存了假的 demo-token，没有 openid，
所以消息网关即使配了真凭据，也只能发往一个不存在的 openid。

这一步把「真 openid」补齐：
  小程序 wx.login → code → 本接口 → 微信 jscode2session → openid
然后小程序把 openid 存本地，预约时一起发给提醒计划接口。

测试号没有 AppSecret，jscode2session 会失败——此时本接口返回 200 + demo openid，
小程序据此走桩通道（不存真实 openid，提醒走桩），不弹红字、不影响登录主流程。
"""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.infra.message_gateway import WX_APPID, WX_SECRET

log = logging.getLogger("auth")
router = APIRouter(prefix="/api/auth", tags=["auth"])


class CodeIn(BaseModel):
    code: str


@router.post("/login")
def login(body: CodeIn) -> dict:
    if not (WX_APPID and WX_SECRET):
        # 没配凭据（测试号 / 还没填 bat）：不报错，直接给 demo openid，
        # 前端据此走桩通道，登录主流程不受影响、也不弹红字。
        return {"ok": True, "openid": "demo-openid", "token": "demo-token",
                "stub": True}

    url = (
        "https://api.weixin.qq.com/sns/jscode2session"
        f"?appid={WX_APPID}&secret={WX_SECRET}"
        f"&js_code={body.code}&grant_type=authorization_code"
    )
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError) as exc:
        raise HTTPException(status_code=502, detail=f"微信接口调用失败: {exc}")

    if "openid" not in data:
        # errcode/errmsg 都在，典型是 invalid appsecret（测试号）
        raise HTTPException(status_code=400, detail=str(data))

    openid = data["openid"]
    # 课程作业简化：token 直接复用 openid；生产环境应签发 JWT
    return {"ok": True, "openid": openid, "token": "tok-" + openid}
