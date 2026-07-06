#!/usr/bin/env python3
"""
Evidence collector - prove what exactly happens during city selection
"""

import os
import sys
import time
import json

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
        wait = WebDriverWait(driver, 10)
        
        print("✅ 成功连接到Chrome浏览器")
        return driver, wait
        
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return None, None


def collect_evidence(driver, wait):
    """Collect detailed evidence of what happens during city selection"""
    
    print("=== 收集城市选择证据 ===")
    
    evidence = {
        "initial_state": {},
        "after_focus": {},
        "after_typing": {},
        "dropdown_options": [],
        "before_click": {},
        "after_click": {},
        "javascript_events": [],
        "dom_changes": []
    }
    
    try:
        # Find the city input
        city_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder*='选择意向工作城市']")))
        
        # 1. Record initial state
        print("📊 记录初始状态...")
        evidence["initial_state"] = {
            "value": city_input.get_attribute("value"),
            "placeholder": city_input.get_attribute("placeholder"),
            "class": city_input.get_attribute("class"),
            "readonly": city_input.get_attribute("readonly"),
            "disabled": city_input.get_attribute("disabled"),
            "data_attributes": {attr: city_input.get_attribute(attr) for attr in ["data-testid", "data-cy", "data-automation"] if city_input.get_attribute(attr)}
        }
        print(f"   初始值: '{evidence['initial_state']['value']}'")
        
        # 2. Clear and focus
        print("🎯 清空并聚焦...")
        city_input.clear()
        time.sleep(0.5)
        city_input.click()
        time.sleep(1)
        
        evidence["after_focus"] = {
            "value": city_input.get_attribute("value"),
            "active_element": driver.execute_script("return document.activeElement === arguments[0];", city_input)
        }
        print(f"   聚焦后值: '{evidence['after_focus']['value']}'")
        
        # 3. Type and record
        print("⌨️  输入'深'...")
        city_input.send_keys("深")
        time.sleep(2)
        
        evidence["after_typing"] = {
            "value": city_input.get_attribute("value"),
            "input_event_fired": True  # We know this because we typed
        }
        print(f"   输入后值: '{evidence['after_typing']['value']}'")
        
        # 4. Analyze dropdown options
        print("🔍 分析下拉选项...")
        dropdown_selectors = [
            "//*[contains(text(), '深圳') and not(contains(text(), '元戎启行'))]",
            ".ant-select-item",
            "[role='option']",
            ".dropdown-item"
        ]
        
        for selector in dropdown_selectors:
            try:
                if selector.startswith("/"):
                    elements = driver.find_elements(By.XPATH, selector)
                else:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                for element in elements:
                    if element.is_displayed():
                        option_info = {
                            "text": element.text,
                            "tag": element.tag_name,
                            "class": element.get_attribute("class"),
                            "selector_used": selector,
                            "clickable": element.is_enabled(),
                            "location": element.location,
                            "size": element.size
                        }
                        evidence["dropdown_options"].append(option_info)
                        print(f"   选项: '{option_info['text']}' ({option_info['tag']})")
            except:
                continue
        
        # 5. Find target option and record before click
        print("🎯 定位目标选项...")
        target_option = None
        
        try:
            target_option = driver.find_element(By.XPATH, "//*[contains(text(), '广东·深圳市等2个地点')]")
            
            evidence["before_click"] = {
                "input_value": city_input.get_attribute("value"),
                "option_text": target_option.text,
                "option_visible": target_option.is_displayed(),
                "option_enabled": target_option.is_enabled(),
                "option_location": target_option.location
            }
            print(f"   点击前输入值: '{evidence['before_click']['input_value']}'")
            print(f"   目标选项: '{evidence['before_click']['option_text']}'")
            
        except Exception as e:
            print(f"   未找到目标选项: {e}")
            return evidence
        
        # 6. Set up JavaScript event monitoring
        print("📡 设置JavaScript事件监控...")
        
        # Inject event listeners
        driver.execute_script("""
            window.citySelectionEvents = [];
            
            var input = arguments[0];
            var originalValue = input.value;
            
            // Monitor value changes
            var observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.type === 'attributes' && mutation.attributeName === 'value') {
                        window.citySelectionEvents.push({
                            type: 'value_attribute_change',
                            timestamp: Date.now(),
                            oldValue: mutation.oldValue,
                            newValue: input.value
                        });
                    }
                });
            });
            
            observer.observe(input, {
                attributes: true,
                attributeOldValue: true,
                attributeFilter: ['value']
            });
            
            // Monitor property changes
            Object.defineProperty(input, '_value', {
                get: function() { return this.value; },
                set: function(val) {
                    window.citySelectionEvents.push({
                        type: 'value_property_set',
                        timestamp: Date.now(),
                        oldValue: this.value,
                        newValue: val
                    });
                    this.setAttribute('value', val);
                }
            });
            
            // Monitor events
            ['input', 'change', 'blur', 'focus', 'click'].forEach(function(eventType) {
                input.addEventListener(eventType, function(e) {
                    window.citySelectionEvents.push({
                        type: 'event_' + eventType,
                        timestamp: Date.now(),
                        value: input.value,
                        target: e.target.tagName
                    });
                });
            });
        """, city_input)
        
        # 7. Perform the click and monitor
        print("🖱️  执行点击并监控...")
        
        # Record exact moment before click
        pre_click_value = city_input.get_attribute("value")
        
        # Click the option
        target_option.click()
        
        # Wait and monitor changes
        time.sleep(3)
        
        # Record after click
        post_click_value = city_input.get_attribute("value")
        
        evidence["after_click"] = {
            "input_value_before": pre_click_value,
            "input_value_after": post_click_value,
            "value_changed": pre_click_value != post_click_value,
            "dropdown_still_visible": len(driver.find_elements(By.XPATH, "//*[contains(text(), '广东·深圳市等2个地点')]")) > 0
        }
        
        print(f"   点击前值: '{pre_click_value}'")
        print(f"   点击后值: '{post_click_value}'")
        print(f"   值是否改变: {evidence['after_click']['value_changed']}")
        
        # 8. Collect JavaScript events
        print("📊 收集JavaScript事件...")
        
        js_events = driver.execute_script("return window.citySelectionEvents || [];")
        evidence["javascript_events"] = js_events
        
        print(f"   捕获到 {len(js_events)} 个事件:")
        for event in js_events[-5:]:  # Show last 5 events
            print(f"     {event['type']}: {event.get('newValue', event.get('value', 'N/A'))}")
        
        # 9. Analyze DOM changes
        print("🔬 分析DOM变化...")
        
        # Check if there are any React/Vue indicators
        react_indicators = driver.execute_script("""
            var input = arguments[0];
            return {
                hasReactFiber: !!input._reactInternalFiber || !!input.__reactInternalInstance,
                hasVueInstance: !!input.__vue__,
                hasAngularScope: !!input.$scope,
                parentClasses: input.parentElement ? input.parentElement.className : '',
                hasDataReactId: !!input.getAttribute('data-reactid'),
                hasNgModel: !!input.getAttribute('ng-model')
            };
        """, city_input)
        
        evidence["dom_changes"] = react_indicators
        print(f"   React检测: {react_indicators['hasReactFiber']}")
        print(f"   Vue检测: {react_indicators['hasVueInstance']}")
        print(f"   父元素类: {react_indicators['parentClasses'][:50]}...")
        
        return evidence
        
    except Exception as e:
        print(f"❌ 证据收集失败: {e}")
        evidence["error"] = str(e)
        return evidence


