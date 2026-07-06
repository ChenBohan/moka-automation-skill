#!/usr/bin/env python3
"""
Test script for job application automation
"""

import os
import sys
import json

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from job_application_automation import JobApplicationBot


def test_basic_functionality():
    """Test basic bot functionality"""
    print("Testing JobApplicationBot basic functionality...")
    
    bot = JobApplicationBot(headless=True, timeout=10)
    
    try:
        # Test navigation to a simple page
        test_url = "https://httpbin.org/forms/post"
        if bot.navigate_to_job_page(test_url):
            print("✅ Navigation test passed")
        else:
            print("❌ Navigation test failed")
            return False
        
        # Test form filling
        test_form_data = {
            "custname": "Test User",
            "custtel": "13800138000",
            "custemail": "test@example.com"
        }
        
        if bot.fill_form(test_form_data):
            print("✅ Form filling test passed")
        else:
            print("❌ Form filling test failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    finally:
        bot.close()


def validate_config_file():
    """Validate the config template file"""
    print("Validating config template file...")
    
    config_path = "job_config_template.json"
    if not os.path.exists(config_path):
        print(f"❌ Config file not found: {config_path}")
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        required_keys = ['form_data']
        for key in required_keys:
            if key not in config:
                print(f"❌ Missing required key in config: {key}")
                return False
        
        print("✅ Config file validation passed")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in config file: {e}")
        return False
    except Exception as e:
        print(f"❌ Config validation failed: {e}")
        return False


def main():
    """Run all tests"""
    print("Running job automation tests...\n")
    
    tests = [
        ("Config File Validation", validate_config_file),
        ("Basic Bot Functionality", test_basic_functionality)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print(f"\n--- Test Summary ---")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️  Some tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)