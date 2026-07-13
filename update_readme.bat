@echo off
chcp 65001 >nul
echo ===================================================
echo   Labelme 进度统计 - 手动更新脚本
echo ===================================================
echo.

:: 自动检测并静默配置 Git Hook 钩子
set HOOK_FILE=.git\hooks\pre-commit
if not exist "%HOOK_FILE%" (
    if exist ".git" (
        echo [提示] 检测到您的本地未配置 Git Commit 自动触发钩子。
        echo 正在为您自动安装配置，以便将来 commit 时能自动更新统计...
        
        :: 确保 hooks 文件夹存在
        if not exist ".git\hooks" mkdir ".git\hooks"
        
        (
            echo #!/bin/sh
            echo echo "==================================================="
            echo echo "   正在自动统计标注进度并更新 README.md... "
            echo echo "==================================================="
            echo python update_readme.py
        ) > "%HOOK_FILE%"
        echo [提示] 自动更新钩子安装成功！
        echo.
    )
)

echo 正在扫描图片和标签文件，重新计算进度并渲染图表...
python update_readme.py

echo.
echo ===================================================
echo [完成] README.md 与 progress_chart.svg 更新成功！
echo ===================================================
echo.
pause
