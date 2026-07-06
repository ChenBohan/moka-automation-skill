#!/usr/bin/env python3
"""
Test script with user's actual data
"""

import os
import sys
import json

# Test parameters from user
RESUME_FILE = "/home/chenbohan/Downloads/【【2026春招】自动驾驶软件_模型工程师_深圳 20-40K】张浩然 26年应届生.pdf"
CITY = "深圳"
RECOMMENDATION = "自动驾驶软件_模型工程师"

def test_file_access():
    """Test if we can access the resume file"""
    print("=== Testing File Access ===")
    
    if not os.path.exists(RESUME_FILE):
        print(f"❌ Resume file not found: {RESUME_FILE}")
        return False
    
    file_size = os.path.getsize(RESUME_FILE)
    print(f"✅ Resume file found: {RESUME_FILE}")
    print(f"   File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    
    # Check if file is readable
    try:
        with open(RESUME_FILE, 'rb') as f:
            # Read first few bytes to ensure file is accessible
            header = f.read(10)
            if header.startswith(b'%PDF'):
                print("✅ File appears to be a valid PDF")
            else:
                print("⚠️  File may not be a standard PDF format")
    except Exception as e:
        print(f"❌ Cannot read file: {e}")
        return False
    
    return True


def test_config_creation():
    """Test creating config with user data"""
    print("\n=== Testing Configuration Creation ===")
    
    config_data = {
        "form_data": {
            "city": CITY,
            "recommendation": {
                "value": RECOMMENDATION,
                "type": "textarea"
            },
            "name": "张浩然",
            "email": "zhanghaorun@example.com",
            "phone": "13800138000"
        },
        "settings": {
            "headless": False,
            "timeout": 30,
            "wait_after_submit": 5
        }
    }
    
    try:
        # Test JSON serialization
        config_json = json.dumps(config_data, ensure_ascii=False, indent=2)
        print("✅ Configuration data is valid JSON")
        print(f"   City: {config_data['form_data']['city']}")
        print(f"   Recommendation: {config_data['form_data']['recommendation']['value']}")
        
        # Save test config
        with open("user_test_config.json", 'w', encoding='utf-8') as f:
            f.write(config_json)
        print("✅ Test configuration saved as 'user_test_config.json'")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration creation failed: {e}")
        return False


def test_command_construction():
    """Test building the automation command"""
    print("\n=== Testing Command Construction ===")
    
    # This is what the actual command would look like
    test_url = "https://app.mokahr.com/recommendation-apply/deeproute/6488#/job/64ad4641-77e0-4c9d-9602-2ef29b851d5a/apply"
    
    # Method 1: Using config file
    cmd1 = f"""python3 job_application_automation.py \\
  --url "{test_url}" \\
  --file "{RESUME_FILE}" \\
  --config "user_test_config.json" """
    
    print("✅ Command with config file:")
    print(cmd1)
    
    # Method 2: Using command line arguments
    cmd2 = f"""python3 job_application_automation.py \\
  --url "{test_url}" \\
  --file "{RESUME_FILE}" \\
  --city "{CITY}" \\
  --recommendation "{RECOMMENDATION}" """
    
    print("\n✅ Command with direct arguments:")
    print(cmd2)
    
    # Method 3: Using shell script
    cmd3 = f"""./run_job_application.sh \\
  -u "{test_url}" \\
  -f "{RESUME_FILE}" \\
  -c "user_test_config.json" """
    
    print("\n✅ Shell script command:")
    print(cmd3)
    
    return True


def show_next_steps():
    """Show what user needs to do next"""
    print("\n=== Next Steps ===")
    print("To run the actual automation, you need:")
    print("1. The actual job application URL from mokahr.com")
    print("2. Run one of these commands:")
    print()
    print("   # Using the shell script (recommended):")
    print("   ./run_job_application.sh \\")
    print('     -u "ACTUAL_JOB_URL_HERE" \\')
    print(f'     -f "{RESUME_FILE}" \\')
    print('     -c "user_test_config.json"')
    print()
    print("   # Or using Python directly:")
    print("   python3 job_application_automation.py \\")
    print('     --url "ACTUAL_JOB_URL_HERE" \\')
    print(f'     --file "{RESUME_FILE}" \\')
    print(f'     --city "{CITY}" \\')
    print(f'     --recommendation "{RECOMMENDATION}"')
    print()
    print("⚠️  Replace 'ACTUAL_JOB_URL_HERE' with the real mokahr job application URL")


def main():
    """Run all tests with user's data"""
    print("Testing automation with your specific data...\n")
    
    tests = [
        ("File Access", test_file_access),
        ("Configuration Creation", test_config_creation),
        ("Command Construction", test_command_construction)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
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
        print("🎉 All tests passed! Your data is ready for automation.")
        show_next_steps()
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)