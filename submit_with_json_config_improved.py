#!/usr/bin/env python3
"""
改进版基于JSON配置文件进行简历提交
增加了更好的错误处理、进度跟踪、城市选择优化等功能
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import automation functions
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core'))
from final_working_automation import upload_resume, fill_recommendation, submit_application

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException


class ImprovedJSONSubmitter:
    """改进版基于JSON配置的简历提交器"""
    
    def __init__(self, job_descriptions_file: str, dry_run: bool = False):
        self.job_urls = self._load_job_urls(job_descriptions_file)
        self.results = []
        self.dry_run = dry_run
        self.driver = None
        self.wait = None
        
        if dry_run:
            print("🧪 DRY RUN MODE: No actual submissions will be made")
    
    def _load_job_urls(self, file_path: str) -> Dict[str, str]:
        """加载职位URL映射"""
        job_urls = {}
        
        print(f"🔍 Loading job URLs from: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Failed to read job descriptions file: {e}")
            return {}
        
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
        return job_urls
    
    def _connect_to_chrome(self) -> bool:
        """连接到Chrome浏览器（改进版）"""
        if self.dry_run:
            print("🧪 DRY RUN: Skipping Chrome connection")
            return True
            
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"🔄 Attempting to connect to Chrome (attempt {attempt + 1}/{max_retries})")
                
                chrome_options = Options()
                chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
                chromedriver_path = os.path.expanduser("~/.local/bin/chromedriver-linux64/chromedriver")
                service = Service(chromedriver_path)
                
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.wait = WebDriverWait(self.driver, 15)
                
                print("✅ Connected to Chrome browser")
                return True
                
            except WebDriverException as e:
                print(f"⚠️ Chrome connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    print("⏳ Waiting 3 seconds before retry...")
                    time.sleep(3)
                else:
                    print("❌ All Chrome connection attempts failed")
                    print("💡 Please ensure Chrome is running with: google-chrome --remote-debugging-port=9222")
                    return False
        
        return False
    
    def _open_new_tab_and_navigate(self, url: str) -> bool:
        """打开新标签页并导航到URL"""
        if self.dry_run:
            print(f"🧪 DRY RUN: Would navigate to {url}")
            return True
            
        try:
            # 使用CDP打开新标签页
            self.driver.switch_to.new_window('tab')
            print("✅ Opened new tab")
            
            # 导航到URL
            print(f"🌐 Navigating to: {url}")
            self.driver.get(url)
            time.sleep(1)  # 等待页面加载
            
            print(f"✅ Page loaded: {self.driver.title}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to open new tab or navigate: {e}")
            return False
    
    def _select_city_improved(self, city_name: str, job_title: str) -> bool:
        """改进的城市选择"""
        if self.dry_run:
            print(f"🧪 DRY RUN: Would select city {city_name} for {job_title}")
            return True
            
        print(f"🏙️ Checking city selection for: {job_title}")
        
        # 强化学习算法工程师不需要选择城市
        if "强化学习算法工程师" in job_title:
            print("ℹ️ This job doesn't require city selection, skipping...")
            return True
        
        print(f"🏙️ Selecting city: {city_name}")
        
        try:
            # 等待城市输入框出现
            city_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='选择意向工作城市']"))
            )
            print("  Found city input field")
            
            # 点击输入框打开下拉菜单
            city_input.click()
            time.sleep(0.5)
            
            # 根据城市名称选择对应选项
            city_map = {
                "上海": "上海市",
                "深圳": "深圳市"
            }
            target_city = city_map.get(city_name, city_name + "市")
            
            # 尝试多种选择器
            selectors = [
                f"//div[contains(@class, 'ant-select-item') and contains(text(), '{target_city}')]",
                f"//li[contains(@class, 'ant-select-item') and contains(text(), '{target_city}')]",
                f"//*[contains(text(), '{target_city}') and contains(@class, 'ant-select-item')]"
            ]
            
            option_clicked = False
            for selector in selectors:
                try:
                    option = self.wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    option.click()
                    print(f"  ✅ Successfully selected: {target_city}")
                    option_clicked = True
                    break
                except TimeoutException:
                    continue
            
            if not option_clicked:
                print(f"  ⚠️ Could not find city option for {target_city}, trying fallback...")
                # 备用方案：选择第一个可用选项
                try:
                    first_option = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".ant-select-item"))
                    )
                    first_option.click()
                    print(f"  ⚠️ Selected fallback option: {first_option.text}")
                except:
                    print("  ❌ City selection completely failed")
                    return False
            
            time.sleep(0.5)
            return True
            
        except Exception as e:
            print(f"  ❌ City selection error: {e}")
            return False
    
    def _submit_single_application(self, resume_path: str, candidate_name: str, 
                                 job_title: str, recommendation: str, city: str) -> Dict:
        """提交单个申请（改进版）"""
        
        result = {
            'candidate_name': candidate_name,
            'job_title': job_title,
            'recommendation': recommendation[:100] + "..." if len(recommendation) > 100 else recommendation,
            'city': city,
            'success': False,
            'error': None,
            'timestamp': str(datetime.now())
        }
        
        print(f"\n🔄 Starting application submission:")
        print(f"  👤 Candidate: {candidate_name}")
        print(f"  🎯 Job: {job_title}")
        print(f"  🏙️ City: {city}")
        print(f"  💬 Recommendation: {recommendation[:100]}...")
        
        if self.dry_run:
            print("🧪 DRY RUN: Simulating successful submission")
            result['success'] = True
            return result
        
        # 获取职位URL
        job_url = self.job_urls.get(job_title)
        if not job_url:
            error_msg = f"Job URL not found for: {job_title}"
            print(f"❌ {error_msg}")
            result['error'] = error_msg
            return result
        
        try:
            # 打开新标签页并导航
            if not self._open_new_tab_and_navigate(job_url):
                result['error'] = "Failed to navigate to job page"
                return result
            
            # 上传简历
            print("📤 Uploading resume...")
            if not upload_resume(self.driver, self.wait, resume_path):
                result['error'] = "Resume upload failed"
                return result
            print("✅ Resume uploaded successfully")
            
            # 选择城市
            if not self._select_city_improved(city, job_title):
                result['error'] = "City selection failed"
                return result
            print("✅ City selection completed")
            
            # 填写推荐语
            print("💬 Filling recommendation text...")
            if not fill_recommendation(self.driver, self.wait, recommendation):
                result['error'] = "Recommendation filling failed"
                return result
            print("✅ Recommendation filled successfully")
            
            # 提交申请
            print("📨 Submitting application...")
            if not submit_application(self.driver, self.wait):
                result['error'] = "Application submission failed"
                return result
            print("✅ Application submitted successfully!")
            
            result['success'] = True
            return result
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"❌ {error_msg}")
            result['error'] = error_msg
            import traceback
            traceback.print_exc()
            return result
    
    def process_with_json_config(self, resume_folder: str, json_config_path: str):
        """基于JSON配置处理简历提交（改进版）"""
        
        print(f"\n🚀 STARTING IMPROVED JSON-BASED RESUME SUBMISSION")
        print("=" * 80)
        
        # 加载JSON配置
        try:
            with open(json_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"✅ Loaded JSON config with {len(config)} candidates")
        except Exception as e:
            print(f"❌ Failed to load JSON config: {e}")
            return
        
        # 连接Chrome（如果不是干运行模式）
        if not self._connect_to_chrome():
            print("❌ Cannot proceed without Chrome connection")
            return
        
        # 统计信息
        total_candidates = len(config)
        total_applications = total_candidates * 2  # 每人2个职位
        completed_applications = 0
        successful_applications = 0
        
        print(f"📊 Processing plan: {total_candidates} candidates, {total_applications} applications total")
        
        # 处理每个候选人
        for candidate_idx, (candidate_name, candidate_config) in enumerate(config.items(), 1):
            print(f"\n{'='*15} CANDIDATE {candidate_idx}/{total_candidates}: {candidate_name} {'='*15}")
            
            # 查找对应的简历文件
            resume_file = None
            for file in os.listdir(resume_folder):
                if candidate_name in file and file.endswith('.pdf'):
                    resume_file = file
                    break
            
            if not resume_file:
                print(f"❌ Resume file not found for {candidate_name}")
                # 记录失败结果
                for job_num in [1, 2]:
                    job_key = f"第{['一', '二'][job_num-1]}匹配职位"
                    if candidate_config.get(job_key):
                        self.results.append({
                            'candidate_name': candidate_name,
                            'job_title': candidate_config.get(job_key),
                            'success': False,
                            'error': 'Resume file not found',
                            'timestamp': str(datetime.now())
                        })
                        completed_applications += 1
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
            
            for job_idx, job in enumerate(jobs, 1):
                if not job["title"] or not job["recommendation"]:
                    print(f"⚠️ Missing job {job_idx} configuration for {candidate_name}")
                    completed_applications += 1
                    continue
                
                print(f"\n📝 APPLICATION {job_idx}/2 (Overall: {completed_applications + 1}/{total_applications})")
                
                result = self._submit_single_application(
                    resume_path, candidate_name, job["title"], 
                    job["recommendation"], city
                )
                
                self.results.append(result)
                completed_applications += 1
                
                if result['success']:
                    successful_applications += 1
                    print(f"✅ Application {job_idx} submitted successfully!")
                else:
                    print(f"❌ Application {job_idx} failed: {result.get('error', 'Unknown error')}")
                
                # 进度更新
                progress = (completed_applications / total_applications) * 100
                print(f"📊 Progress: {completed_applications}/{total_applications} ({progress:.1f}%)")
                
                # 短暂延迟避免过快提交
                if not self.dry_run and completed_applications < total_applications:
                    print("⏳ Waiting 2 seconds before next submission...")
                    time.sleep(2)
        
        # 打印最终统计
        self._print_final_results(total_applications, successful_applications)
        
        # 关闭浏览器连接
        if self.driver and not self.dry_run:
            try:
                self.driver.quit()
                print("🔒 Browser connection closed")
            except:
                pass
    
    def _print_final_results(self, total: int, successful: int):
        """打印最终结果（改进版）"""
        print(f"\n{'='*20} IMPROVED SUBMISSION COMPLETED {'='*20}")
        
        print(f"📊 FINAL STATISTICS:")
        print(f"  Total applications: {total}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {total - successful}")
        print(f"  Success rate: {successful/total*100:.1f}%" if total > 0 else "  Success rate: 0%")
        
        # 按候选人分组显示结果
        candidates = {}
        for result in self.results:
            name = result['candidate_name']
            if name not in candidates:
                candidates[name] = []
            candidates[name].append(result)
        
        print(f"\n📋 RESULTS BY CANDIDATE:")
        for name, results in candidates.items():
            success_count = sum(1 for r in results if r['success'])
            print(f"  👤 {name}: {success_count}/{len(results)} successful")
            for result in results:
                status = "✅" if result['success'] else "❌"
                error_info = f" ({result.get('error', 'Unknown error')})" if not result['success'] else ""
                print(f"    {status} {result['job_title']}{error_info}")
        
        # 保存详细结果到文件
        results_file = f"/home/chenbohan/boss/mokahr-automation-skill/submission_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            print(f"\n💾 Detailed results saved to: {results_file}")
        except Exception as e:
            print(f"⚠️ Failed to save results file: {e}")


def main():
    """主函数"""
    if len(sys.argv) < 3:
        print("Usage: python3 submit_with_json_config_improved.py <resume_folder> <json_config_file> [--dry-run]")
        print("Example: python3 submit_with_json_config_improved.py /home/chenbohan/Downloads/jianli config.json")
        print("         python3 submit_with_json_config_improved.py /home/chenbohan/Downloads/jianli config.json --dry-run")
        return
    
    resume_folder = sys.argv[1]
    json_config_path = sys.argv[2]
    dry_run = "--dry-run" in sys.argv
    
    # 检查路径
    if not os.path.exists(resume_folder):
        print(f"❌ Resume folder not found: {resume_folder}")
        return
    
    if not os.path.exists(json_config_path):
        print(f"❌ JSON config file not found: {json_config_path}")
        return
    
    # 职位描述文件路径
    job_descriptions_file = "/home/chenbohan/Downloads/职位描述.txt"
    
    print(f"📁 Resume folder: {resume_folder}")
    print(f"📋 JSON config: {json_config_path}")
    print(f"🔗 Job descriptions: {job_descriptions_file}")
    if dry_run:
        print("🧪 DRY RUN MODE: No actual submissions will be made")
    
    # 创建提交器并执行
    submitter = ImprovedJSONSubmitter(job_descriptions_file, dry_run=dry_run)
    submitter.process_with_json_config(resume_folder, json_config_path)


if __name__ == "__main__":
    main()