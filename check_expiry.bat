@echo off
REM 设置代码页为UTF-8
chcp 65001 >nul

REM 设置环境变量
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
set PYTHONLEGACYWINDOWSSTDIO=utf-8

REM 运行检测脚本
py -3 vps_monitor.py

REM 如果运行失败，显示错误信息并暂停
if %ERRORLEVEL% neq 0 (
    echo 运行失败！错误代码：%ERRORLEVEL%
    echo 请检查Python安装和脚本是否正确。
    pause
) 