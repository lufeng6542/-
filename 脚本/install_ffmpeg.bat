@echo off
chcp 65001 >nul
echo ============================================
echo   FFmpeg 安装脚本 (Windows)
echo ============================================
echo.

:: 方法1: 使用winget安装 (推荐)
echo 方法1: 使用Windows包管理器安装
echo 正在检查winget...
where winget >nul 2>&1
if %errorlevel% equ 0 (
    echo 找到winget，正在安装FFmpeg...
    winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
    echo.
    echo ✅ FFmpeg安装完成！
    echo 请关闭当前命令行窗口，重新打开后使用。
    goto :end
)

:: 方法2: 使用pip安装imageio-ffmpeg
echo.
echo 方法2: 使用Python安装FFmpeg绑定
pip install imageio-ffmpeg
python -c "import imageio_ffmpeg; print(f'FFmpeg路径: {imageio_ffmpeg.get_ffmpeg_exe()}')"
echo.

:: 方法3: 手动安装提示
echo.
echo ============================================
echo 如果以上方法失败，请手动安装:
echo.
echo 1. 访问 https://www.gyan.dev/ffmpeg/builds/
echo 2. 下载 "ffmpeg-release-essentials.zip"
echo 3. 解压到 C:\ffmpeg
echo 4. 将 C:\ffmpeg\bin 添加到系统PATH
echo ============================================

:end
echo.
pause