def analyze_evidence(evidence):
    """Analyze collected evidence and draw conclusions"""
    
    print("\n=== 证据分析 ===")
    
    # Analysis 1: Value behavior
    print("1. 值变化行为分析:")
    
    initial_value = evidence["initial_state"]["value"]
    after_typing = evidence["after_typing"]["value"]
    after_click = evidence["after_click"]["input_value_after"]
    
    print(f"   初始值: '{initial_value}'")
    print(f"   输入后: '{after_typing}'")
    print(f"   点击后: '{after_click}'")
    
    if after_typing == "深" and after_click == "":
        print("   🔍 结论: 点击后值被清空/重置")
        print("   📝 证据: 输入'深'成功，但点击选项后变为空")
    
    # Analysis 2: JavaScript events
    print("\n2. JavaScript事件分析:")
    
    events = evidence.get("javascript_events", [])
    if events:
        print(f"   捕获到 {len(events)} 个事件")
        
        # Look for suspicious patterns
        value_sets = [e for e in events if e["type"] == "value_property_set"]
        if value_sets:
            print(f"   发现 {len(value_sets)} 次值设置操作")
            for vs in value_sets:
                print(f"     设置: '{vs['oldValue']}' -> '{vs['newValue']}'")
        
        # Look for change events after click
        change_events = [e for e in events if e["type"] == "event_change"]
        if change_events:
            print(f"   发现 {len(change_events)} 次change事件")
    else:
        print("   未捕获到JavaScript事件")
    
    # Analysis 3: Framework detection
    print("\n3. 前端框架检测:")
    
    dom_info = evidence.get("dom_changes", {})
    if dom_info.get("hasReactFiber"):
        print("   🔍 检测到: React框架")
    if dom_info.get("hasVueInstance"):
        print("   🔍 检测到: Vue框架")
    if "ant-" in dom_info.get("parentClasses", ""):
        print("   🔍 检测到: Ant Design组件库")
    
    # Analysis 4: Dropdown behavior
    print("\n4. 下拉菜单行为分析:")
    
    options = evidence.get("dropdown_options", [])
    if options:
        print(f"   找到 {len(options)} 个下拉选项")
        target_option = next((opt for opt in options if "广东·深圳市" in opt["text"]), None)
        if target_option:
            print(f"   目标选项存在: '{target_option['text']}'")
            print(f"   可点击: {target_option['clickable']}")
    
    # Final conclusion
    print("\n=== 最终结论 ===")
    
    if after_typing == "深" and after_click == "":
        print("✅ 证据确凿: 点击后值被重置")
        print("📋 可能原因:")
        print("   1. JavaScript事件处理器重置了值")
        print("   2. React/Vue组件状态管理")
        print("   3. 表单验证逻辑")
        print("   4. 防自动化机制")
        
        return True
    else:
        print("❓ 证据不足或行为异常")
        return False


def main():
    """Main evidence collection function"""
    
    print("城市选择行为证据收集器")
    print("=" * 60)
    
    driver, wait = connect_to_chrome()
    if not driver:
        return False
    
    try:
        print(f"当前页面: {driver.title}")
        
        # Collect evidence
        evidence = collect_evidence(driver, wait)
        
        # Save evidence to file
        evidence_file = "city_selection_evidence.json"
        with open(evidence_file, 'w', encoding='utf-8') as f:
            json.dump(evidence, f, ensure_ascii=False, indent=2)
        print(f"\n💾 证据已保存到: {evidence_file}")
        
        # Analyze evidence
        conclusion = analyze_evidence(evidence)
        
        print("\n浏览器保持打开供进一步检查...")
        
        return conclusion
        
    except Exception as e:
        print(f"❌ 主程序失败: {e}")
        return False


if __name__ == "__main__":
    success = main()
    
    print("\n" + "=" * 60)
    if success:
        print("🎯 证据收集完成，结论得到证实")
    else:
        print("❓ 证据收集完成，需要进一步分析")
    
    sys.exit(0 if success else 1)