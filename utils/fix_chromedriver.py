#!/usr/bin/env python3
"""
Fix ChromeDriver installation issues
"""

import os
import sys
import requests
import zipfile
import stat
import subprocess
from pathlib import Path


def get_chrome_version():
    """Get installed Chrome version"""
    try:
        # Try different ways to get Chrome version
        commands = [
            ["google-chrome", "--version"],
            ["google-chrome-stable", "--version"],
            ["chromium-browser", "--version"],
            ["chromium", "--version"]
        ]
        
        for cmd in commands:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version_str = result.stdout.strip()
                    # Extract version number (e.g., "Google Chrome 142.0.7444.162" -> "142")
                    version_parts = version_str.split()
                    for part in version_parts:
                        if '.' in part and part[0].isdigit():
                            major_version = part.split('.')[0]
                            print(f"Found Chrome version: {version_str}")
                            return major_version
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        print("Could not determine Chrome version")
        return None
        
    except Exception as e:
        print(f"Error getting Chrome version: {e}")
        return None


def download_chromedriver(version, target_dir):
    """Download ChromeDriver for the specified version"""
    try:
        # ChromeDriver download URL pattern
        base_url = "https://chromedriver.storage.googleapis.com"
        
        # For Chrome 115+, use the new ChromeDriver API
        if int(version) >= 115:
            # Use Chrome for Testing API
            api_url = f"https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
            print(f"Fetching ChromeDriver info for Chrome {version}+...")
            
            response = requests.get(api_url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                # Find the latest version for this major version
                for version_info in reversed(data['versions']):
                    if version_info['version'].startswith(f"{version}."):
                        downloads = version_info.get('downloads', {})
                        chromedriver_info = downloads.get('chromedriver', [])
                        
                        # Find Linux x64 version
                        for driver in chromedriver_info:
                            if driver['platform'] == 'linux64':
                                download_url = driver['url']
                                print(f"Found ChromeDriver URL: {download_url}")
                                return download_chromedriver_from_url(download_url, target_dir)
        
        # Fallback: try common versions
        common_versions = [
            f"{version}.0.0.0",
            f"{version}.0.7444.175",
            f"{version}.0.7444.162"
        ]
        
        for full_version in common_versions:
            download_url = f"{base_url}/{full_version}/chromedriver_linux64.zip"
            print(f"Trying ChromeDriver version: {full_version}")
            
            try:
                response = requests.head(download_url, timeout=10)
                if response.status_code == 200:
                    print(f"Found ChromeDriver: {download_url}")
                    return download_chromedriver_from_url(download_url, target_dir)
            except:
                continue
        
        print(f"Could not find ChromeDriver for Chrome version {version}")
        return False
        
    except Exception as e:
        print(f"Error downloading ChromeDriver: {e}")
        return False


def download_chromedriver_from_url(url, target_dir):
    """Download and extract ChromeDriver from URL"""
    try:
        print(f"Downloading ChromeDriver from: {url}")
        
        # Download the zip file
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        # Create target directory
        os.makedirs(target_dir, exist_ok=True)
        
        # Save and extract zip file
        zip_path = os.path.join(target_dir, "chromedriver.zip")
        with open(zip_path, 'wb') as f:
            f.write(response.content)
        
        # Extract chromedriver
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(target_dir)
        
        # Find the chromedriver executable
        chromedriver_path = None
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                if file == 'chromedriver' and not file.endswith('.zip'):
                    chromedriver_path = os.path.join(root, file)
                    break
            if chromedriver_path:
                break
        
        if chromedriver_path:
            # Make executable
            os.chmod(chromedriver_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
            print(f"ChromeDriver installed at: {chromedriver_path}")
            
            # Clean up zip file
            os.remove(zip_path)
            
            return chromedriver_path
        else:
            print("Could not find chromedriver in extracted files")
            return False
            
    except Exception as e:
        print(f"Error downloading/extracting ChromeDriver: {e}")
        return False


def main():
    """Fix ChromeDriver installation"""
    print("=== ChromeDriver Fix Tool ===\n")
    
    # Get Chrome version
    chrome_version = get_chrome_version()
    if not chrome_version:
        print("❌ Could not detect Chrome version. Please install Chrome browser first.")
        return False
    
    # Set target directory
    target_dir = os.path.expanduser("~/.local/bin")
    os.makedirs(target_dir, exist_ok=True)
    
    # Download ChromeDriver
    print(f"\nDownloading ChromeDriver for Chrome {chrome_version}...")
    chromedriver_path = download_chromedriver(chrome_version, target_dir)
    
    if chromedriver_path:
        print(f"✅ ChromeDriver successfully installed!")
        print(f"   Path: {chromedriver_path}")
        
        # Test the driver
        try:
            result = subprocess.run([chromedriver_path, "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"   Version: {result.stdout.strip()}")
                print("\n🎉 ChromeDriver is working correctly!")
                
                # Add to PATH if not already there
                if target_dir not in os.environ.get('PATH', ''):
                    print(f"\n💡 Add {target_dir} to your PATH:")
                    print(f"   export PATH=\"{target_dir}:$PATH\"")
                
                return True
            else:
                print(f"❌ ChromeDriver test failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ ChromeDriver test failed: {e}")
            return False
    else:
        print("❌ Failed to install ChromeDriver")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)