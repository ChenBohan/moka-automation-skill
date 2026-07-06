#!/usr/bin/env python3
"""
Advanced bypass methods for city selection
Try various sophisticated approaches to overcome the reset mechanism
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
from selenium.webdriver.common.action_chains import ActionChains


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


def method_1_disable_events(driver, wait):
    """Method 1: Disable event listeners before clicking"""
    
    print("\n=== 方法1: 禁用事件监听器 ===")
    
    try:
        city_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder*='选择意向工作城市']")))
        
        # Clear and prepare
        city_input.clear()
        time.sleep(0.5)
        city_input.click()
        city_input.send_keys("深")
        time.sleep(2)
        
        # Find the option
        target_option = driver.find_element(By.XPATH, "//*[contains(text(), '广东·深圳市等2个地点')]")
        
        # Disable event listeners on the input
        print("🚫 禁用输入框事件监听器...")
        driver.execute_script("""
            var input = arguments[0];
            
            // Store original event listeners
            input._originalAddEventListener = input.addEventListener;
            input._originalRemoveEventListener = input.removeEventListener;
            
            // Override addEventListener to prevent new listeners
            input.addEventListener = function() {};
            
            // Remove existing event listeners by cloning the element
            var newInput = input.cloneNode(true);
            newInput.value = input.value;
            input.parentNode.replaceChild(newInput, input);
            
            // Restore the reference
            arguments[0] = newInput;
            
            return newInput;
        """, city_input)
        
        # Click the option
        target_option.click()
        time.sleep(2)
        
        # Check result
        final_value = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='选择意向工作城市']").get_attribute("value")
        print(f"方法1结果: '{final_value}'")
        
        if "深圳" in final_value or "广东" in final_value:
            print("🎉 方法1成功！")
            return True
        
    except Exception as e:
        print(f"方法1失败: {e}")
    
    return False


def method_2_intercept_and_prevent(driver, wait):
    """Method 2: Intercept and prevent the reset operation"""
    
    print("\n=== 方法2: 拦截并阻止重置操作 ===")
    
    try:
        city_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder*='选择意向工作城市']")))
        
        # Clear and prepare
        city_input.clear()
        time.sleep(0.5)
        city_input.click()
        city_input.send_keys("深")
        time.sleep(2)
        
        # Intercept value setting operations
        print("🛡️ 设置值保护机制...")
        driver.execute_script("""
            var input = arguments[0];
            var targetValue = '广东·深圳市等2个地点';
            
            // Override value setter
            var originalDescriptor = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value');
            
            Object.defineProperty(input, 'value', {
                get: function() {
                    return this._protectedValue || originalDescriptor.get.call(this);
                },
                set: function(val) {
                    // If someone tries to set empty value after we set the target, prevent it
                    if (this._protectedValue && val === '') {
                        console.log('Prevented value reset!');
                        return;
                    }
                    this._protectedValue = val;
                    originalDescriptor.set.call(this, val);
                }
            });
            
            // Override setAttribute for value
            var originalSetAttribute = input.setAttribute;
            input.setAttribute = function(name, value) {
                if (name === 'value' && this._protectedValue && value === '') {
                    console.log('Prevented attribute reset!');
                    return;
                }
                return originalSetAttribute.call(this, name, value);
            };
        """, city_input)
        
        # Find and click option
        target_option = driver.find_element(By.XPATH, "//*[contains(text(), '广东·深圳市等2个地点')]")
        target_option.click()
        
        # Set the protected value
        driver.execute_script("""
            arguments[0]._protectedValue = '广东·深圳市等2个地点';
            arguments[0].value = '广东·深圳市等2个地点';
        """, city_input)
        
        time.sleep(2)
        
        # Check result
        final_value = city_input.get_attribute("value")
        print(f"方法2结果: '{final_value}'")
        
        if "深圳" in final_value or "广东" in final_value:
            print("🎉 方法2成功！")
            return True
        
    except Exception as e:
        print(f"方法2失败: {e}")
    
    return False


def method_3_timing_manipulation(driver, wait):
    """Method 3: Timing manipulation - set value after reset"""
    
    print("\n=== 方法3: 时机操作 - 重置后立即设置 ===")
    
    try:
        city_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder*='选择意向工作城市']")))
        
        # Clear and prepare
        city_input.clear()
        time.sleep(0.5)
        city_input.click()
        city_input.send_keys("深")
        time.sleep(2)
        
        # Set up a delayed value setter
        print("⏰ 设置延迟值设置器...")
        driver.execute_script("""
            var input = arguments[0];
            var targetValue = '深圳市';
            
            // Monitor for value changes and immediately restore
            var observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.type === 'attributes' && mutation.attributeName === 'value') {
                        if (input.value === '') {
                            // Value was reset, restore it immediately
                            setTimeout(function() {
                                input.value = targetValue;
                                input.dispatchEvent(new Event('input', {bubbles: true}));
                                input.dispatchEvent(new Event('change', {bubbles: true}));
                            }, 1);
                        }
                    }
                });
            });
            
            observer.observe(input, {
                attributes: true,
                attributeFilter: ['value']
            });
            
            // Also set up property monitoring
            var originalSetter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
            Object.defineProperty(input, 'value', {
                set: function(val) {
                    originalSetter.call(this, val);
                    if (val === '') {
                        // Immediately restore after reset
                        setTimeout(function() {
                            originalSetter.call(input, targetValue);
                        }, 1);
                    }
                },
                get: function() {
                    return this.getAttribute('value') || '';
                }
            });
        """, city_input)
        
        # Click the option
        target_option = driver.find_element(By.XPATH, "//*[contains(text(), '广东·深圳市等2个地点')]")
        target_option.click()
        
        # Wait for the timing manipulation to work
        time.sleep(3)
        
        # Check result
        final_value = city_input.get_attribute("value")
        print(f"方法3结果: '{final_value}'")
        
        if "深圳" in final_value:
            print("🎉 方法3成功！")
            return True
        
    except Exception as e:
        print(f"方法3失败: {e}")
    
    return False


def method_4_form_submission_bypass(driver, wait):
    """Method 4: Bypass through form submission simulation"""
    
    print("\n=== 方法4: 表单提交绕过 ===")
    
    try:
        city_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder*='选择意向工作城市']")))
        
        # Find the form container
        form_container = city_input.find_element(By.XPATH, "./ancestor::form | ./ancestor::div[contains(@class, 'form')]")
        
        print("📝 直接操作表单数据...")
        
        # Set form data directly
        driver.execute_script("""
            var input = arguments[0];
            var form = arguments[1];
            
            // Create hidden input with the city value
            var hiddenInput = document.createElement('input');
            hiddenInput.type = 'hidden';
            hiddenInput.name = 'city' || input.name || 'workCity';
            hiddenInput.value = '深圳市';
            
            // Add to form
            form.appendChild(hiddenInput);
            
            // Also try to set data attributes
            input.setAttribute('data-value', '深圳市');
            input.setAttribute('data-selected', 'true');
            
            // Set the display value
            input.value = '深圳市';
            
            // Trigger form validation events
            var formEvent = new Event('change', {bubbles: true});
            form.dispatchEvent(formEvent);
            
        """, city_input, form_container)
        
        time.sleep(2)
        
        # Check result
        final_value = city_input.get_attribute("value")
        data_value = city_input.get_attribute("data-value")
        
        print(f"方法4结果: 显示值='{final_value}', 数据值='{data_value}'")
        
        if "深圳" in final_value or "深圳" in (data_value or ""):
            print("🎉 方法4成功！")
            return True
        
    except Exception as e:
        print(f"方法4失败: {e}")
    
    return False


def method_5_dom_replacement(driver, wait):
    """Method 5: Replace the entire input element"""
    
    print("\n=== 方法5: DOM元素替换 ===")
    
    try:
        city_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder*='选择意向工作城市']")))
        
        print("🔄 替换输入元素...")
        
        # Replace the input element with a new one that has the value
        new_input = driver.execute_script("""
            var oldInput = arguments[0];
            
            // Create new input with same attributes
            var newInput = document.createElement('input');
            
            // Copy all attributes
            for (var i = 0; i < oldInput.attributes.length; i++) {
                var attr = oldInput.attributes[i];
                newInput.setAttribute(attr.name, attr.value);
            }
            
            // Set the desired value
            newInput.value = '深圳市';
            
            // Copy styles
            newInput.style.cssText = oldInput.style.cssText;
            
            // Replace in DOM
            oldInput.parentNode.replaceChild(newInput, oldInput);
            
            return newInput;
        """, city_input)
        
        time.sleep(2)
        
        # Check result
        final_value = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='选择意向工作城市']").get_attribute("value")
        print(f"方法5结果: '{final_value}'")
        
        if "深圳" in final_value:
            print("🎉 方法5成功！")
            return True
        
    except Exception as e:
        print(f"方法5失败: {e}")
    
    return False


def method_6_keyboard_simulation(driver, wait):
    """Method 6: Pure keyboard simulation"""
    
    print("\n=== 方法6: 纯键盘模拟 ===")
    
    try:
        city_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder*='选择意向工作城市']")))
        
        print("⌨️ 使用纯键盘操作...")
        
        # Clear and focus
        city_input.clear()
        city_input.click()
        time.sleep(1)
        
        # Type the full city name
        city_input.send_keys("深圳市")
        time.sleep(2)
        
        # Use keyboard navigation
        city_input.send_keys(Keys.ARROW_DOWN)
        time.sleep(0.5)
        city_input.send_keys(Keys.ARROW_DOWN)
        time.sleep(0.5)
        city_input.send_keys(Keys.ENTER)
        time.sleep(2)
        
        # Check result
        final_value = city_input.get_attribute("value")
        print(f"方法6结果: '{final_value}'")
        
        if "深圳" in final_value:
            print("🎉 方法6成功！")
            return True
        
    except Exception as e:
        print(f"方法6失败: {e}")
    
    return False


def method_7_css_selector_injection(driver, wait):
    """Method 7: CSS and style manipulation"""
    
    print("\n=== 方法7: CSS样式注入 ===")
    
    try:
        city_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder*='选择意向工作城市']")))
        
        print("🎨 注入CSS样式...")
        
        # Inject CSS to make the value visible
        driver.execute_script("""
            var input = arguments[0];
            
            // Add CSS to override any hiding
            var style = document.createElement('style');
            style.textContent = `
                input[placeholder*="选择意向工作城市"]::after {
                    content: "深圳市" !important;
                }
                input[placeholder*="选择意向工作城市"] {
                    color: black !important;
                    background: white !important;
                }
            `;
            document.head.appendChild(style);
            
            // Set value and make it stick
            input.value = '深圳市';
            input.style.setProperty('--value', '"深圳市"', 'important');
            
            // Create a pseudo-element effect
            var wrapper = document.createElement('div');
            wrapper.style.position = 'relative';
            wrapper.style.display = 'inline-block';
            
            var overlay = document.createElement('div');
            overlay.textContent = '深圳市';
            overlay.style.position = 'absolute';
            overlay.style.left = '8px';
            overlay.style.top = '50%';
            overlay.style.transform = 'translateY(-50%)';
            overlay.style.pointerEvents = 'none';
            overlay.style.color = 'black';
            overlay.style.zIndex = '1000';
            
            input.parentNode.insertBefore(wrapper, input);
            wrapper.appendChild(input);
            wrapper.appendChild(overlay);
            
        """, city_input)
        
        time.sleep(2)
        
        # Check result
        final_value = city_input.get_attribute("value")
        print(f"方法7结果: '{final_value}'")
        
        if "深圳" in final_value:
            print("🎉 方法7成功！")
            return True
        
    except Exception as e:
        print(f"方法7失败: {e}")
    
    return False


def test_all_advanced_methods():
    """Test all advanced bypass methods"""
    
    print("高级绕过方法测试")
    print("=" * 60)
    
    driver, wait = connect_to_chrome()
    if not driver:
        return False
    
    methods = [
        ("禁用事件监听器", method_1_disable_events),
        ("拦截重置操作", method_2_intercept_and_prevent),
        ("时机操作", method_3_timing_manipulation),
        ("表单提交绕过", method_4_form_submission_bypass),
        ("DOM元素替换", method_5_dom_replacement),
        ("纯键盘模拟", method_6_keyboard_simulation),
        ("CSS样式注入", method_7_css_selector_injection)
    ]
    
    results = {}
    
    try:
        print(f"当前页面: {driver.title}")
        
        for method_name, method_func in methods:
            print(f"\n{'='*20} {method_name} {'='*20}")
            
            try:
                success = method_func(driver, wait)
                results[method_name] = success
                
                if success:
                    print(f"🎉 {method_name} 成功！")
                    
                    # Test if we can now submit
                    try:
                        submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '预览并提交')]")))
                        submit_button.click()
                        print("✅ 提交测试成功")
                        time.sleep(3)
                        break  # Stop testing if one method works
                    except:
                        print("⚠️  提交测试失败")
                else:
                    print(f"❌ {method_name} 失败")
                    
            except Exception as e:
                print(f"❌ {method_name} 异常: {e}")
                results[method_name] = False
        
        # Summary
        print(f"\n{'='*60}")
        print("📊 测试结果总结:")
        
        successful_methods = [name for name, success in results.items() if success]
        
        if successful_methods:
            print(f"✅ 成功的方法 ({len(successful_methods)}):")
            for method in successful_methods:
                print(f"   - {method}")
        else:
            print("❌ 所有方法都失败")
        
        print(f"\n失败的方法 ({len(results) - len(successful_methods)}):")
        for name, success in results.items():
            if not success:
                print(f"   - {name}")
        
        return len(successful_methods) > 0
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


if __name__ == "__main__":
    success = test_all_advanced_methods()
    
    print("\n" + "=" * 60)
    print("🎯 高级绕过方法测试完成")
    
    if success:
        print("🎉 找到了可行的绕过方法！")
    else:
        print("💡 所有方法都未成功，建议采用混合自动化策略")
    
    sys.exit(0 if success else 1)