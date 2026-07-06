#!/usr/bin/env python3
"""
Visual test with browser window for observation
"""

import os
import sys
import time

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from job_application_automation import JobApplicationBot


def visual_test():
    """Visual test with browser window"""
    
    # Test parameters
    url = "https://app.mokahr.com/recommendation-apply/deeproute/6488#/job/64ad4641-77e0-4c9d-9602-2ef29b851d5a/apply"
    resume_file = "/home/chenbohan/Downloads/【【2026春招】自动驾驶软件_模型工程师_深圳 20-40K】张浩然 26年应届生.pdf"
    
    form_data = {
        "city": "深圳",
        "recommendation": {
            "value": "自动驾驶软件_模型工程师",
            "type": "textarea"
        }
    }
    
    print("=== 可视化自动化测试 ===")
    print("浏览器窗口将会弹出，您可以观察整个自动化过程")
    print()
    print(f"目标URL: {url}")
    print(f"简历文件: {resume_file}")
    print(f"城市选择: {form_data['city']}")
    print(f"推荐理由: {form_data['recommendation']['value']}")
    print()
    
    # Check file exists
    if not os.path.exists(resume_file):
        print(f"❌ 简历文件未找到: {resume_file}")
        return False
    
    print("✅ 简历文件已找到")
    print()
    
    # Initialize bot with visible browser
    try:
        print("🚀 正在初始化浏览器...")
        print("   - 浏览器窗口即将弹出")
        print("   - 请观察自动化操作过程")
        print("   - 如果遇到问题，您可以手动干预")
        print()
        
        # Use headless=False to show browser window
        bot = JobApplicationBot(headless=False, timeout=30)
        print("✅ 浏览器初始化成功")
        print()
        
        # Step 1: Navigate
        print("📍 步骤 1: 导航到招聘页面...")
        if not bot.navigate_to_job_page(url):
            print("❌ 页面导航失败")
            return False
        print("✅ 页面导航成功")
        print("   请观察: 页面是否正确加载")
        time.sleep(3)
        
        # Step 2: Upload file
        print("\n📄 步骤 2: 上传简历文件...")
        print(f"   正在上传: {os.path.basename(resume_file)}")
        if bot.upload_file(resume_file, wait_for_parsing=True):
            print("✅ 文件上传成功")
            print("   请观察: 文件是否上传并自动解析")
        else:
            print("⚠️  文件上传可能失败，请手动上传")
        time.sleep(5)
        
        # Step 3: Select city
        print("\n🏙️  步骤 3: 选择工作城市...")
        print(f"   尝试选择城市: {form_data['city']}")
        if bot.select_city(form_data['city']):
            print("✅ 城市选择成功")
        else:
            print("⚠️  自动城市选择失败")
            print("   👆 请手动选择城市: 深圳")
        time.sleep(3)
        
        # Step 4: Fill recommendation
        print("\n✍️  步骤 4: 填写推荐理由...")
        print(f"   推荐理由: {form_data['recommendation']['value']}")
        if bot.fill_form_field("recommendation", form_data['recommendation']['value'], "textarea"):
            print("✅ 推荐理由填写成功")
        else:
            print("⚠️  自动填写推荐理由失败")
            print("   👆 请手动填写推荐理由: 自动驾驶软件_模型工程师")
        time.sleep(3)
        
        # Step 5: Submit
        print("\n📋 步骤 5: 提交申请...")
        print("   正在寻找提交按钮...")
        if bot.submit_application():
            print("✅ 申请提交成功")
        else:
            print("⚠️  自动提交失败")
            print("   👆 请手动点击提交按钮")
        
        print("\n⏳ 保持浏览器窗口打开30秒，供您观察结果...")
        print("   您可以在此期间手动完成任何未完成的步骤")
        
        # Keep browser open for observation
        for i in range(30, 0, -1):
            print(f"\r   倒计时: {i:2d}秒 (您可以按Ctrl+C提前结束)", end="", flush=True)
            time.sleep(1)
        
        print("\n\n🎯 自动化测试完成")
        return True
        
    except KeyboardInterrupt:
        print("\n\n⏹️  用户中断了测试")
        return True
        
    except Exception as e:
        print(f"\n❌ 自动化测试失败: {e}")
        return False
        
    finally:
        try:
            print("\n🔒 正在关闭浏览器...")
            bot.close()
            print("✅ 浏览器已关闭")
        except:
            pass


if __name__ == "__main__":
    print("启动可视化自动化测试...")
    print("=" * 50)
    
    success = visual_test()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ 可视化测试完成!")
        print("\n📝 测试总结:")
        print("- 您已观察了完整的自动化过程")
        print("- 成功的步骤可以在实际使用中重复")
        print("- 失败的步骤需要手动完成")
    else:
        print("❌ 测试过程中出现错误")
    
    print("\n💡 使用建议:")
    print("- 脚本可以自动完成文件上传等耗时操作")
    print("- 手动完成城市选择和推荐理由填写")
    print("- 这样可以大大节省申请时间")
    
    sys.exit(0 if success else 1)