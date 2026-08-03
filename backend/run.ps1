# VocaAgent 后端启动脚本 (PowerShell)
# 使用 Conda 环境 Python，不依赖全局 Python

$VOCA_PYTHON = "C:\Users\myqf8\.conda\envs\vocaagent\python.exe"

if (-not (Test-Path $VOCA_PYTHON)) {
    Write-Host "[错误] Conda 环境未找到: $VOCA_PYTHON" -ForegroundColor Red
    exit 1
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "[VocaAgent] 使用 Conda 环境: $VOCA_PYTHON" -ForegroundColor Cyan

# 如果命令行有参数就透传
if ($args.Count -gt 0) {
    & $VOCA_PYTHON $args
} else {
    & $VOCA_PYTHON app.py
}
