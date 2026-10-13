# Campus AI 专属 GitHub 推送脚本
$Host.UI.RawUI.WindowTitle = "Push Campus AI to GitHub"
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "        Campus AI - GitHub 一键推送器" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Host "`n[1/2] 当前远程仓库地址：" -ForegroundColor White
git remote -v

Write-Host "`n[2/2] 正在推送到 GitHub main 分支..." -ForegroundColor Green
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n========================================================" -ForegroundColor Cyan
    Write-Host "恭喜！项目已成功完整推送到 GitHub 远程仓库！" -ForegroundColor Green
    Write-Host "========================================================" -ForegroundColor Cyan
} else {
    Write-Host "`n========================================================" -ForegroundColor Red
    Write-Host "推送未完成，可能的原因：" -ForegroundColor Yellow
    Write-Host "1. 您尚未在 GitHub 上点击 New 建立名为 Campus-AI 的空仓库；" -ForegroundColor White
    Write-Host "   创建地址：https://github.com/new" -ForegroundColor Cyan
    Write-Host "2. 需要进行浏览器账号登录授权。" -ForegroundColor White
    Write-Host "========================================================" -ForegroundColor Red
}

Write-Host "`n按任意键退出..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
