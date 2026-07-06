#!/bin/bash

# Job Application Automation Runner
# 职位申请自动化运行脚本

echo "🤖 职位申请自动化工具"
echo "========================="

# Check if Chrome debug mode is running
if ! pgrep -f "remote-debugging-port=9222" > /dev/null; then
    echo "⚠️  Chrome调试模式未运行"
    echo "请先运行: ./start_chrome_debug.sh"
    echo "然后在浏览器中登录并打开职位申请页面"
    exit 1
fi

echo "✅ 检测到Chrome调试模式正在运行"

# Check if chromedriver exists
CHROMEDRIVER_PATH="$HOME/.local/bin/chromedriver-linux64/chromedriver"
if [ ! -f "$CHROMEDRIVER_PATH" ]; then
    echo "⚠️  ChromeDriver未找到"
    echo "正在安装ChromeDriver..."
    python3 fix_chromedriver.py
fi

echo "✅ ChromeDriver已准备就绪"

# Run the automation
echo "🚀 开始自动化流程..."
python3 simplified_working_automation.py

# Check result
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 自动化执行完成！"
    echo "💡 请检查浏览器页面并完成任何剩余步骤"
    echo ""
    echo "📋 执行的步骤:"
    echo "   ✅ 简历上传"
    echo "   ⚠️  城市选择 (可能需要手动确认)"
    echo "   ✅ 推荐理由填写"
    echo "   ✅ 提交按钮点击"
    echo ""
    echo "🔧 如果城市选择失败，请尝试高级方法:"
    echo "   python3 advanced_bypass_methods.py"
else
    echo ""
    echo "❌ 自动化执行失败"
    echo "💡 建议:"
    echo "   1. 检查Chrome浏览器是否在正确页面"
    echo "   2. 确认已登录mokahr.com"
    echo "   3. 尝试刷新页面后重新运行"
    echo "   4. 查看错误日志进行调试"
fi