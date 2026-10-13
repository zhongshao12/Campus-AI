@echo off
title Push Campus AI to GitHub
cd /d "%~dp0"

echo ========================================================
echo        Campus AI - GitHub 一键推送脚本
echo ========================================================
echo.
echo 目标远程仓库:
git remote -v
echo.
echo 正在推送到 GitHub main 分支...
git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo 推送成功！已同步至 GitHub 仓库。
    echo ========================================================
) else (
    echo.
    echo ========================================================
    echo 推送未完成，请检查：
    echo 1. 是否已在 GitHub 上创建名为 Campus-AI 的空仓库？
    echo    (访问 https://github.com/new 即可新建)
    echo 2. 若仓库名字不同，可输入以下命令修改远程地址：
    echo    git remote set-url origin https://github.com/zhongshao12/<你的仓库名>.git
    echo ========================================================
)
echo.
pause
