#!/usr/bin/env python3
"""
Final working automation using successful bypass methods
Based on the successful methods from advanced_bypass_methods.py
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


TARGET_URL = "https://app.mokahr.com/recommendation-apply/deeproute/6488#/job/64ad4641-77e0-4c9d-9602-2ef29b851d5a/apply"


def connect_to_chrome():
    """Connect to existing Chrome browser and open a new tab"""
    
    try:
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        
        chromedriver_path = os.path.expanduser("~/.local/bin/chromedriver-linux64/chromedriver")
        service = Service(chromedriver_path)
        
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✅ Connected to Chrome browser")
        
        # Open a new tab and switch to it (CDP method is most reliable)
        driver.switch_to.new_window('tab')
        
        # Navigate to the target URL
        print(f"🌐 Navigating to: {TARGET_URL}")
        driver.get(TARGET_URL)
        time.sleep(3)
        print(f"✅ Page loaded: {driver.title}")
        
        wait = WebDriverWait(driver, 10)
        return driver, wait
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None, None


def upload_resume(driver, wait, resume_path):
    """Upload resume file"""
    
    print(f"📄 Uploading resume: {resume_path}")
    
    try:
        if not os.path.exists(resume_path):
            print(f"❌ Resume file not found: {resume_path}")
            return False
        
        file_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']")))
        file_input.send_keys(resume_path)
        print("✅ Resume uploaded")
        
        # Wait for resume parsing and form rendering
        print("⏳ Waiting for resume parsing...")
        time.sleep(1)  # 减少简历解析等待时间
        
        return True
        
    except Exception as e:
        print(f"❌ Resume upload failed: {e}")
        return False


def select_city_robust(driver, wait):
    """Select city using dropdown click method"""
    
    print("🏙️ Selecting city: 深圳")
    
    try:
        # Try standard placeholder selector first
        city_input = None
        city_selectors = [
            "input[placeholder*='选择意向工作城市']",
            "input[placeholder*='城市']",
            "input[placeholder*='意向']",
        ]
        
        for sel in city_selectors:
            try:
                city_input = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                print(f"  Found city input with selector: {sel}")
                break
            except:
                continue
        
        # Fallback: find by form label text
        if city_input is None:
            city_input = driver.execute_script("""
                var labels = document.querySelectorAll('label, [class*="label"], [class*="Label"], [class*="title"], [class*="Title"]');
                for (var i = 0; i < labels.length; i++) {
                    var text = labels[i].textContent || '';
                    if (text.includes('意向工作城市') || text.includes('意向城市') || text.includes('工作城市')) {
                        var container = labels[i].closest('[class*="FormItem"]') || labels[i].closest('[class*="form-item"]') || labels[i].parentElement;
                        if (container) {
                            var input = container.querySelector('input[type="text"]');
                            if (input) return input;
                            input = container.querySelector('input');
                            if (input) return input;
                        }
                    }
                }
                return null;
            """)
            if city_input:
                print("  Found city input via form label search")
        
        # Last fallback: XPath
        if city_input is None:
            try:
                city_label = driver.find_element(By.XPATH, "//*[contains(text(), '意向工作城市') or contains(text(), '意向城市')]")
                parent = city_label.find_element(By.XPATH, "./ancestor::*[.//input[@type='text']]")
                city_input = parent.find_element(By.CSS_SELECTOR, "input[type='text']")
                print("  Found city input via XPath label search")
            except:
                pass
        
        if city_input is None:
            print("  ❌ Could not find city input")
            return False
        
        # Scroll to and click city input to open dropdown
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", city_input)
        time.sleep(0.5)
        city_input.click()
        time.sleep(1)
        
        # Find the dropdown
        dropdowns = driver.find_elements(By.CSS_SELECTOR, "[class*='dropdown']")
        visible_dropdowns = [d for d in dropdowns if d.is_displayed()]
        
        if not visible_dropdowns:
            print("  ⚠️ No dropdown found after clicking")
            return False
        
        dd = visible_dropdowns[0]
        
        # Find and click 深圳 option
        options = dd.find_elements(By.XPATH, ".//*[contains(text(), '深圳')]")
        for opt in options:
            if opt.is_displayed():
                opt.click()
                print("  ✅ Clicked '深圳市' option")
                time.sleep(1)
                
                # Verify selection by checking visible DOM elements
                shenzhen_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '深圳') and not(self::script)]")
                visible_sz = [e for e in shenzhen_elements if e.is_displayed()]
                if visible_sz:
                    print("✅ City selection successful")
                    return True
                break
        
        print("  ❌ Could not find/click 深圳 option")
        return False
        
    except Exception as e:
        print(f"❌ City selection failed: {e}")
        return False


def fill_recommendation(driver, wait, recommendation_text):
    """Fill recommendation reason"""
    
    print(f"💭 Filling recommendation: {recommendation_text}")
    
    try:
        recommendation_field = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "textarea[placeholder*='推荐理由']")))
        recommendation_field.clear()
        recommendation_field.send_keys(Keys.CONTROL + "a")
        recommendation_field.send_keys(recommendation_text)
        
        print("✅ Recommendation filled")
        return True
        
    except Exception as e:
        print(f"❌ Recommendation fill failed: {e}")
        return False


def _capture_page_feedback(driver):
    """Capture visible page content/feedback after submission"""
    
    # Get the main visible text content of the page body
    try:
        body_text = driver.execute_script("""
            // Get main content area text (exclude nav/header/footer)
            var main = document.querySelector('main, [class*="content"], [class*="Content"], [class*="result"], [class*="Result"], [class*="thanks"], [class*="Thanks"]');
            if (main) return main.innerText.trim();
            
            // Fallback: get body text but filter out noise
            var body = document.body.innerText.trim();
            // Return first 500 chars
            return body.substring(0, 500);
        """)
        return body_text if body_text else None
    except:
        return None


def submit_application(driver, wait):
    """Submit the application: click preview+submit, then confirm"""
    
    print("🚀 Submitting application...")
    
    # Step 1: Find and click "预览并提交" button
    try:
        submit_selectors = [
            "//button[contains(text(), '预览并提交')]",
            "//button[contains(text(), '提交')]",
            "//button[contains(@class, 'sd-Button-primary')]",
        ]
        
        submit_button = None
        for sel in submit_selectors:
            try:
                btns = driver.find_elements(By.XPATH, sel)
                visible_btns = [b for b in btns if b.is_displayed()]
                if visible_btns:
                    submit_button = visible_btns[0]
                    break
            except:
                continue
        
        if not submit_button:
            print("  ❌ Could not find submit button")
            return False
        
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_button)
        time.sleep(0.5)
        
        try:
            submit_button.click()
        except:
            driver.execute_script("arguments[0].click();", submit_button)
        
        print("  ✅ Clicked '预览并提交'")
        
    except Exception as e:
        print(f"  ❌ Failed to click submit button: {e}")
        return False
    
    # Step 2: Wait 1s for confirmation page, then click "确认提交"
    try:
        time.sleep(1)
        
        # Find "确认提交" button
        confirm_button = None
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        visible_buttons = [b for b in all_buttons if b.is_displayed()]
        
        for b in visible_buttons:
            btn_text = b.text.strip()
            if "确认提交" in btn_text:
                confirm_button = b
                break
        
        if not confirm_button:
            for b in visible_buttons:
                btn_text = b.text.strip()
                if "确认" in btn_text and "预览" not in btn_text:
                    confirm_button = b
                    break
        
        if not confirm_button:
            print("  ⚠️ Could not find confirm button")
            return False
        
        try:
            confirm_button.click()
        except:
            driver.execute_script("arguments[0].click();", confirm_button)
        
        print(f"  ✅ Clicked '{confirm_button.text.strip()}'")
        
        # Capture page feedback after submission
        time.sleep(2)
        feedback = _capture_page_feedback(driver)
        if feedback:
            print(f"  📢 Page feedback: {feedback}")
        
        print("✅ Application submitted successfully!")
        return True, feedback
        
    except Exception as e:
        print(f"  ❌ Failed to confirm submission: {e}")
        return False


def complete_automation():
    """Complete automation workflow - opens a new tab each run"""
    
    print("🤖 Starting automation workflow")
    print("=" * 50)
    
    # Configuration
    resume_path = "/home/chenbohan/Downloads/【【2026春招】自动驾驶软件_模型工程师_深圳 20-40K】张浩然 26年应届生.pdf"
    recommendation_text = "自动驾驶软件_模型工程师"
    
    # Connect to browser (opens a new tab automatically)
    driver, wait = connect_to_chrome()
    if not driver:
        return False
    
    try:
        # Step 1: Upload resume
        if not upload_resume(driver, wait, resume_path):
            return False
        
        # Step 2: Select city
        city_result = select_city_robust(driver, wait)
        if not city_result:
            print("⚠️ City selection failed, continuing...")
        
        # Step 3: Fill recommendation
        if not fill_recommendation(driver, wait, recommendation_text):
            print("⚠️ Recommendation filling failed, continuing...")
        
        # Step 4: Submit application
        submit_result, feedback = submit_application(driver, wait)
        if not submit_result:
            return False, None
        
        print("\n🎉 Automation completed!")
        return True, feedback
        
    except Exception as e:
        print(f"❌ Automation failed: {e}")
        return False


if __name__ == "__main__":
    success, feedback = complete_automation()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Success!")
    else:
        print("❌ Failed")
    
    sys.exit(0 if success else 1)
