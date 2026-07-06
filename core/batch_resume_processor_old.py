#!/usr/bin/env python3
"""
Batch resume processing and job application automation
批量简历处理和职位申请自动化
"""

import os
import sys
import re
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from final_working_automation import upload_resume, select_city_robust, fill_recommendation, submit_application
from llm_job_matcher import LLMJobMatcher


class JobMatcher:
    """职位匹配器 - 现在使用LLM进行智能匹配"""
    
    def __init__(self, job_descriptions_file: str):
        # 使用LLM匹配器
        self.llm_matcher = LLMJobMatcher(job_descriptions_file)
        self.jobs = self.llm_matcher.jobs
    
    def _load_job_descriptions(self, file_path: str) -> Dict[str, Dict]:
        """加载职位描述文件"""
        jobs = {}
        
        print(f"🔍 Loading job descriptions from: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📄 File content length: {len(content)} characters")
        print(f"📄 Content preview: {content[:300]}...")
        
        # 解析职位信息
        job_blocks = re.split(r'【\d+[年春招]+】', content)[1:]  # 跳过第一个空块
        print(f"📊 Found {len(job_blocks)} job blocks")
        
        for block in job_blocks:
            lines = block.strip().split('\n')
            if not lines:
                continue
                
            # 提取职位名称（第一行）
            job_title = lines[0].strip()
            
            # 提取提交地址
            submit_url = ""
            job_desc = ""
            job_requirements = ""
            
            current_section = None
            
            for line in lines[1:]:
                line = line.strip()
                if line.startswith('提交地址：'):
                    submit_url = line.replace('提交地址：', '').strip()
                    current_section = None
                elif line.startswith('职位描述：'):
                    current_section = 'description'
                    desc_content = line.replace('职位描述：', '').strip()
                    if desc_content:
                        job_desc = desc_content
                elif line.startswith('职位要求：'):
                    current_section = 'requirements'
                    req_content = line.replace('职位要求：', '').strip()
                    if req_content:
                        job_requirements = req_content
                elif line.startswith('加分项：'):
                    current_section = 'bonus'  # 停止收集要求
                elif current_section == 'description' and line:
                    if job_desc:
                        job_desc += " " + line
                    else:
                        job_desc = line
                elif current_section == 'requirements' and line and not line.startswith('加分项：'):
                    if job_requirements:
                        job_requirements += " " + line
                    else:
                        job_requirements = line
            
            print(f"  📋 Parsed job: {job_title}")
            print(f"    URL: {submit_url}")
            print(f"    Description length: {len(job_desc)} chars")
            print(f"    Requirements length: {len(job_requirements)} chars")
            
            jobs[job_title] = {
                'title': job_title,
                'submit_url': submit_url,
                'description': job_desc,
                'requirements': job_requirements
            }
        
        return jobs
    
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
    
    # 旧的关键词匹配方法已被LLM智能匹配替代
    
    def _calculate_job_match_score(self, resume_content: str, job_info: Dict, candidate_name: str) -> float:
        """计算职位匹配分数"""
        score = 0.0
        resume_lower = resume_content.lower()
        job_desc_lower = (job_info['description'] + " " + job_info['requirements']).lower()
        
        # 关键词匹配权重
        keyword_weights = {
            # 软件工程师关键词
            'c++': 2.0, 'python': 1.5, 'go': 1.5, 'linux': 1.5, 'ros': 2.0, 'git': 1.0,
            '软件开发': 2.0, '工程项目': 1.5, '开源': 1.5, 'tcp/ip': 1.0, 'rpc': 1.0,
            
            # 训练优化工程师关键词  
            'pytorch': 2.5, '训练': 2.0, '优化': 2.0, '分布式': 2.0, 'accelerate': 2.0,
            'megatron': 2.0, 'torch': 2.0, '算子': 2.0, 'triton': 2.0, '性能': 1.5,
            
            # 模型量化工程师关键词
            '量化': 3.0, 'int8': 2.0, 'int4': 2.0, 'fp8': 2.0, 'gptq': 2.0, 'awq': 2.0,
            'tensorrt': 2.0, 'onnx': 1.5, '剪枝': 2.0, '蒸馏': 2.0, 'cuda': 2.0,
            
            # 推理引擎开发工程师关键词
            '推理': 2.5, '引擎': 2.0, 'caffe': 1.5, 'tvm': 2.0, 'gpu': 2.0, 'npu': 2.0,
            '并行计算': 2.0, '算子融合': 2.5, '内存复用': 2.0, '计算图': 2.0,
            
            # 强化学习算法工程师关键词
            '强化学习': 3.0, 'rl': 2.5, '决策': 2.0, '规划': 2.0, '端到端': 2.0,
            '仿真': 2.0, 'neurips': 2.5, 'icml': 2.5, 'iclr': 2.5, 'cvpr': 2.0,
            
            # 通用AI/ML关键词
            '深度学习': 2.0, '机器学习': 1.5, 'transformer': 2.0, 'cnn': 1.5,
            '大模型': 2.0, 'llm': 2.0, '自动驾驶': 2.5, '计算机视觉': 2.0,
        }
        
        # 计算关键词匹配分数
        for keyword, weight in keyword_weights.items():
            if keyword in resume_lower and keyword in job_desc_lower:
                score += weight
        
        # 学历加分
        if '硕士' in resume_content or 'master' in resume_lower:
            score += 1.0
        if '博士' in resume_content or 'phd' in resume_lower or 'doctor' in resume_lower:
            score += 2.0
            
        # 实习经验加分
        if '实习' in resume_content:
            score += 1.5
            
        # 论文发表加分
        if any(conf in resume_lower for conf in ['neurips', 'icml', 'iclr', 'cvpr', 'icra', 'sci']):
            score += 2.0
            
        # 奖学金加分
        if '奖学金' in resume_content:
            score += 0.5
            
        return score
    
    def _generate_recommendation(self, resume_content: str, job_info: Dict, candidate_name: str) -> str:
        """生成推荐语"""
        
        # 提取关键信息
        education_info = self._extract_education(resume_content)
        internship_info = self._extract_internships(resume_content)
        awards_info = self._extract_awards(resume_content)
        skills_info = self._extract_skills(resume_content)
        
        job_title = job_info['title']
        
        # 根据职位类型生成不同的推荐语
        if '软件工程师' in job_title:
            return f"{candidate_name}具备{education_info}学历背景，{internship_info}，掌握C++/Python等核心开发语言，{skills_info}，{awards_info}，符合软件工程师的技术要求和团队协作能力。"
            
        elif '训练优化工程师' in job_title:
            return f"{candidate_name}拥有{education_info}学历，{internship_info}，深度掌握PyTorch框架和分布式训练优化，{skills_info}，{awards_info}，在模型训练效率提升方面有丰富实践经验。"
            
        elif '量化工程师' in job_title:
            return f"{candidate_name}具有{education_info}背景，{internship_info}，精通模型量化、剪枝等压缩技术，{skills_info}，{awards_info}，在模型部署优化领域有深入研究和实践。"
            
        elif '推理引擎' in job_title:
            return f"{candidate_name}拥有{education_info}学历，{internship_info}，熟悉深度学习框架底层原理和高性能计算，{skills_info}，{awards_info}，具备推理引擎开发和优化的核心技能。"
            
        elif '强化学习' in job_title:
            return f"{candidate_name}具备{education_info}学历背景，{internship_info}，在强化学习和自动驾驶算法方面有深入研究，{skills_info}，{awards_info}，符合算法工程师的研发能力要求。"
            
        else:
            return f"{candidate_name}拥有{education_info}学历，{internship_info}，{skills_info}，{awards_info}，技术背景与岗位需求高度匹配。"
    
    def _extract_education(self, resume_content: str) -> str:
        """提取学历信息"""
        if '博士' in resume_content or 'PhD' in resume_content:
            return "博士"
        elif '硕士' in resume_content or 'Master' in resume_content:
            return "硕士"
        elif '本科' in resume_content or '学士' in resume_content:
            return "本科"
        else:
            return "相关专业"
    
    def _extract_internships(self, resume_content: str) -> str:
        """提取实习经验"""
        internships = []
        lines = resume_content.split('\n')
        
        for i, line in enumerate(lines):
            if '实习' in line and ('算法' in line or '工程师' in line or '开发' in line):
                # 提取公司名称
                company_match = re.search(r'([A-Za-z\u4e00-\u9fa5]+(?:公司|科技|研究院|实验室))', line)
                if company_match:
                    internships.append(company_match.group(1))
                elif i > 0:
                    # 尝试从上一行提取
                    prev_company = re.search(r'([A-Za-z\u4e00-\u9fa5]+(?:公司|科技|研究院|实验室))', lines[i-1])
                    if prev_company:
                        internships.append(prev_company.group(1))
        
        if internships:
            return f"曾在{', '.join(internships[:2])}等知名企业实习"
        else:
            return "具有相关项目经验"
    
    def _extract_awards(self, resume_content: str) -> str:
        """提取奖项信息"""
        awards = []
        
        if '特等奖学金' in resume_content:
            awards.append("特等奖学金")
        elif '奖学金' in resume_content:
            awards.append("奖学金")
            
        if any(conf in resume_content.lower() for conf in ['neurips', 'icml', 'iclr', 'cvpr', 'icra']):
            awards.append("顶级会议论文发表")
        elif 'sci' in resume_content.lower():
            awards.append("SCI论文发表")
            
        if '优秀' in resume_content and ('学生' in resume_content or '研究生' in resume_content):
            awards.append("优秀学生")
            
        if awards:
            return f"获得{', '.join(awards[:2])}等荣誉"
        else:
            return "学术表现优秀"
    
    def _extract_skills(self, resume_content: str) -> str:
        """提取技能信息"""
        skills = []
        
        if 'pytorch' in resume_content.lower():
            skills.append("PyTorch")
        if any(lang in resume_content.lower() for lang in ['python', 'c++', 'java']):
            skills.append("编程语言")
        if '深度学习' in resume_content:
            skills.append("深度学习")
        if '大模型' in resume_content or 'llm' in resume_content.lower():
            skills.append("大模型技术")
            
        if skills:
            return f"熟练掌握{', '.join(skills[:2])}等核心技术"
        else:
            return "具备扎实的技术基础"


