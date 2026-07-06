#!/usr/bin/env python3
"""
Debug city dropdown to understand its structure
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


def analyze_city_dropdown(driver, wait):
    """Analyze the city dropdown structure in detail"""
    
    print("=== 分析城市下拉框结构 ===")
    
    # First, load a fresh page
    target_url = "https://app.mokahr.com/recommendation-apply/deeproute/6488#/job/64ad4641-77e0-4c9d-9602-2ef29b851d5a/apply"
    driver.get(target_url)
    time.sleep(5)
    
    # Upload file first to get the form in the right state
    print("1. 先上传文件以获得正确的表单状态...")
    resume_file = "/home/chenbohan/Downloads/【【2026春招】自动驾驶软件_模型工程师_深圳 20-40K】张浩然 26年应届生.pdf"
    
    try:
        file_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']")))
        file_input.send_keys(os.path.abspath(resume_file))
        print("   文件上传完成")
        time.sleep(8)
    except:
        print("   文件上传失败，继续分析...")
    
    # Now analyze the city dropdown
    print("\n2. 分析城市下拉框...")
    
    # Find all inputs that might be the city selector
    city_candidates = [
        "input[placeholder*='城市']",
        "input[placeholder*='工作地点']", 
        "input[placeholder*='意向']",
        "input[placeholder*='选择']"
    ]
    
    for i, selector in enumerate(city_candidates):
        print(f"\n--- 候选选择器 {i+1}: {selector} ---")
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            print(f"找到 {len(elements)} 个元素")
            
            for j, element in enumerate(elements):
                print(f"  元素 {j+1}:")
                print(f"    标签: {element.tag_name}")
                print(f"    占位符: {element.get_attribute('placeholder')}")
                print(f"    类名: {element.get_attribute('class')}")
                print(f"    ID: {element.get_attribute('id')}")
                print(f"    值: {element.get_attribute('value')}")
                print(f"    可见: {element.is_displayed()}")
                print(f"    可用: {element.is_enabled()}")
                
                # If this looks like the city input, try to interact with it
                placeholder = element.get_attribute('placeholder') or ""
                if "城市" in placeholder and element.is_displayed():
                    print(f"    >>> 这看起来是城市输入框！")
                    
                    # Try to click and see what happens
                    print(f"    尝试点击...")
                    try:
                        # Scroll to element first
                        driver.execute_script("arguments[0].scrollIntoView(true);", element)
                        time.sleep(1)
                        
                        element.click()
                        print(f"    ✅ 点击成功")
                        time.sleep(3)  # Wait for dropdown to appear
                        
                        # Now analyze what appeared
                        print(f"    分析点击后的页面变化...")
                        
                        # Look for dropdown containers
                        dropdown_selectors = [
                            ".ant-select-dropdown",
                            ".dropdown-menu",
                            ".select-dropdown", 
                            "[role='listbox']",
                            ".options-container",
                            "div[style*='position: absolute']"
                        ]
                        
                        dropdown_found = False
                        for dropdown_sel in dropdown_selectors:
                            try:
                                dropdowns = driver.find_elements(By.CSS_SELECTOR, dropdown_sel)
                                for dropdown in dropdowns:
                                    if dropdown.is_displayed():
                                        print(f"    ✅ 找到下拉容器: {dropdown_sel}")
                                        print(f"       类名: {dropdown.get_attribute('class')}")
                                        print(f"       内容预览: {dropdown.text[:100]}...")
                                        dropdown_found = True
                                        
                                        # Look for options inside this dropdown
                                        option_selectors = [
                                            ".ant-select-item",
                                            ".dropdown-item",
                                            ".option",
                                            "li",
                                            "div[role='option']"
                                        ]
                                        
                                        for opt_sel in option_selectors:
                                            try:
                                                options = dropdown.find_elements(By.CSS_SELECTOR, opt_sel)
                                                if options:
                                                    print(f"       找到 {len(options)} 个选项 ({opt_sel}):")
                                                    for k, option in enumerate(options[:5]):  # Show first 5
                                                        opt_text = option.text.strip()
                                                        if opt_text:
                                                            print(f"         选项 {k+1}: '{opt_text}'")
                                                            if "深圳" in opt_text:
                                                                print(f"         >>> 找到深圳选项！")
                                                                
                                                                # Try to click it
                                                                try:
                                                                    option.click()
                                                                    print(f"         ✅ 成功点击深圳选项")
                                                                    time.sleep(2)
                                                                    
                                                                    # Check if selection worked
                                                                    current_value = element.get_attribute('value')
                                                                    print(f"         选择后的值: '{current_value}'")
                                                                    
                                                                    return True
                                                                except Exception as e:
                                                                    print(f"         ❌ 点击深圳选项失败: {e}")
                                                    break
                                            except:
                                                continue
                                        break
                            except:
                                continue
                        
                        if not dropdown_found:
                            print(f"    ⚠️  点击后未找到下拉菜单")
                            
                            # Try to see all visible elements that might have appeared
                            print(f"    检查所有可能的新元素...")
                            all_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '深圳') or contains(text(), '广东')]")
                            if all_elements:
                                print(f"    找到包含'深圳'或'广东'的元素:")
                                for elem in all_elements[:3]:
                                    if elem.is_displayed():
                                        print(f"      - {elem.tag_name}: '{elem.text}' (类名: {elem.get_attribute('class')})")
                        
                    except Exception as e:
                        print(f"    ❌ 点击失败: {e}")
                
        except Exception as e:
            print(f"选择器 {selector} 分析失败: {e}")
    
    print("\n=== 分析完成 ===")
    return False


def main():
    """Main debug function"""
    
    print("城市下拉框调试分析")
    print("=" * 50)
    
    driver, wait = connect_to_chrome()
    if not driver:
        return False
    
    try:
        success = analyze_city_dropdown(driver, wait)
        
        if success:
            print("\n🎉 成功找到并选择了深圳选项！")
        else:
            print("\n⚠️  未能自动选择深圳，但已收集调试信息")
        
        print("\n浏览器保持打开供进一步检查...")
        
        return success
        
    except Exception as e:
        print(f"❌ 调试过程出错: {e}")
        return False


if __name__ == "__main__":
    main()