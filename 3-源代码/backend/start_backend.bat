@echo off
chcp 65001 >nul
title dental-backend
cd /d C://dental//backend
echo.
echo   本机局域网 IP 如下，手机要用这个地址：
echo   ------------------------------------
ipconfig | findstr /i "IPv4"
echo   ------------------------------------
echo.
echo   手机浏览器打开：http://上面的IPv4地址:8000/docs
echo   能看到接口文档页 = 网络通，可以真机预览了
echo.
echo   这个黑窗口不能关，关了后端就停了
echo.
REM ============================================================
REM 微信订阅消息凭据（只有正式小程序才需要填；测试号留空即可）
REM 把下面三行等号后面填上你在 mp.weixin.qq.com 拿到的内容：
REM   WX_APPID      = 小程序 AppID（开发管理 → 开发设置）
REM   WX_SECRET     = 小程序 AppSecret（同上，点"生成"后复制）
REM   WX_TEMPLATE_ID= 订阅消息模板 ID（功能 → 订阅消息 → 我的模板）
REM 三项都填齐 → 自动走真微信；留空 → 自动走桩通道（不实发）
REM ============================================================
set WX_APPID=wxeec6c201a303788c
set WX_SECRET=406a32e79b...5f9
set WX_TEMPLATE_ID=1aCsuC8REMdXfsABM2cF8YYPYBDzKZhphhSepmoSEy4
C://dental//.venv//Scripts//python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
