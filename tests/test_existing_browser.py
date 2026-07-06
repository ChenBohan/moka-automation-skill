#!/usr/bin/env python3
"""
Test connecting to existing Chrome browser (non-interactive)
"""

import os
import sys
import time

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


def test_chrome_connection():
    """Test connection to existing Chrome browser"""
    
    print("=== 测试连接现有Chrome浏览器 ===")
    print("假设Chrome已在调试模式运行...")
    
    try:
        # Connect to existing Chrome instance
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        
        # Use local chromedriver
        chromedriver_path = os.path.expanduser("~/.local/bin/chromedriver-linux64/chromedriver")
        service = Service(chromedriver_path)
        
        print("正在连接到Chrome调试端口9222...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("✅ 成功连接到现有Chrome浏览器")
        
        # Get current page info
        current_url = driver.current_url
        page_title = driver.title
        
        print(f"当前页面URL: {current_url}")
        print(f"页面标题: {page_title}")
        
        return driver
        
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return None


def test_navigation_and_automation(driver):
    """Test navigation and automation on existing browser"""
    
    if not driver:
        return False
    
    try:
        # Target URL
        target_url = "https://app.mokahr.com/recommendation-apply/deeproute/6488#/job/64ad4641-77e0-4c9d-9602-2ef29b851d5a/apply"
        
        print(f"\n📍 导航到目标页面...")
        print(f"URL: {target_url}")
        
        # Navigate to target page
        driver.get(target_url)
        time.sleep(5)  # Wait for page load
        
        print("✅ 页面导航完成")
        
        # Check page content
        print("\n🔍 检查页面内容...")
        
        # Look for key elements
        elements_found = {}
        
        # Check for file upload
        try:
            file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
            elements_found['file_upload'] = len(file_inputs)
            print(f"   文件上传控件: {len(file_inputs)}个")
        except:
            elements_found['file_upload'] = 0
        
        # Check for textareas
        try:
            textareas = driver.find_elements(By.TAG_NAME, "textarea")
            elements_found['textareas'] = len(textareas)
            print(f"   文本框: {len(textareas)}个")
        except:
            elements_found['textareas'] = 0
        
        # Check for buttons
        try:
            buttons = driver.find_elements(By.TAG_NAME, "button")
            elements_found['buttons'] = len(buttons)
            print(f"   按钮: {len(buttons)}个")
        except:
            elements_found['buttons'] = 0
        
        # Check for inputs
        try:
            inputs = driver.find_elements(By.TAG_NAME, "input")
            elements_found['inputs'] = len(inputs)
            print(f"   输入框: {len(inputs)}个")
        except:
            elements_found['inputs'] = 0
        
        # Test file upload if available
        resume_file = "/home/chenbohan/Downloads/【【2026春招】自动驾驶软件_模型工程师_深圳 20-40K】张浩然 26年应届生.pdf"
        
        if elements_found['file_upload'] > 0 and os.path.exists(resume_file):
            print(f"\n📄 测试文件上传...")
            
            try:
                file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
                if file_input.is_displayed():
                    print(f"   上传文件: {os.path.basename(resume_file)}")
                    file_input.send_keys(os.path.abspath(resume_file))
                    print("✅ 文件上传命令已发送")
                    
                    # Wait for upload processing
                    print("   等待文件处理...")
                    time.sleep(8)
                    print("✅ 文件处理完成")
                else:
                    print("⚠️  文件上传控件不可见")
            except Exception as e:
                print(f"❌ 文件上传失败: {e}")
        
        # Test form filling
        print(f"\n✍️  测试表单填写...")
        
        # Try to fill city
        city_selectors = [
            "input[placeholder*='城市']",
            "input[placeholder*='工作地点']",
            "input[placeholder*='意向']"
        ]
        
        city_filled = False
        for selector in city_selectors:
            try:
                city_input = driver.find_element(By.CSS_SELECTOR, selector)
                if city_input.is_displayed() and city_input.is_enabled():
                    city_input.clear()
                    city_input.send_keys("深圳")
                    print("✅ 城市填写成功: 深圳")
                    city_filled = True
                    break
            except:
                continue
        
        if not city_filled:
            print("⚠️  未找到城市输入框")
        
        # Try to fill recommendation
        recommendation_selectors = [
            "textarea[placeholder*='推荐理由']",
            "textarea[placeholder*='自我介绍']",
            "textarea[placeholder*='请简单介绍']"
        ]
        
        recommendation_filled = False
        for selector in recommendation_selectors:
            try:
                rec_input = driver.find_element(By.CSS_SELECTOR, selector)
                if rec_input.is_displayed() and rec_input.is_enabled():
                    rec_input.clear()
                    rec_input.send_keys("自动驾驶软件_模型工程师")
                    print("✅ 推荐理由填写成功")
                    recommendation_filled = True
                    break
            except:
                continue
        
        if not recommendation_filled:
            print("⚠️  未找到推荐理由输入框")
        
        print(f"\n📊 测试结果总结:")
        print(f"   页面导航: ✅")
        print(f"   文件上传: {'✅' if elements_found['file_upload'] > 0 else '❌'}")
        print(f"   城市填写: {'✅' if city_filled else '⚠️'}")
        print(f"   推荐理由: {'✅' if recommendation_filled else '⚠️'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 自动化测试失败: {e}")
        return False


def main():
    """Main test function"""
    
    print("测试现有浏览器自动化功能")
    print("=" * 50)
    
    # Test connection
    driver = test_chrome_connection()
    
    if not driver:
        print("\n❌ 无法连接到Chrome浏览器")
        print("请确保Chrome已在调试模式运行:")
        print("google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome_debug")
        return False
    
    # Test automation
    success = test_navigation_and_automation(driver)
    
    if success:
        print("\n🎉 自动化测试完成!")
        print("浏览器将保持打开状态，您可以继续手动操作")
    else:
        print("\n❌ 自动化测试失败")
    
    # Keep browser open - don't quit driver
    print("\n浏览器保持打开状态...")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)