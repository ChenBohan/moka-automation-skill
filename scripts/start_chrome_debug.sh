#!/bin/bash

# Start Chrome in debug mode for automation

echo "=== Chrome调试模式启动脚本 ==="
echo

# Kill existing Chrome processes
echo "1. 关闭现有Chrome进程..."
pkill -f chrome 2>/dev/null || true
pkill -f chromium 2>/dev/null || true
sleep 2

# Clean up debug profile
echo "2. 清理调试配置文件..."
rm -rf /tmp/chrome_debug 2>/dev/null || true

# Find Chrome executable
CHROME_EXE=""
CHROME_PATHS=(
    "/usr/bin/google-chrome"
    "/usr/bin/google-chrome-stable"
    "/usr/bin/chromium-browser"
    "/snap/bin/chromium"
)

for path in "${CHROME_PATHS[@]}"; do
    if [ -f "$path" ]; then
        CHROME_EXE="$path"
        break
    fi
done

if [ -z "$CHROME_EXE" ]; then
    echo "❌ 未找到Chrome浏览器"
    echo "请安装Chrome或Chromium浏览器"
    exit 1
fi

echo "3. 找到Chrome: $CHROME_EXE"

# Start Chrome with debugging enabled
echo "4. 启动Chrome调试模式..."
echo "   - 远程调试端口: 9222"
echo "   - 配置文件: /tmp/chrome_debug"
echo

$CHROME_EXE \
    --remote-debugging-port=9222 \
    --user-data-dir=/tmp/chrome_debug \
    --no-first-run \
    --no-default-browser-check \
    --disable-extensions-except \
    --disable-plugins-discovery \
    > /dev/null 2>&1 &

CHROME_PID=$!

echo "✅ Chrome已启动 (PID: $CHROME_PID)"
echo
echo "📋 接下来请："
echo "1. 在Chrome中登录mokahr网站"
echo "2. 导航到招聘页面"
echo "3. 在另一个终端运行: python3 use_current_tab.py"
echo
echo "按Ctrl+C停止Chrome调试模式"

# Wait for interrupt
trap "echo; echo '停止Chrome调试模式...'; kill $CHROME_PID 2>/dev/null; exit 0" INT

# Keep script running
while kill -0 $CHROME_PID 2>/dev/null; do
    sleep 1
done

echo "Chrome进程已结束"