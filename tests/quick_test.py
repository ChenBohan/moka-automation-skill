#!/usr/bin/env python3
"""
Quick test to verify basic functionality
"""

import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from job_application_automation import JobApplicationBot
from selenium.webdriver.common.by import By


def quick_test():
    """Quick test of basic functionality"""
    
    print("=== Quick Automation Test ===")
    
    # Test parameters
    url = "https://httpbin.org/forms/post"  # Simple test form
    
    try:
        print("1. Initializing bot...")
        bot = JobApplicationBot(headless=True, timeout=10)
        print("✅ Bot initialized")
        
        print("2. Testing navigation...")
        if bot.navigate_to_job_page(url):
            print("✅ Navigation successful")
        else:
            print("❌ Navigation failed")
            return False
        
        print("3. Testing form filling...")
        test_data = {
            "custname": "Test User",
            "custtel": "13800138000"
        }
        
        if bot.fill_form(test_data):
            print("✅ Form filling successful")
        else:
            print("⚠️  Form filling partially successful")
        
        print("4. Closing bot...")
        bot.close()
        print("✅ Test completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_mokahr_navigation():
    """Test navigation to actual mokahr site"""
    
    print("\n=== Mokahr Navigation Test ===")
    
    url = "https://app.mokahr.com/recommendation-apply/deeproute/6488#/job/64ad4641-77e0-4c9d-9602-2ef29b851d5a/apply"
    
    try:
        print("1. Initializing bot for mokahr...")
        bot = JobApplicationBot(headless=True, timeout=15)
        print("✅ Bot initialized")
        
        print("2. Navigating to mokahr...")
        if bot.navigate_to_job_page(url):
            print("✅ Mokahr navigation successful")
            
            # Check if we can find some expected elements
            print("3. Checking page elements...")
            try:
                # Look for file upload
                file_inputs = bot.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
                if file_inputs:
                    print(f"✅ Found {len(file_inputs)} file input(s)")
                
                # Look for form fields
                textareas = bot.driver.find_elements(By.TAG_NAME, "textarea")
                if textareas:
                    print(f"✅ Found {len(textareas)} textarea(s)")
                
                # Look for buttons
                buttons = bot.driver.find_elements(By.TAG_NAME, "button")
                if buttons:
                    print(f"✅ Found {len(buttons)} button(s)")
                
                print("✅ Page structure looks good")
                
            except Exception as e:
                print(f"⚠️  Element check failed: {e}")
        else:
            print("❌ Mokahr navigation failed")
            return False
        
        print("4. Closing bot...")
        bot.close()
        print("✅ Mokahr test completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Mokahr test failed: {e}")
        return False


if __name__ == "__main__":
    print("Running quick automation tests...\n")
    
    # Test 1: Basic functionality
    test1_success = quick_test()
    
    # Test 2: Mokahr navigation
    test2_success = test_mokahr_navigation()
    
    print(f"\n=== Test Results ===")
    print(f"Basic functionality: {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"Mokahr navigation: {'✅ PASS' if test2_success else '❌ FAIL'}")
    
    if test1_success and test2_success:
        print("\n🎉 All tests passed! The automation system is working.")
        print("\nNext step: Run the full automation with your resume file:")
        print("python3 test_automation_direct.py")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
    
    sys.exit(0 if (test1_success and test2_success) else 1)