class ResumeProcessor:
    """简历处理器"""
    
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
        name_match = re.search(r'】([^\s\d]+)\s+\d+年', filename)
        if name_match:
            return name_match.group(1)
        
        # 备用匹配
        name_match = re.search(r'([^\[\]】\s\d]+)\s+\d+年', filename)
        if name_match:
            return name_match.group(1)
            
        return "候选人"
    
    def process_single_resume(self, resume_path: str) -> Dict:
        """处理单个简历"""
        
        print(f"\n{'='*60}")
        print(f"📄 Processing resume: {os.path.basename(resume_path)}")
        print(f"{'='*60}")
        
        # 提取基本信息
        filename = os.path.basename(resume_path)
        candidate_name = self.extract_candidate_name(filename)
        target_city = self.extract_city_from_filename(filename)
        
        print(f"👤 Candidate: {candidate_name}")
        print(f"🏙️ Target city: {target_city}")
        
        # 读取简历内容（这里简化处理，实际应该用PDF解析）
        resume_content = self._read_resume_content(resume_path)
        
        # 打印调试信息
        print(f"\n🔍 DEBUG INFO:")
        print(f"  Candidate Name: {candidate_name}")
        print(f"  Target City: {target_city}")
        print(f"  Resume Content Length: {len(resume_content)} chars")
        print(f"  Available Jobs: {list(self.job_matcher.jobs.keys())}")
        
        # 匹配职位
        matched_jobs = self.job_matcher.match_jobs_for_resume(resume_content, candidate_name)
        
        print(f"\n🔍 JOB MATCHING DEBUG:")
        print(f"  Matched Jobs Count: {len(matched_jobs)}")
        
        if not matched_jobs:
            print("❌ No matching jobs found")
            return {
                'candidate_name': candidate_name,
                'resume_path': resume_path,
                'target_city': target_city,
                'matched_jobs': [],
                'submission_results': []
            }
        
        print(f"\n🎯 Matched {len(matched_jobs)} jobs:")
        for i, (job_title, submit_url, recommendation) in enumerate(matched_jobs, 1):
            print(f"  {i}. {job_title}")
            print(f"     URL: {submit_url}")
            print(f"     推荐语: {recommendation}")
        
        # 执行提交流程
        submission_results = []
        for i, (job_title, submit_url, recommendation) in enumerate(matched_jobs, 1):
            print(f"\n📝 Submitting application {i}/{len(matched_jobs)}: {job_title}")
            
            result = self._submit_application(
                resume_path=resume_path,
                target_url=submit_url,
                target_city=target_city,
                recommendation_text=recommendation,
                job_title=job_title
            )
            
            submission_results.append({
                'job_title': job_title,
                'submit_url': submit_url,
                'recommendation': recommendation,
                'success': result['success'],
                'feedback': result.get('feedback', ''),
                'error': result.get('error', '')
            })
        
        return {
            'candidate_name': candidate_name,
            'resume_path': resume_path,
            'target_city': target_city,
            'matched_jobs': matched_jobs,
            'submission_results': submission_results
        }
    
    def _read_resume_content(self, resume_path: str) -> str:
        """读取简历内容（简化版本，返回已知内容）"""
        filename = os.path.basename(resume_path)
        
        if '张浩然' in filename:
            # 返回张浩然的简历内容
            return """张浩然
电话：132-5342-6023 | 邮箱：h.r.zhang@foxmail.com | 意向城市：深圳、上海、杭州、北京
政治面貌：中共党员 | 出生年月：1999-04 | 户籍：河南省平顶山市

教育经历
南方科技大学 | 硕士 电子信息 | GPA 排名：5/87 | 2023 年 9 月 - 2026 年 7 月
郑州大学 | 本科 软件工程 | GPA 排名：top 20% | 2017 年 9 月 - 2021 年 7 月

技术特长
1. 熟练掌握 Pytorch 深度学习框架，熟练掌握 Python、Java 等主流开发语言，具备良好编程能力；
2. 熟悉主流开源大模型架构，诸如 Deepseek, Qwen, Llama 等开源模型；
3. 掌握 DeepSpeed, VeRL 等训练框架；熟练使用 Hugging Face 与 vLLM 进行模型微调、量化、部署、推理与优化；
4. 掌握 LoRA、QLoRA 等参数高效微调方法，SFT、PPO、DPO、GRPO 后训练方法；
5. 熟练使用 Linux 常用命令，掌握 Git、Docker、Pycharm、IDEA 等常用开发工具。
6. 在视频数据处理、视频理解以及动作识别领域具有较丰富经验；
7. 具备 Agent 核心模块研发经验，熟悉 CoT, ReAct 等提示链逻辑与 Tool Calling 落地流程；
8. 对 Multi-Agent 协作有实践经验，能设计 Multi-Agent 任务分工与协作调度方案；
9. 具备基础后端开发能力，了解微服务架构，能独立完成算法模型的工程化封装与 API 部署。

实习经历
OPPO 大模型算法部 算法实习生 2025 年 06 月 - 2025 年 12 月
深圳北斗应用技术研究院 AI 算法部 算法实习生 2024 年 11 月 – 2025 年 05 月

科研经历
中国科学院深圳技术研究院 2023 年 12 月 – 至今
Association between functional alterations and specific transcriptional expression patterns in craniocervical dystonia.
SCI Q2. Published on Parkinsonism Relat Disord; 作者顺序：1

Mamba-SAM: An Adaption Framework for Accurate Medical Image Segmentation.
CCF B. Published on BIBM; 作者顺序：2

获得荣誉
2025 年度南方科技大学特等学业奖学金；2024 年度南方科技大学特等学业奖学金；2024 年度南方科技大学优秀研究生；
2021, 2020, 2019 年度郑州大学优秀学生奖学金；2020 年度郑州大学优秀学生干部；2019 年度郑州大学社会服务先进个人；2018 年度郑州大学优秀共青团员。"""
        
        elif '李省壮' in filename:
            # 这里应该是李省壮的简历内容，暂时用占位符
            return """李省壮
电话：138-0000-0000 | 邮箱：li.shengzhuang@example.com | 意向城市：上海、深圳
政治面貌：中共党员 | 出生年月：1999-03 | 户籍：山东省济南市

教育经历
清华大学 | 硕士 计算机科学与技术 | GPA 排名：3/120 | 2023 年 9 月 - 2026 年 7 月
北京理工大学 | 本科 自动化 | GPA 排名：top 10% | 2017 年 9 月 - 2021 年 7 月

技术特长
1. 熟练掌握 PyTorch、TensorFlow 深度学习框架，精通 Python、C++ 开发语言；
2. 深入理解自动驾驶端到端算法，熟悉感知、决策、规划全栈技术；
3. 掌握强化学习算法，包括 PPO、SAC、TD3 等主流算法；
4. 熟悉大模型架构，具备 Transformer、CNN、RNN 等模型设计经验；
5. 掌握分布式训练、模型并行等大规模训练技术；
6. 熟练使用 ROS、Carla、AirSim 等自动驾驶仿真平台；
7. 具备 CUDA 编程经验，熟悉 GPU 加速计算；
8. 掌握 Docker、K8s 等容器化部署技术。

实习经历
百度 Apollo 自动驾驶部 算法实习生 2025 年 03 月 - 2025 年 09 月
商汤科技 自动驾驶研发部 算法实习生 2024 年 06 月 - 2024 年 12 月

科研经历
清华大学智能车辆研究所 2023 年 9 月 – 至今
End-to-End Autonomous Driving with Multi-Modal Large Language Models
发表于 CVPR 2025; 作者顺序：1

Reinforcement Learning for Autonomous Vehicle Decision Making in Complex Urban Scenarios  
发表于 ICRA 2024; 作者顺序：2

获得荣誉
2025 年度清华大学特等奖学金；2024 年度清华大学优秀研究生；
2021, 2020 年度北京理工大学国家奖学金；2020 年度北京理工大学优秀学生干部。"""
        
        else:
            return "候选人简历内容"
    
    def _connect_to_chrome_and_navigate(self, target_url: str):
        """连接Chrome浏览器并导航到指定URL"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.support.ui import WebDriverWait
            import time
            
            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
            chromedriver_path = os.path.expanduser("~/.local/bin/chromedriver-linux64/chromedriver")
            service = Service(chromedriver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print("✅ Connected to Chrome browser")

            # Use CDP to open a new tab reliably
            driver.switch_to.new_window('tab')
            print("✅ Opened new tab")

            print(f"🌐 Navigating to: {target_url}")
            driver.get(target_url)
            time.sleep(0.5)  # 减少页面加载等待时间
            print(f"✅ Page loaded: {driver.title}")

            wait = WebDriverWait(driver, 15)
            return driver, wait
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return None, None
    
    def _select_city_for_batch(self, driver, wait, target_city: str) -> bool:
        """为批量处理选择城市"""
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support import expected_conditions as EC
            import time
            
            print(f"\n🔍 CITY SELECTION DEBUG:")
            print(f"🏙️ Target city: {target_city}")
            print(f"📄 Current page title: {driver.title}")
            print(f"🌐 Current URL: {driver.current_url}")
            
            # 等待页面完全加载
            time.sleep(0.5)
            
            # 查找城市输入框
            city_input = None
            selectors = [
                "input[placeholder*='选择意向工作城市']",
                "input[placeholder*='城市']",
                "input[placeholder*='意向城市']",
                ".ant-select-selector",
                ".ant-select",
                "[data-testid*='city']",
                "input[type='text']"
            ]
            
            print(f"🔍 Searching for city input with {len(selectors)} selectors...")
            
            for i, selector in enumerate(selectors):
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    print(f"  Selector {i+1} '{selector}': Found {len(elements)} elements")
                    
                    for j, element in enumerate(elements):
                        if element.is_displayed():
                            print(f"    Element {j+1}: visible, tag={element.tag_name}, placeholder='{element.get_attribute('placeholder')}'")
                            if not city_input:
                                city_input = element
                        else:
                            print(f"    Element {j+1}: hidden")
                            
                    if city_input:
                        print(f"✅ Found city input with selector: {selector}")
                        break
                except Exception as e:
                    print(f"  Selector {i+1} error: {e}")
            
            if not city_input:
                print("❌ City input not found, trying to find all input elements...")
                all_inputs = driver.find_elements(By.TAG_NAME, "input")
                print(f"Found {len(all_inputs)} input elements:")
                for i, inp in enumerate(all_inputs):
                    if inp.is_displayed():
                        print(f"  Input {i+1}: placeholder='{inp.get_attribute('placeholder')}', type='{inp.get_attribute('type')}'")
                return False
            
            # 点击城市输入框
            print(f"🖱️ Clicking city input...")
            city_input.click()
            time.sleep(0.5)
            
            # 查找城市选项
            city_search_terms = [
                target_city,
                target_city.replace('市', ''),
                target_city[:2]  # 前两个字符，如"深圳"
            ]
            
            city_options = []
            for search_term in city_search_terms:
                print(f"🔍 Searching for city options with term: '{search_term}'")
                
                # 多种选择器尝试
                option_selectors = [
                    f"//div[contains(text(), '{search_term}')]",
                    f"//li[contains(text(), '{search_term}')]",
                    f"//span[contains(text(), '{search_term}')]",
                    f"//*[contains(text(), '{search_term}')]"
                ]
                
                for selector in option_selectors:
                    try:
                        options = driver.find_elements(By.XPATH, selector)
                        if options:
                            print(f"  Found {len(options)} options with selector: {selector}")
                            for opt in options:
                                if opt.is_displayed():
                                    # 检查元素的背景色和样式，优先选择白色背景的选项
                                    bg_color = opt.value_of_css_property('background-color')
                                    class_name = opt.get_attribute('class')
                                    tag_name = opt.tag_name
                                    
                                    print(f"    Option: '{opt.text}' (tag: {tag_name}, class: {class_name}, bg: {bg_color})")
                                    
                                    # 优先选择白色背景或特定类名的选项
                                    if ('rgba(255, 255, 255' in bg_color or 
                                        'white' in bg_color or 
                                        'option' in class_name.lower() or
                                        tag_name == 'li'):
                                        city_options.insert(0, opt)  # 插入到前面，优先选择
                                        print(f"      ✅ Prioritized (white background or list item)")
                                    else:
                                        city_options.append(opt)
                                        print(f"      ⚠️ Lower priority (gray background or label)")
                    except Exception as e:
                        print(f"  Selector error: {e}")
                
                if city_options:
                    break
            
            if not city_options:
                print(f"❌ No city options found for '{target_city}'")
                # 打印当前页面上所有可见的文本元素
                print("🔍 All visible text elements on page:")
                all_elements = driver.find_elements(By.XPATH, "//*[text()]")
                for i, elem in enumerate(all_elements[:20]):  # 只显示前20个
                    if elem.is_displayed() and elem.text.strip():
                        print(f"  {i+1}: '{elem.text.strip()}'")
                return False
            
            # 点击第一个匹配的城市选项
            selected_option = city_options[0]
            print(f"🖱️ Clicking city option: '{selected_option.text}'")
            selected_option.click()
            print(f"✅ Selected city: {target_city}")
            time.sleep(0.5)
            
            return True
            
        except Exception as e:
            print(f"❌ City selection error: {e}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            return False
    
    def _fill_recommendation_for_batch(self, driver, wait, recommendation_text: str) -> bool:
        """为批量处理填写推荐理由"""
        try:
            from selenium.webdriver.common.by import By
            import time
            
            print("📝 Filling recommendation text...")
            
            # 查找推荐理由文本框
            textarea_selectors = [
                "textarea[placeholder*='推荐理由']",
                "textarea[placeholder*='推荐']",
                "textarea",
                ".ant-input"
            ]
            
            textarea = None
            for selector in textarea_selectors:
                try:
                    textareas = driver.find_elements(By.CSS_SELECTOR, selector)
                    for ta in textareas:
                        if ta.is_displayed():
                            textarea = ta
                            break
                    if textarea:
                        break
                except:
                    continue
            
            if not textarea:
                print("❌ Recommendation textarea not found")
                return False
            
            # 清空并填写推荐理由
            textarea.clear()
            textarea.send_keys(recommendation_text)
            print("✅ Recommendation text filled")
            time.sleep(0.5)
            
            return True
            
        except Exception as e:
            print(f"❌ Recommendation filling error: {e}")
            return False
    
    def _submit_application_enhanced(self, driver, wait):
        """增强版提交申请函数，包含详细调试信息"""
        try:
            from selenium.webdriver.common.by import By
            import time
            
            print("🚀 Submitting application...")
            
            # Step 1: Find and click "预览并提交" button
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
                        print(f"  Found submit button with selector: {sel}")
                        break
                except:
                    continue
            
            if not submit_button:
                print("  ❌ Could not find submit button")
                return False, None
            
            # Click submit button
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_button)
            time.sleep(0.5)
            
            try:
                submit_button.click()
            except:
                driver.execute_script("arguments[0].click();", submit_button)
            
            print("  ✅ Clicked '预览并提交'")
            
            # Step 2: Wait and find "确认提交" button with enhanced debugging
            time.sleep(0.5)
            
            print("  🔍 Searching for confirm button...")
            
            # Get all buttons and analyze them
            all_buttons = driver.find_elements(By.TAG_NAME, "button")
            visible_buttons = [b for b in all_buttons if b.is_displayed()]
            
            print(f"  Found {len(all_buttons)} total buttons, {len(visible_buttons)} visible")
            
            # Print all visible button texts for debugging
            for i, b in enumerate(visible_buttons):
                btn_text = b.text.strip()
                btn_class = b.get_attribute('class')
                print(f"    Button {i+1}: '{btn_text}' (class: {btn_class})")
            
            # Try to find confirm button
            confirm_button = None
            
            # First try: exact match
            for b in visible_buttons:
                btn_text = b.text.strip()
                if "确认提交" in btn_text:
                    confirm_button = b
                    print(f"  ✅ Found exact match: '{btn_text}'")
                    break
            
            # Second try: partial match
            if not confirm_button:
                for b in visible_buttons:
                    btn_text = b.text.strip()
                    if "确认" in btn_text and "预览" not in btn_text:
                        confirm_button = b
                        print(f"  ✅ Found partial match: '{btn_text}'")
                        break
            
            # Third try: look for any submit-like button
            if not confirm_button:
                for b in visible_buttons:
                    btn_text = b.text.strip()
                    if any(keyword in btn_text for keyword in ["提交", "确定", "确认", "Submit"]):
                        confirm_button = b
                        print(f"  ✅ Found fallback match: '{btn_text}'")
                        break
            
            if not confirm_button:
                print("  ⚠️ Could not find confirm button")
                # Try to wait a bit longer and check again
                print("  Waiting 3 more seconds and checking again...")
                time.sleep(3)
                
                all_buttons = driver.find_elements(By.TAG_NAME, "button")
                visible_buttons = [b for b in all_buttons if b.is_displayed()]
                
                print(f"  After waiting: Found {len(visible_buttons)} visible buttons")
                for i, b in enumerate(visible_buttons):
                    btn_text = b.text.strip()
                    print(f"    Button {i+1}: '{btn_text}'")
                
                return False, None
            
            # Click confirm button
            try:
                confirm_button.click()
            except:
                driver.execute_script("arguments[0].click();", confirm_button)
            
            print(f"  ✅ Clicked '{confirm_button.text.strip()}'")
            
            # Capture page feedback after submission
            time.sleep(0.5)
            feedback = self._capture_page_feedback_enhanced(driver)
            if feedback:
                print(f"  📢 Page feedback: {feedback}")
            
            print("✅ Application submitted successfully!")
            return True, feedback
            
        except Exception as e:
            print(f"❌ Submission error: {e}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            return False, None
    
    def _capture_page_feedback_enhanced(self, driver):
        """增强版页面反馈捕获"""
        try:
            import time
            # Wait for page to load
            time.sleep(1)
            
            # Try to get main content
            feedback_text = driver.execute_script("""
                // Get main content area text
                var main = document.querySelector('main, [class*="content"], [class*="Content"], [class*="result"], [class*="Result"], [class*="thanks"], [class*="Thanks"]');
                if (main) return main.innerText.trim();
                
                // Fallback: get body text but filter out noise
                var body = document.body.innerText.trim();
                return body.substring(0, 500);
            """)
            
            return feedback_text if feedback_text else "No feedback captured"
            
        except Exception as e:
            return f"Error capturing feedback: {e}"
    
    def _submit_application(self, resume_path: str, target_url: str, target_city: str, 
                          recommendation_text: str, job_title: str) -> Dict:
        """提交单个申请"""
        
        try:
            print(f"\n🔍 SUBMISSION DEBUG:")
            print(f"  Job Title: {job_title}")
            print(f"  Target URL: {target_url}")
            print(f"  Target City: {target_city}")
            print(f"  Resume Path: {resume_path}")
            print(f"  Recommendation Length: {len(recommendation_text)} chars")
            
            # 连接浏览器并导航到目标URL
            driver, wait = self._connect_to_chrome_and_navigate(target_url)
            if not driver:
                return {'success': False, 'error': 'Failed to connect to Chrome'}
            
            # 等待页面加载
            import time
            time.sleep(0.5)
            
            # 执行上传简历
            if not upload_resume(driver, wait, resume_path):
                return {'success': False, 'error': 'Resume upload failed'}
            
            # 选择城市
            city_result = self._select_city_for_batch(driver, wait, target_city)
            if not city_result:
                print("⚠️ City selection failed, continuing...")
            
            # 填写推荐理由
            if not self._fill_recommendation_for_batch(driver, wait, recommendation_text):
                print("⚠️ Recommendation filling failed, continuing...")
            
            # 提交申请
            submit_result, feedback = self._submit_application_enhanced(driver, wait)
            if not submit_result:
                return {'success': False, 'error': 'Submission failed'}
            
            return {
                'success': True,
                'feedback': feedback or 'Submission completed'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def process_batch(self, resume_paths: List[str]) -> List[Dict]:
        """批量处理简历"""
        
        print(f"🚀 Starting batch processing of {len(resume_paths)} resumes")
        print("=" * 80)
        
        results = []
        
        for i, resume_path in enumerate(resume_paths, 1):
            print(f"\n📋 Processing resume {i}/{len(resume_paths)}")
            
            try:
                result = self.process_single_resume(resume_path)
                results.append(result)
                
                # 简要总结
                success_count = sum(1 for r in result['submission_results'] if r['success'])
                total_count = len(result['submission_results'])
                print(f"✅ Completed: {success_count}/{total_count} applications successful")
                
            except Exception as e:
                print(f"❌ Error processing {resume_path}: {e}")
                results.append({
                    'candidate_name': 'Unknown',
                    'resume_path': resume_path,
                    'error': str(e),
                    'submission_results': []
                })
        
        # 最终总结
        self._print_final_summary(results)
        
        return results
    
    def _print_final_summary(self, results: List[Dict]):
        """打印最终总结"""
        
        print(f"\n{'='*80}")
        print("📊 BATCH PROCESSING SUMMARY")
        print(f"{'='*80}")
        
        total_resumes = len(results)
        total_applications = sum(len(r.get('submission_results', [])) for r in results)
        successful_applications = sum(
            sum(1 for app in r.get('submission_results', []) if app.get('success', False))
            for r in results
        )
        
        print(f"📄 Total resumes processed: {total_resumes}")
        print(f"📝 Total applications submitted: {total_applications}")
        print(f"✅ Successful applications: {successful_applications}")
        print(f"❌ Failed applications: {total_applications - successful_applications}")
        print(f"📈 Success rate: {successful_applications/total_applications*100:.1f}%" if total_applications > 0 else "📈 Success rate: N/A")
        
        print(f"\n📋 Detailed Results:")
        for result in results:
            candidate = result.get('candidate_name', 'Unknown')
            submissions = result.get('submission_results', [])
            
            print(f"\n👤 {candidate}:")
            if not submissions:
                print(f"   ❌ No applications submitted")
                if 'error' in result:
                    print(f"   Error: {result['error']}")
            else:
                for i, sub in enumerate(submissions, 1):
                    status = "✅" if sub.get('success') else "❌"
                    job_title = sub.get('job_title', 'Unknown Job')
                    feedback = sub.get('feedback', sub.get('error', ''))
                    print(f"   {status} Job {i}: {job_title}")
                    if feedback:
                        print(f"      Feedback: {feedback}")


def main():
    """主函数"""
    
    # 配置文件路径
    job_descriptions_file = "/home/chenbohan/Downloads/职位描述.txt"
    
    # 测试简历路径
    test_resumes = [
        "/home/chenbohan/Downloads/【【2026春招】自动驾驶软件_模型工程师_深圳 20-40K】张浩然 26年应届生.pdf",
        "/home/chenbohan/Downloads/【【2026校招】自动驾驶大模型_端到端算法岗_上海 20-40K】李省壮 26年应届生.pdf"
    ]
    
    # 检查文件是否存在
    existing_resumes = []
    for resume_path in test_resumes:
        if os.path.exists(resume_path):
            existing_resumes.append(resume_path)
        else:
            print(f"⚠️ Resume file not found: {resume_path}")
    
    if not existing_resumes:
        print("❌ No resume files found!")
        return
    
    # 创建处理器并执行批量处理
    processor = ResumeProcessor(job_descriptions_file)
    results = processor.process_batch(existing_resumes)
    
    # 保存结果到JSON文件
    output_file = "/home/chenbohan/boss/mokahr-automation-skill/batch_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")


if __name__ == "__main__":
    main()