# Campus AI 专属 PowerShell 一键启动器
$Host.UI.RawUI.WindowTitle = "Campus AI — AI 校园恋爱物语"
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "       Campus AI — AI 校园恋爱物语 正在启动..." -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 1. 启动后端
Write-Host "[1/2] 正在启动游戏后端 (FastAPI - Port 8000)..." -ForegroundColor Green
Start-Process -FilePath "cmd.exe" -ArgumentList "/k cd /d `"$scriptDir\backend`" && python run.py"

# 2. 启动前端
Write-Host "[2/2] 正在启动游戏前端 (Vite - Port 5173)..." -ForegroundColor Green
Start-Process -FilePath "cmd.exe" -ArgumentList "/k cd /d `"$scriptDir\frontend`" && npx vite --open"

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "游戏服务已全部拉起！" -ForegroundColor Yellow
Write-Host "前端界面: http://127.0.0.1:5173" -ForegroundColor White
Write-Host "接口文档: http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "按任意键退出本窗口（后台游戏进程将继续保持运行）..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
