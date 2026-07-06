#!/usr/bin/env python3
"""
基于JSON配置文件进行简历提交
接受简历文件夹路径和JSON配置文件，直接执行自动提交
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import automation functions
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core'))
from final_working_automation import upload_resume, select_city_robust, fill_recommendation, submit_application

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException


class JSONBasedSubmitter:
    """基于JSON配置的简历提交器"""
    
    def __init__(self, job_descriptions_file: str):
        self.job_urls = self._load_job_urls(job_descriptions_file)
        self.results = []
    
    def _load_job_urls(self, file_path: str) -> Dict[str, str]:
        """加载职位URL映射"""
        job_urls = {}
        
        print(f"🔍 Loading job URLs from: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析职位URL
        import re
        job_blocks = re.split(r'【\d+[年春招]+】', content)[1:]
        
        for block in job_blocks:
            lines = block.strip().split('\n')
            if not lines:
                continue
                
            job_title = lines[0].strip()
            submit_url = ""
            
            for line in lines[1:]:
                line = line.strip()
                if line.startswith('提交地址：'):
                    submit_url = line.replace('提交地址：', '').strip()
                    break
            
            if submit_url:
                job_urls[job_title] = submit_url
        
        print(f"✅ Loaded {len(job_urls)} job URLs")
        for job_title, url in job_urls.items():
            print(f"  📌 {job_title}: {url}")
        
        return job_urls
    
    def _connect_to_chrome(self):
        """连接到Chrome浏览器"""
        try:
            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
            chromedriver_path = os.path.expanduser("~/.local/bin/chromedriver-linux64/chromedriver")
            service = Service(chromedriver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print("✅ Connected to Chrome browser")

            # 使用CDP打开新标签页
            driver.switch_to.new_window('tab')
            print("✅ Opened new tab")

            wait = WebDriverWait(driver, 15)
            return driver, wait
        except Exception as e:
            print(f"❌ Chrome connection failed: {e}")
            return None, None
    
    def _select_city_smart(self, driver, wait, city_name: str, job_title: str) -> bool:
        """Auto-detect city field and select the configured city, skip if not present"""
        print(f"🏙️ Checking if city selection is needed for: {job_title}")

        try:
            # Try to find city input field
            city_input = None
            city_selectors = [
                "input[placeholder*='选择意向工作城市']",
                "input[placeholder*='城市']",
                "input[placeholder*='意向']",
            ]

            for sel in city_selectors:
                try:
                    city_input = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
                    )
                    print(f"  Found city input with selector: {sel}")
                    break
                except:
                    continue

            if city_input is None:
                print(f"ℹ️ No city selection field found for '{job_title}', skipping...")
                return True

            print(f"🏙️ Selecting city: {city_name}")
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

            # Find and click city option (skip menu headers)
            options = dd.find_elements(By.XPATH, f".//*[contains(text(), '{city_name}')]")
            
            # Try each option, skip menu headers and prioritize actual options
            clicked_successfully = False
            for opt in options:
                if opt.is_displayed():
                    try:
                        # Check if this is a menu header (should be skipped)
                        class_name = opt.get_attribute("class") or ""
                        bg_color = driver.execute_script("return window.getComputedStyle(arguments[0]).backgroundColor;", opt)
                        text_color = driver.execute_script("return window.getComputedStyle(arguments[0]).color;", opt)
                        
                        # Skip menu headers/group titles
                        is_header = (
                            "header" in class_name.lower() or
                            "rgb(244, 246, 251)" in bg_color or  # Light gray background
                            "rgb(152, 156, 178)" in text_color   # Gray text color
                        )
                        
                        if is_header:
                            continue
                        
                        # Try to click this option
                        opt.click()
                        print(f"  ✅ Clicked '{city_name}' option")
                        time.sleep(1)

                        # Verify selection by checking visible DOM elements
                        verify_elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{city_name}') and not(self::script)]")
                        visible_verify = [e for e in verify_elements if e.is_displayed()]
                        
                        if visible_verify:
                            print("✅ City selection successful")
                            clicked_successfully = True
                            break
                            
                    except Exception as e:
                        continue
            
            if not clicked_successfully:
                print(f"  ❌ Could not find/click valid '{city_name}' option")
                return False
            
            return True

            print(f"  ❌ Could not find/click '{city_name}' option")
            return False

        except Exception as e:
            print(f"❌ City selection failed: {e}")
            return False
    
    def _capture_page_feedback(self, driver) -> str:
        """捕获页面反馈信息"""
        try:
            # 等待页面稳定
            time.sleep(1)
            
            # 查找常见的反馈元素
            feedback_selectors = [
                "//h1 | //h2 | //h3",
                "//div[contains(@class, 'message')]",
                "//div[contains(@class, 'feedback')]",
                "//div[contains(@class, 'result')]",
                "//div[contains(@class, 'success')]",
                "//div[contains(@class, 'error')]",
                "//div[contains(@class, 'fail')]",
                "//p[contains(text(), '失败') or contains(text(), '成功') or contains(text(), '已存在')]"
            ]
            
            feedback_texts = []
            for selector in feedback_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.text.strip():
                            text = element.text.strip()
                            if text and text not in feedback_texts:
                                feedback_texts.append(text)
                except:
                    continue
            
            if feedback_texts:
                # 优先返回包含关键词的反馈
                for text in feedback_texts:
                    if any(keyword in text for keyword in ['失败', '成功', '已存在', '保护期', '重复推荐']):
                        return text
                return feedback_texts[0]
            
            # 备用方案：获取页面标题或body文本
            try:
                title = driver.title
                if title and title != "深圳元戎启行科技有限公司 - 内部推荐":
                    return f"Page title: {title}"
            except:
                pass
            
            try:
                body_text = driver.find_element(By.TAG_NAME, "body").text.strip()
                if body_text:
                    return body_text[:200] + "..." if len(body_text) > 200 else body_text
            except:
                pass
            
            return "No feedback captured"
            
        except Exception as e:
            return f"Error capturing feedback: {str(e)}"
    
    def _submit_single_application(self, resume_path: str, candidate_name: str, 
                                 job_title: str, recommendation: str, city: str) -> Tuple[bool, str]:
        """提交单个申请，返回(success, feedback)"""
        
        print(f"\n🔄 Starting application submission:")
        print(f"  👤 Candidate: {candidate_name}")
        print(f"  🎯 Job: {job_title}")
        print(f"  🏙️ City: {city}")
        print(f"  💬 Recommendation: {recommendation[:100]}...")
        
        # 获取职位URL
        job_url = self.job_urls.get(job_title)
        if not job_url:
            print(f"❌ Job URL not found for: {job_title}")
            return False, f"Job URL not found for: {job_title}"
        
        try:
            # 连接Chrome
            driver, wait = self._connect_to_chrome()
            if not driver:
                return False, "Chrome connection failed"
            
            # 导航到职位页面
            print(f"🌐 Navigating to: {job_url}")
            driver.get(job_url)
            time.sleep(0.5)
            print(f"✅ Page loaded: {driver.title}")
            
            # 上传简历
            print("📤 Uploading resume...")
            if not upload_resume(driver, wait, resume_path):
                print("❌ Resume upload failed")
                return False, "Resume upload failed"
            
            # 选择城市
            if not self._select_city_smart(driver, wait, city, job_title):
                print("❌ City selection failed")
                return False, "City selection failed"
            
            # 填写推荐语
            print("💬 Filling recommendation text...")
            if not fill_recommendation(driver, wait, recommendation):
                print("❌ Recommendation filling failed")
                return False, "Recommendation filling failed"
            
            # 提交申请（带重试机制）
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    print(f"📨 Submitting application (attempt {attempt + 1}/{max_retries})...")
                    
                    if submit_application(driver, wait):
                        # 捕获页面反馈
                        feedback = self._capture_page_feedback(driver)
                        print(f"📢 Page feedback: {feedback}")
                        print("✅ Application submitted successfully!")
                        return True, feedback
                    else:
                        if attempt < max_retries - 1:
                            print(f"  ⚠️ Submission attempt {attempt + 1} failed, retrying in 2 seconds...")
                            time.sleep(2)
                        else:
                            print("❌ All submission attempts failed")
                            return False, "All submission attempts failed"
                            
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"  ⚠️ Submission attempt {attempt + 1} error: {e}, retrying in 2 seconds...")
                        time.sleep(2)
                    else:
                        print(f"❌ All submission attempts failed with error: {e}")
                        return False, f"Submission failed: {str(e)}"
            
            return False, "Unexpected submission failure"
            
        except Exception as e:
            error_msg = f"Submission error: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return False, error_msg
    
    def process_with_json_config(self, resume_folder: str, json_config_path: str):
        """基于JSON配置处理简历提交"""
        
        print(f"\n🚀 STARTING JSON-BASED RESUME SUBMISSION")
        print("=" * 80)
        
        # 加载JSON配置
        try:
            with open(json_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            if isinstance(config, list):
                merged = {}
                for item in config:
                    merged.update(item)
                config = merged
            print(f"✅ Loaded JSON config with {len(config)} candidates")
        except Exception as e:
            print(f"❌ Failed to load JSON config: {e}")
            return
        
        # 处理每个候选人
        total_applications = 0
        successful_applications = 0
        
        for candidate_name, candidate_config in config.items():
            print(f"\n{'='*20} PROCESSING CANDIDATE: {candidate_name} {'='*20}")
            
            # 查找对应的简历文件
            resume_file = None
            for file in os.listdir(resume_folder):
                if candidate_name in file and file.endswith('.pdf'):
                    resume_file = file
                    break
            
            if not resume_file:
                print(f"❌ Resume file not found for {candidate_name}")
                
                # 记录找不到简历文件的情况
                city = candidate_config.get("城市", "深圳")
                jobs = [
                    {
                        "title": candidate_config.get("第一匹配职位"),
                        "recommendation": candidate_config.get("第一匹配评价")
                    },
                    {
                        "title": candidate_config.get("第二匹配职位"),
                        "recommendation": candidate_config.get("第二匹配评价")
                    }
                ]
                
                # 为每个配置的职位记录"简历文件未找到"的结果
                for i, job in enumerate(jobs, 1):
                    if job["title"] and job["recommendation"]:
                        result = {
                            'candidate_name': candidate_name,
                            'job_title': job["title"],
                            'recommendation': job["recommendation"],
                            'city': city,
                            'success': False,
                            'feedback': f"Resume file not found for {candidate_name}",
                            'timestamp': str(datetime.now())
                        }
                        self.results.append(result)
                        total_applications += 1
                
                continue
            
            resume_path = os.path.join(resume_folder, resume_file)
            print(f"📄 Found resume: {resume_file}")
            
            # 提取配置信息
            city = candidate_config.get("城市", "深圳")
            
            # 处理两个职位
            jobs = [
                {
                    "title": candidate_config.get("第一匹配职位"),
                    "recommendation": candidate_config.get("第一匹配评价")
                },
                {
                    "title": candidate_config.get("第二匹配职位"),
                    "recommendation": candidate_config.get("第二匹配评价")
                }
            ]
            
            # 标志跟踪第一个职位是否失败
            first_job_failed = False
            
            for i, job in enumerate(jobs, 1):
                if not job["title"] or not job["recommendation"]:
                    print(f"⚠️ Missing job {i} configuration for {candidate_name}")
                    continue
                
                # 如果是第二个职位且第一个职位失败了，跳过
                if i == 2 and first_job_failed:
                    print(f"⏭️ Skipping job 2 for {candidate_name} because job 1 failed")
                    continue
                
                print(f"\n📝 SUBMITTING APPLICATION {i}/2")
                total_applications += 1
                
                success, feedback = self._submit_single_application(
                    resume_path, candidate_name, job["title"], 
                    job["recommendation"], city
                )
                
                # 检查第一个职位是否因为候选人已存在或投递限制而失败
                # 即使submit_application返回True，也要检查feedback内容
                if i == 1:
                    failure_keywords = ["已存在", "失败", "投递限制", "达到投递限制", "每人一共可以申请投递"]
                    if any(keyword in feedback for keyword in failure_keywords):
                        print(f"🚫 First job failed for {candidate_name}: {feedback}")
                        print(f"⏭️ Will skip second job for this candidate")
                        first_job_failed = True
                        # 更新success状态以反映真实结果
                        success = False
                
                # 记录结果
                result = {
                    'candidate_name': candidate_name,
                    'job_title': job["title"],
                    'recommendation': job["recommendation"],
                    'city': city,
                    'success': success,
                    'feedback': feedback,
                    'timestamp': str(datetime.now())
                }
                self.results.append(result)
                
                if success:
                    successful_applications += 1
                    print(f"✅ Application {i} submitted successfully!")
                else:
                    print(f"❌ Application {i} submission failed")
                
                # 短暂延迟
                time.sleep(2)
        
        # 打印最终统计
        self._print_final_results(total_applications, successful_applications)
    
    def _print_final_results(self, total: int, successful: int):
        """打印最终结果"""
        print(f"\n{'='*20} JSON-BASED SUBMISSION COMPLETED {'='*20}")
        
        print(f"📊 FINAL STATISTICS:")
        print(f"  Total applications: {total}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {total - successful}")
        print(f"  Success rate: {successful/total*100:.1f}%" if total > 0 else "  Success rate: 0%")
        
        print(f"\n📋 DETAILED RESULTS:")
        for i, result in enumerate(self.results, 1):
            status = "✅" if result['success'] else "❌"
            feedback = result.get('feedback', 'No feedback')
            print(f"  {i}. {status} {result['candidate_name']} -> {result['job_title']}")
            if not result['success']:
                print(f"      💬 Feedback: {feedback}")


def main():
    """主函数"""
    if len(sys.argv) != 3:
        print("Usage: python3 submit_with_json_config.py <resume_folder> <json_config_file>")
        print("Example: python3 submit_with_json_config.py /home/chenbohan/Downloads/jianli config.json")
        return
    
    resume_folder = sys.argv[1]
    json_config_path = sys.argv[2]
    
    # 检查路径
    if not os.path.exists(resume_folder):
        print(f"❌ Resume folder not found: {resume_folder}")
        return
    
    if not os.path.exists(json_config_path):
        print(f"❌ JSON config file not found: {json_config_path}")
        return
    
    # 职位描述文件路径
    job_descriptions_file = "/home/chenbohan/Downloads/jianli/职位描述.txt"
    
    print(f"📁 Resume folder: {resume_folder}")
    print(f"📋 JSON config: {json_config_path}")
    print(f"🔗 Job descriptions: {job_descriptions_file}")
    
    # 创建提交器并执行
    submitter = JSONBasedSubmitter(job_descriptions_file)
    submitter.process_with_json_config(resume_folder, json_config_path)


if __name__ == "__main__":
    main()