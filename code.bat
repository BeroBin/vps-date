
@echo off
REM 设置代码页为UTF-8
chcp 65001 >nul

echo 开始运行批处理文件...
echo 当前目录: %cd%
echo.

REM 检查Python安装
echo 检查Python安装...
py -3 --version
if %ERRORLEVEL% neq 0 (
    echo Python未正确安装或py命令不可用
    echo 尝试使用python命令...
    python --version
    if %ERRORLEVEL% neq 0 (
        echo Python未安装或未添加到PATH
        echo 请先安装Python并添加到PATH
        pause
        exit /b 1
    )
    set PYTHON_CMD=python
) else (
    set PYTHON_CMD=py -3
)
echo.

REM 检查脚本文件是否存在
echo 检查脚本文件...
if not exist "vps_manager.py" (
    echo 错误：找不到 vps_manager.py 文件
    echo 请确保该文件存在于当前目录
    pause
    exit /b 1
)
echo 找到 vps_manager.py 文件
echo.

REM 设置环境变量
echo 设置环境变量...
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
set PYTHONLEGACYWINDOWSSTDIO=utf-8
echo 环境变量设置完成
echo.

REM 运行脚本
echo 运行脚本...
%PYTHON_CMD% vps_manager.py

REM 检查运行结果
if %ERRORLEVEL% neq 0 (
    echo.
    echo 运行失败！错误代码：%ERRORLEVEL%
    echo 请检查Python安装和脚本是否正确。
    echo.
) else (
    echo.
    echo 脚本运行完成
    echo.
)

echo 按任意键退出...
pause