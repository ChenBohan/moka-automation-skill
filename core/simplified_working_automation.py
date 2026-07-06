#!/usr/bin/env python3
"""
Simplified working automation focusing on successful methods
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
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def connect_to_chrome():
    """Connect to existing Chrome browser"""
    
    try:
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        
        chromedriver_path = os.path.expanduser("~/.local/bin/chromedriver-linux64/chromedriver")
        service = Service(chromedriver_path)
        
        driver = webdriver.Chrome(service=service, options=chrome_options)
        wait = WebDriverWait(driver, 15)
        
        print("✅ 成功连接到Chrome浏览器")
        return driver, wait
        
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return None, None


def upload_resume(driver, wait, resume_path):
    """Upload resume file"""
    
    print(f"\n📄 上传简历: {resume_path}")
    
    try:
        if not os.path.exists(resume_path):
            print(f"❌ 简历文件不存在: {resume_path}")
            return False
        
        file_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']")))
        file_input.send_keys(resume_path)
        print("✅ 简历上传成功")
        
        print("⏳ 等待简历解析...")
        time.sleep(5)
        
        return True
        
    except Exception as e:
        print(f"❌ 简历上传失败: {e}")
        return False


def select_city_keyboard_method(driver, wait):
    """Use keyboard method that worked in testing"""
    
    print("\n🏙️ 选择工作城市: 深圳 (键盘方法)")
    
    try:
        city_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder*='选择意向工作城市']")))
        
        # Clear and prepare
        city_input.clear()
        city_input.click()
        time.sleep(1)
        
        # Type city name
        city_input.send_keys("深圳市")
        time.sleep(2)
        
        # Use arrow keys to navigate
        city_input.send_keys(Keys.ARROW_DOWN)
        time.sleep(0.5)
        city_input.send_keys(Keys.ENTER)
        time.sleep(2)
        
        # Check result
        final_value = city_input.get_attribute("value")
        print(f"城市选择结果: '{final_value}'")
        
        if "深圳" in final_value:
            print("✅ 城市选择成功")
            return True
        else:
            print("⚠️  城市选择可能未完全成功，但继续执行")
            return True  # Continue anyway
        
    except Exception as e:
        print(f"❌ 城市选择失败: {e}")
        return False


def fill_recommendation(driver, wait, recommendation_text):
    """Fill recommendation reason"""
    
    print(f"\n💭 填写推荐理由: {recommendation_text}")
    
    try:
        recommendation_field = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "textarea[placeholder*='推荐理由']")))
        
        recommendation_field.clear()
        recommendation_field.send_keys(recommendation_text)
        
        print("✅ 推荐理由填写成功")
        return True
        
    except Exception as e:
        print(f"❌ 推荐理由填写失败: {e}")
        return False


def find_and_click_submit(driver, wait):
    """Find and click submit button with multiple strategies"""
    
    print("\n🚀 查找并点击提交按钮...")
    
    # Multiple selectors to try
    submit_selectors = [
        "//button[contains(text(), '预览并提交')]",
        "//button[contains(@class, 'sd-Button-primary')]",
        "//button[contains(text(), '提交')]",
        "//input[@type='submit']",
        "//button[@type='submit']"
    ]
    
    for selector in submit_selectors:
        try:
            print(f"尝试选择器: {selector}")
            submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
            
            # Try clicking
            submit_button.click()
            print(f"✅ 使用选择器成功点击: {selector}")
            return True
            
        except Exception as e:
            print(f"选择器失败: {selector} - {e}")
            continue
    
    print("❌ 所有提交按钮选择器都失败")
    return False


def complete_workflow():
    """Complete the automation workflow"""
    
    print("🤖 简化自动化流程")
    print("=" * 50)
    
    # Configuration
    resume_path = "/home/chenbohan/Downloads/【【2026春招】自动驾驶软件_模型工程师_深圳 20-40K】张浩然 26年应届生.pdf"
    recommendation_text = "自动驾驶软件_模型工程师"
    
    # Connect
    driver, wait = connect_to_chrome()
    if not driver:
        return False
    
    try:
        print(f"当前页面: {driver.title}")
        
        # Step 1: Upload resume
        if not upload_resume(driver, wait, resume_path):
            print("❌ 简历上传失败，停止执行")
            return False
        
        # Step 2: Select city
        if not select_city_keyboard_method(driver, wait):
            print("⚠️  城市选择失败，但继续...")
        
        # Step 3: Fill recommendation
        if not fill_recommendation(driver, wait, recommendation_text):
            print("❌ 推荐理由填写失败，停止执行")
            return False
        
        # Step 4: Submit
        if not find_and_click_submit(driver, wait):
            print("❌ 提交失败")
            return False
        
        print("\n🎉 自动化流程完成！")
        print("请手动检查页面状态并完成后续步骤")
        
        return True
        
    except Exception as e:
        print(f"❌ 流程执行失败: {e}")
        return False


if __name__ == "__main__":
    success = complete_workflow()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 自动化执行完成！")
        print("💡 提示: 请检查页面并手动完成任何剩余步骤")
    else:
        print("❌ 自动化执行失败")
    
    sys.exit(0 if success else 1)