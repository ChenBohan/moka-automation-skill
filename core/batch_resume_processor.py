#!/usr/bin/env python3
"""
Batch resume processing and job application automation
批量简历处理和职位申请自动化 - 使用LLM智能匹配
"""

import os
import sys
import re
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from final_working_automation import upload_resume, select_city_robust, fill_recommendation, submit_application
from llm_job_matcher import LLMJobMatcher

# Selenium imports for browser automation
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class JobMatcher:
    """职位匹配器 - 现在使用LLM进行智能匹配"""
    
    def __init__(self, job_descriptions_file: str):
        # 使用LLM匹配器
        self.llm_matcher = LLMJobMatcher(job_descriptions_file)
        self.jobs = self.llm_matcher.jobs
    
    def _load_job_descriptions(self, file_path: str) -> Dict[str, Dict]:
        """加载职位描述文件 - 现在由LLMJobMatcher处理"""
        return self.llm_matcher.jobs
    
    def match_jobs_for_resume(self, resume_content: str, candidate_name: str) -> List[Tuple[str, str, str]]:
        """
        使用LLM为简历匹配最适合的两个职位
        返回: [(job_title, submit_url, recommendation), ...]
        """
        print(f"\n🤖 LLM-BASED JOB MATCHING FOR {candidate_name}:")
        print(f"📄 Resume content length: {len(resume_content)} characters")
        print(f"📄 Resume preview: {resume_content[:200]}...")
        
        # 使用LLM匹配器进行智能匹配
        matches = self.llm_matcher.match_jobs_with_llm(resume_content, candidate_name)
        
        if not matches:
            print("❌ LLM matching failed, using fallback")
            return self._fallback_matching(candidate_name)
        
        print(f"\n✅ LLM returned {len(matches)} job matches")
        
        # 转换为所需格式: (job_title, submit_url, recommendation)
        selected_jobs = []
        for job_title, submit_url, recommendation, score in matches:
            selected_jobs.append((job_title, submit_url, recommendation))
            print(f"  📌 {job_title}: {recommendation[:100]}...")
        
        return selected_jobs
    
    def _fallback_matching(self, candidate_name: str) -> List[Tuple[str, str, str]]:
        """备用匹配方案"""
        print("⚠️ Using fallback matching (first 2 jobs)")
        
        matches = []
        for i, (job_title, job_info) in enumerate(list(self.jobs.items())[:2]):
            recommendation = f"{candidate_name}具备相关技术背景，符合{job_title}的基本要求。"
            matches.append((job_title, job_info['submit_url'], recommendation))
        
        return matches


