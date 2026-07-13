@echo off
chcp 65001 >nul
set HOOK_DIR=.git\hooks

echo ===================================================
echo   Labelme 进度统计 - Git Hooks 自动配置脚本
echo ===================================================
echo.

if not exist "%HOOK_DIR%" (
    echo [错误] 未在该目录下检测到 .git 目录。
    echo 请确认这是项目的 Git 仓库根目录。
    echo.
    pause
    exit /b 1
)

echo 正在写入 Git pre-commit 钩子...
(
    echo #!/bin/sh
    echo echo "==================================================="
    echo echo "   正在自动统计标注进度并更新 README.md... "
    echo echo "==================================================="
    echo python update_readme.py
) > "%HOOK_DIR%\pre-commit"

echo [成功] Git pre-commit 自动统计钩子配置完成！
echo.
echo 提示：以后您（及其他合作者）在执行 git commit 时，
echo 进度统计脚本会自动运行，并将更新后的 README.md 和折线图一并提交。
echo.
pause
