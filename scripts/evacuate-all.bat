@echo off
chcp 65001 >nul
title 一键撤离爆破（公司机 · 全量）
echo ============================================================
echo   一键撤离爆破脚本（公司机 → 家用机）
echo   作用：撤离前一次性完成——
echo     ① 全部 git 仓库 push 干净
echo     ② 安鼎记忆/会话/产出加密快照
echo     ③ 快照 push 到私有仓 hermes-recovery
echo     ④ 密钥/明文安全检查
echo   执行时间约 2-5 分钟，中途不要关窗口。
echo ============================================================
echo.

set HERMES=%LOCALAPPDATA%\hermes
set SEVENZ=%~dp07zr.exe
set STAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%
set STAMP=%STAMP: =0%
set LOG=%~dp0evacuate-log-%STAMP%.txt
set FAIL=0

echo [启动] 日志: %LOG%
echo ====== EVACUATE %STAMP% ====== > "%LOG%"

rem ---------- 前置检查 ----------
echo.
echo [0/5] 前置检查...
if not exist "%SEVENZ%" (
    echo [错误] 找不到 7zr.exe，请把本脚本放在 U 盘 hermes-deploy 文件夹里运行。
    echo [错误] 找不到 7zr.exe >> "%LOG%"
    pause
    exit /b 1
)
git --version >nul 2>&1
if errorlevel 1 (
    echo [错误] git 不可用。
    echo [错误] git 不可用 >> "%LOG%"
    pause
    exit /b 1
)
gh auth status >nul 2>&1
if errorlevel 1 (
    echo [警告] gh 未登录或 token 无效 —— push 可能失败，继续尝试。
    echo [警告] gh 未登录或 token 无效 >> "%LOG%"
)

rem ---------- ① 全仓库 push ----------
echo.
echo [1/5] 全仓库 push 干净...
set REPOS=adaptive-digital-team he-weizhi-site hermes-skills hermes-recovery
for %%R in (%REPOS%) do (
    if exist "%USERPROFILE%\%%R" (
        echo   ── %%R ──
        pushd "%USERPROFILE%\%%R" >nul 2>&1
        echo   [%%R] 当前分支:
        git branch --show-current 2>&1
        git add -A >nul 2>&1
        git commit -m "evacuate checkpoint %STAMP%" >nul 2>&1
        git push 2>&1
        if errorlevel 1 (
            echo   [%%R] push 失败! >> "%LOG%"
            set FAIL=1
        ) else (
            echo   [%%R] push OK >> "%LOG%"
        )
        popd >nul 2>&1
    ) else (
        echo   [跳过] %%R 不存在（%USERPROFILE%\%%R）
    )
)

rem ---------- ② 收集安鼎数据 ----------
echo.
echo [2/5] 收集安鼎记忆/会话/产出...
mkdir "%TEMP%\hermes-recovery" >nul 2>&1
set ANYDATA=0
if exist "%HERMES%\memories" (
    xcopy /e /i /q /y "%HERMES%\memories" "%TEMP%\hermes-recovery\memories" >nul
    echo   [收集] memories
    set ANYDATA=1
)
if exist "%HERMES%\state.db" (
    copy /y "%HERMES%\state.db" "%TEMP%\hermes-recovery\state.db" >nul
    echo   [收集] state.db
    set ANYDATA=1
)
if exist "%HERMES%\profiles\anding\config.yaml" (
    copy /y "%HERMES%\profiles\anding\config.yaml" "%TEMP%\hermes-recovery\anding-config.yaml" >nul
    echo   [收集] anding/config.yaml
    set ANYDATA=1
)
if exist "%HERMES%\profiles\anding\SOUL.md" (
    copy /y "%HERMES%\profiles\anding\SOUL.md" "%TEMP%\hermes-recovery\anding-SOUL.md" >nul
    echo   [收集] anding/SOUL.md
    set ANYDATA=1
)
if exist "%HERMES%\cron\output" (
    xcopy /e /i /q /y "%HERMES%\cron\output" "%TEMP%\hermes-recovery\cron-output" >nul
    echo   [收集] cron/output
    set ANYDATA=1
)
if "%ANYDATA%"=="0" (
    echo   [跳过] 无安鼎数据可收集（可能 Hermes 未初始化）
)

rem ---------- ③ 加密快照 ----------
echo.
echo [3/5] 加密快照（AES-256）...
echo   输入加密密码（与密钥包相同，输入时不显示）：
for /f "usebackq delims=" %%p in (`powershell -NoProfile -Command "$s=Read-Host -AsSecureString; [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($s))"`) do set "PASS=%%p"
if not defined PASS (
    echo [错误] 未输入密码，中止。
    echo [错误] 未输入密码 >> "%LOG%"
    rmdir /s /q "%TEMP%\hermes-recovery" >nul 2>&1
    pause
    exit /b 1
)
"%SEVENZ%" a -p"%PASS%" -mhe=on -t7z "%~dp0hermes-recovery-%STAMP%.7z" "%TEMP%\hermes-recovery\*" -y >nul
if errorlevel 1 (
    echo [错误] 加密失败。
    echo [错误] 加密失败 >> "%LOG%"
    rmdir /s /q "%TEMP%\hermes-recovery" >nul 2>&1
    pause
    exit /b 1
)
echo   [OK] 快照: hermes-recovery-%STAMP%.7z
echo   [OK] 快照: hermes-recovery-%STAMP%.7z >> "%LOG%"
rmdir /s /q "%TEMP%\hermes-recovery" >nul 2>&1
