#!/usr/bin/env python3
"""
基于JSON配置文件进行简历提交（增强版）
增加了重试机制、反馈处理、跳过逻辑等功能
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
from final_working_automation import upload_resume, select_city_robust, fill_recommendation

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException


class EnhancedJSONSubmitter:
    """增强版基于JSON配置的简历提交器"""
    
    def __init__(self, job_descriptions_file: str, dry_run: bool = False):
        self.job_urls = self._load_job_urls(job_descriptions_file)
        self.results = []
        self.dry_run = dry_run
        self.driver = None
        self.wait = None
        self.candidate_skip_status = {}  # 记录候选人跳过状态
        
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
        """连接到Chrome浏览器"""
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
    
    def _submit_application_with_retry(self) -> Tuple[bool, str]:
        """提交申请（带重试机制和反馈捕获）"""
        if self.dry_run:
            print("🧪 DRY RUN: Simulating successful submission")
            return True, "DRY RUN: Simulated success"
        
        max_retries = 5
        
        for attempt in range(max_retries):
            try:
                print(f"📨 Submitting application (attempt {attempt + 1}/{max_retries})...")
                
                # 查找并点击"预览并提交"按钮
                preview_button = None
                preview_selectors = [
                    "//button[contains(text(), '预览并提交')]",
                    "//button[contains(text(), '提交')]",
                    "//input[@type='submit']",
                    "//*[contains(@class, 'submit') and contains(text(), '提交')]"
                ]
                
                for selector in preview_selectors:
                    try:
                        preview_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                        break
                    except TimeoutException:
                        continue
                
                if not preview_button:
                    if attempt < max_retries - 1:
                        print(f"  ⚠️ Preview button not found, retrying in 2 seconds...")
                        time.sleep(2)
                        continue
                    else:
                        return False, "Preview button not found after all retries"
                
                # 点击预览并提交
                preview_button.click()
                print("  ✅ Clicked '预览并提交'")
                time.sleep(1)
                
                # 查找并点击确认提交按钮
                confirm_button = None
                confirm_selectors = [
                    "//button[contains(text(), '确认提交')]",
                    "//button[contains(text(), '确认')]",
                    "//button[contains(text(), '提交')]"
                ]
                
                for selector in confirm_selectors:
                    try:
                        confirm_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                        break
                    except TimeoutException:
                        continue
                
                if not confirm_button:
                    if attempt < max_retries - 1:
                        print(f"  ⚠️ Confirm button not found, retrying in 2 seconds...")
                        time.sleep(2)
                        continue
                    else:
                        return False, "Confirm button not found after all retries"
                
                # 点击确认提交
                confirm_button.click()
                print("  ✅ Clicked '确认提交'")
                
                # 等待页面跳转并捕获反馈（200ms延迟）
                time.sleep(0.2)  # 等待200ms
                feedback = self._capture_page_feedback()
                
                print(f"  📢 Page feedback: {feedback}")
                
                # 检查反馈是否表示失败
                if any(keyword in feedback for keyword in ['失败', '已存在', '保护期', '重复推荐', '不能重复']):
                    print(f"  ⚠️ Detected failure in feedback: {feedback}")
                    return False, feedback  # 返回失败状态但包含反馈信息
                
                return True, feedback
                
            except Exception as e:
                error_msg = f"Submission attempt {attempt + 1} failed: {str(e)}"
                print(f"  ❌ {error_msg}")
                
                if attempt < max_retries - 1:
                    print(f"  ⏳ Waiting 2 seconds before retry...")
                    time.sleep(2)
                else:
                    return False, f"All {max_retries} submission attempts failed. Last error: {str(e)}"
        
        return False, "Unexpected error in submission retry loop"
    
    def _capture_page_feedback(self) -> str:
        """捕获页面反馈信息"""
        if self.dry_run:
            return "DRY RUN: Simulated feedback"
            
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
                    elements = self.driver.find_elements(By.XPATH, selector)
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
                title = self.driver.title
                if title and title != "深圳元戎启行科技有限公司 - 内部推荐":
                    return f"Page title: {title}"
            except:
                pass
            
            try:
                body_text = self.driver.find_element(By.TAG_NAME, "body").text.strip()
                if body_text:
                    return body_text[:200] + "..." if len(body_text) > 200 else body_text
            except:
                pass
            
            return "No feedback captured"
            
        except Exception as e:
            return f"Error capturing feedback: {str(e)}"
    
    def _should_skip_candidate(self, candidate_name: str, feedback: str) -> bool:
        """判断是否应该跳过候选人的后续职位"""
        skip_keywords = [
            "已存在",
            "保护期",
            "重复推荐",
            "不能重复",
            "已推荐"
        ]
        
        should_skip = any(keyword in feedback for keyword in skip_keywords)
        
        if should_skip:
            self.candidate_skip_status[candidate_name] = {
                'skipped': True,
                'reason': feedback,
                'timestamp': str(datetime.now())
            }
            print(f"🚫 Candidate {candidate_name} will be skipped for remaining positions due to: {feedback}")
        
        return should_skip
    
    def _submit_single_application(self, resume_path: str, candidate_name: str, 
                                 job_title: str, recommendation: str, city: str, 
                                 is_second_job: bool = False) -> Dict:
        """提交单个申请"""
        
        result = {
            'candidate_name': candidate_name,
            'job_title': job_title,
            'recommendation': recommendation[:100] + "..." if len(recommendation) > 100 else recommendation,
            'city': city,
            'success': False,
            'error': None,
            'feedback': None,
            'skipped': False,
            'skip_reason': None,
            'timestamp': str(datetime.now())
        }
        
        print(f"\n🔄 Starting application submission:")
        print(f"  👤 Candidate: {candidate_name}")
        print(f"  🎯 Job: {job_title}")
        print(f"  🏙️ City: {city}")
        print(f"  💬 Recommendation: {recommendation[:100]}...")
        
        # 检查是否应该跳过
        if is_second_job and candidate_name in self.candidate_skip_status:
            skip_info = self.candidate_skip_status[candidate_name]
            result['skipped'] = True
            result['skip_reason'] = skip_info['reason']
            print(f"🚫 Skipping {candidate_name}'s second job due to: {skip_info['reason']}")
            return result
        
        if self.dry_run:
            print("🧪 DRY RUN: Simulating successful submission")
            result['success'] = True
            result['feedback'] = "DRY RUN: Simulated success"
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
            
            # 选择城市（使用原始的select_city_robust函数）
            if "强化学习算法工程师" not in job_title:  # 强化学习算法工程师不需要选择城市
                print(f"🏙️ Selecting city: {city}")
                if not select_city_robust(self.driver, self.wait, city):
                    result['error'] = "City selection failed"
                    return result
                print("✅ City selection completed")
            else:
                print("ℹ️ This job doesn't require city selection, skipping...")
            
            # 填写推荐语
            print("💬 Filling recommendation text...")
            if not fill_recommendation(self.driver, self.wait, recommendation):
                result['error'] = "Recommendation filling failed"
                return result
            print("✅ Recommendation filled successfully")
            
            # 提交申请（带重试机制）
            success, feedback = self._submit_application_with_retry()
            result['success'] = success
            result['feedback'] = feedback
            
            # 检查是否需要跳过后续职位（无论成功还是失败都要检查反馈）
            if not is_second_job:  # 只在第一个职位时检查
                print(f"🔍 Checking if should skip candidate based on feedback: {feedback}")
                if self._should_skip_candidate(candidate_name, feedback):
                    print(f"🚫 Will skip {candidate_name}'s second job due to feedback: {feedback}")
            
            if success:
                print("✅ Application submitted successfully!")
            else:
                print(f"❌ Application submission failed: {feedback}")
                result['error'] = feedback
            
            return result
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"❌ {error_msg}")
            result['error'] = error_msg
            import traceback
            traceback.print_exc()
            return result
    
    def process_with_json_config(self, resume_folder: str, json_config_path: str):
        """基于JSON配置处理简历提交"""
        
        print(f"\n🚀 STARTING ENHANCED JSON-BASED RESUME SUBMISSION")
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
        skipped_applications = 0
        
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
                            'feedback': None,
                            'skipped': False,
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
                    job["recommendation"], city, is_second_job=(job_idx == 2)
                )
                
                self.results.append(result)
                completed_applications += 1
                
                if result['success']:
                    successful_applications += 1
                    print(f"✅ Application {job_idx} submitted successfully!")
                elif result['skipped']:
                    skipped_applications += 1
                    print(f"🚫 Application {job_idx} skipped: {result.get('skip_reason', 'Unknown reason')}")
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
        self._print_final_results(total_applications, successful_applications, skipped_applications)
        
        # 关闭浏览器连接
        if self.driver and not self.dry_run:
            try:
                self.driver.quit()
                print("🔒 Browser connection closed")
            except:
                pass
    
    def _print_final_results(self, total: int, successful: int, skipped: int):
        """打印最终结果"""
        print(f"\n{'='*20} ENHANCED SUBMISSION COMPLETED {'='*20}")
        
        failed = total - successful - skipped
        
        print(f"📊 FINAL STATISTICS:")
        print(f"  Total applications: {total}")
        print(f"  Successful: {successful}")
        print(f"  Skipped: {skipped}")
        print(f"  Failed: {failed}")
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
            skip_count = sum(1 for r in results if r.get('skipped', False))
            print(f"  👤 {name}: {success_count} successful, {skip_count} skipped, {len(results)-success_count-skip_count} failed")
            
            for result in results:
                if result['success']:
                    status = "✅"
                    info = f" - {result.get('feedback', 'No feedback')}"
                elif result.get('skipped', False):
                    status = "🚫"
                    info = f" - SKIPPED: {result.get('skip_reason', 'Unknown reason')}"
                else:
                    status = "❌"
                    # 优先显示feedback，如果没有则显示error
                    error_info = result.get('feedback') or result.get('error', 'Unknown error')
                    info = f" - {error_info}"
                
                print(f"    {status} {result['job_title']}{info}")
        
        # 显示跳过候选人的汇总
        if self.candidate_skip_status:
            print(f"\n🚫 SKIPPED CANDIDATES SUMMARY:")
            for name, skip_info in self.candidate_skip_status.items():
                print(f"  👤 {name}: {skip_info['reason']}")
        
        # 保存详细结果到文件
        results_file = f"/home/chenbohan/boss/mokahr-automation-skill/enhanced_submission_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            detailed_results = {
                'summary': {
                    'total_applications': total,
                    'successful': successful,
                    'skipped': skipped,
                    'failed': failed,
                    'success_rate': f"{successful/total*100:.1f}%" if total > 0 else "0%"
                },
                'candidate_skip_status': self.candidate_skip_status,
                'detailed_results': self.results
            }
            
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(detailed_results, f, ensure_ascii=False, indent=2)
            print(f"\n💾 Detailed results saved to: {results_file}")
        except Exception as e:
            print(f"⚠️ Failed to save results file: {e}")


def main():
    """主函数"""
    if len(sys.argv) < 3:
        print("Usage: python3 submit_with_json_config_enhanced.py <resume_folder> <json_config_file> [--dry-run]")
        print("Example: python3 submit_with_json_config_enhanced.py /home/chenbohan/Downloads/jianli config.json")
        print("         python3 submit_with_json_config_enhanced.py /home/chenbohan/Downloads/jianli config.json --dry-run")
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
    submitter = EnhancedJSONSubmitter(job_descriptions_file, dry_run=dry_run)
    submitter.process_with_json_config(resume_folder, json_config_path)


if __name__ == "__main__":
    main()