#!/usr/bin/env python3
"""
Direct automation test without interactive prompts
"""

import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from job_application_automation import JobApplicationBot


def test_automation_direct():
    """Test automation directly"""
    
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
    
    print("=== Direct Automation Test ===")
    print(f"URL: {url}")
    print(f"Resume: {resume_file}")
    print(f"City: {form_data['city']}")
    print(f"Recommendation: {form_data['recommendation']['value']}")
    print()
    
    # Check file exists
    if not os.path.exists(resume_file):
        print(f"❌ Resume file not found: {resume_file}")
        return False
    
    print("✅ Resume file found")
    
    # Initialize bot
    try:
        print("Initializing automation bot...")
        bot = JobApplicationBot(headless=False, timeout=30)
        print("✅ Bot initialized successfully")
        
        # Run automation
        print("Starting automation process...")
        success = bot.run_automation(url, resume_file, form_data)
        
        if success:
            print("🎉 Automation completed successfully!")
        else:
            print("❌ Automation failed")
        
        return success
        
    except Exception as e:
        print(f"❌ Automation failed with error: {e}")
        return False
    finally:
        try:
            bot.close()
        except:
            pass


if __name__ == "__main__":
    print("Starting direct automation test...\n")
    success = test_automation_direct()
    
    if success:
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed!")
    
    sys.exit(0 if success else 1)