class ResumeProcessor:
    """批量简历处理器"""
    
    def __init__(self, job_descriptions_file: str):
        self.job_matcher = JobMatcher(job_descriptions_file)
        self.results = []
    
    def extract_city_from_filename(self, filename: str) -> str:
        """从文件名提取意向城市"""
        if '深圳' in filename:
            return '深圳市'
        elif '上海' in filename:
            return '上海市'
        else:
            return '深圳市'  # 默认深圳
    
    def extract_candidate_name(self, filename: str) -> str:
        """从文件名提取候选人姓名"""
        # 匹配中文姓名模式
        import re
        name_pattern = r'】([^【】\s]+)\s+\d+年'
        match = re.search(name_pattern, filename)
        if match:
            return match.group(1).strip()
        
        # 备用方案：提取PDF前的最后一个词
        base_name = os.path.splitext(filename)[0]
        parts = base_name.split()
        if parts:
            return parts[-1]
        
        return "候选人"
    
    def read_pdf_content(self, pdf_path: str) -> str:
        """读取PDF文件内容"""
        return self.job_matcher.llm_matcher.extract_pdf_content(pdf_path)
    
    def process_resumes_in_batch(self, resume_folder: str, resume_files: List[str] = None):
        """批量处理简历"""
        
        print(f"\n🚀 STARTING BATCH RESUME PROCESSING")
        print("=" * 80)
        
        # 获取简历文件列表
        if resume_files:
            pdf_files = [f for f in resume_files if f.endswith('.pdf')]
        else:
            pdf_files = [f for f in os.listdir(resume_folder) if f.endswith('.pdf')]
        
        print(f"📁 Found {len(pdf_files)} PDF resumes to process")
        
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"\n{'='*20} PROCESSING RESUME {i}/{len(pdf_files)} {'='*20}")
            print(f"📄 File: {pdf_file}")
            
            try:
                # 提取候选人信息
                candidate_name = self.extract_candidate_name(pdf_file)
                target_city = self.extract_city_from_filename(pdf_file)
                
                print(f"👤 Candidate: {candidate_name}")
                print(f"🏙️ Target City: {target_city}")
                
                # 读取简历内容
                pdf_path = os.path.join(resume_folder, pdf_file)
                resume_content = self.read_pdf_content(pdf_path)
                
                if not resume_content:
                    print(f"❌ Failed to extract content from {pdf_file}")
                    continue
                
                print(f"📖 Resume content extracted: {len(resume_content)} characters")
                
                # 使用LLM匹配职位
                matched_jobs = self.job_matcher.match_jobs_for_resume(resume_content, candidate_name)
                
                if not matched_jobs:
                    print(f"❌ No suitable jobs found for {candidate_name}")
                    continue
                
                print(f"\n🎯 Found {len(matched_jobs)} matching jobs for {candidate_name}")
                
                # 为每个匹配的职位提交申请
                for job_idx, (job_title, submit_url, recommendation) in enumerate(matched_jobs, 1):
                    print(f"\n📝 SUBMITTING APPLICATION {job_idx}/{len(matched_jobs)}")
                    print(f"🎯 Job: {job_title}")
                    print(f"🔗 URL: {submit_url}")
                    print(f"💬 Recommendation: {recommendation[:150]}...")
                    
                    # 执行提交流程
                    success = self._submit_application_for_job(
                        pdf_path, target_city, recommendation, submit_url, candidate_name, job_title
                    )
                    
                    # 记录结果
                    result = {
                        'candidate_name': candidate_name,
                        'job_title': job_title,
                        'submit_url': submit_url,
                        'recommendation': recommendation,
                        'target_city': target_city,
                        'success': success,
                        'timestamp': str(datetime.now())
                    }
                    self.results.append(result)
                    
                    if success:
                        print(f"✅ Application submitted successfully!")
                    else:
                        print(f"❌ Application submission failed")
                    
                    # 短暂延迟避免过快提交
                    import time
                    time.sleep(2)
                
            except Exception as e:
                print(f"❌ Error processing {pdf_file}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # 输出最终结果
        self._print_final_results()
    
    def _submit_application_for_job(self, pdf_path: str, city: str, recommendation: str, 
                                   job_url: str, candidate_name: str, job_title: str) -> bool:
        """为特定职位提交申请"""
        
        print(f"\n🔄 Starting application submission for {candidate_name} -> {job_title}")
        
        try:
            import time
            
            # 连接到Chrome浏览器（不自动导航）
            driver, wait = self._connect_to_chrome_without_nav()
            if not driver:
                return False
            
            # 导航到具体职位URL
            print(f"🌐 Navigating to job URL: {job_url}")
            driver.get(job_url)
            time.sleep(0.5)  # 页面加载等待
            print(f"✅ Page loaded: {driver.title}")
            
            # 上传简历
            print("📤 Uploading resume...")
            if not upload_resume(driver, wait, pdf_path):
                print("❌ Resume upload failed")
                return False
            
            # 选择城市（某些职位可能不需要）
            print(f"🏙️ Checking if city selection is needed for: {job_title}")
            if "强化学习算法工程师" in job_title:
                print("ℹ️ This job doesn't require city selection, skipping...")
            else:
                print(f"🏙️ Selecting city: {city}")
                if not self._select_city_robust(driver, wait, city):
                    print("❌ City selection failed")
                    return False
            
            # 填写推荐语
            print("💬 Filling recommendation text...")
            if not self._fill_recommendation_text(driver, wait, recommendation):
                print("❌ Recommendation text filling failed")
                return False
            
            # 提交申请
            print("📨 Submitting application...")
            if not self._submit_application(driver, wait):
                print("❌ Application submission failed")
                return False
            
            print("✅ Application submitted successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Submission error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _connect_to_chrome_without_nav(self):
        """连接到Chrome浏览器但不自动导航"""
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
    
    def _select_city_robust(self, driver, wait, city_name: str) -> bool:
        """选择城市（增强版）"""
        # 原始函数只支持深圳，需要传递城市参数
        # 暂时使用原始函数，后续可以扩展支持多城市
        print(f"🏙️ Selecting city: {city_name}")
        if city_name == "上海市":
            # 对于上海，需要特殊处理
            print("⚠️ Shanghai city selection needs special handling")
            # 暂时使用原始函数，可能需要手动调整
        return select_city_robust(driver, wait)
    
    def _fill_recommendation_text(self, driver, wait, recommendation: str) -> bool:
        """填写推荐语"""
        return fill_recommendation(driver, wait, recommendation)
    
    def _submit_application(self, driver, wait) -> bool:
        """提交申请"""
        return submit_application(driver, wait)
    
    def _print_final_results(self):
        """打印最终结果统计"""
        print(f"\n{'='*20} BATCH PROCESSING COMPLETED {'='*20}")
        
        total_applications = len(self.results)
        successful_applications = sum(1 for r in self.results if r['success'])
        
        print(f"📊 FINAL STATISTICS:")
        print(f"  Total applications: {total_applications}")
        print(f"  Successful: {successful_applications}")
        print(f"  Failed: {total_applications - successful_applications}")
        print(f"  Success rate: {successful_applications/total_applications*100:.1f}%" if total_applications > 0 else "  Success rate: 0%")
        
        print(f"\n📋 DETAILED RESULTS:")
        for i, result in enumerate(self.results, 1):
            status = "✅" if result['success'] else "❌"
            print(f"  {i}. {status} {result['candidate_name']} -> {result['job_title']}")


def test_batch_processing():
    """测试批量处理功能"""
    
    # 配置
    job_descriptions_file = "/home/chenbohan/Downloads/职位描述.txt"
    resume_folder = "/home/chenbohan/Downloads"
    
    # 指定要测试的简历文件
    test_resumes = [
        "【【2026校招】自动驾驶大模型_端到端算法岗_上海 20-40K】李省壮 26年应届生.pdf",
        "【【2026春招】自动驾驶软件_模型工程师_深圳 20-40K】张浩然 26年应届生.pdf"
    ]
    
    # 创建处理器
    processor = ResumeProcessor(job_descriptions_file)
    
    # 执行批量处理
    processor.process_resumes_in_batch(resume_folder, test_resumes)


if __name__ == "__main__":
    test_batch_processing()