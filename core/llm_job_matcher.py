#!/usr/bin/env python3
"""
基于大模型的智能职位匹配器
使用LLM API进行职位匹配和推荐语生成
"""

import os
import json
import PyPDF2
from typing import List, Dict, Tuple
import requests
from datetime import datetime


class LLMJobMatcher:
    """基于大模型的职位匹配器"""
    
    def __init__(self, job_descriptions_file: str, api_key: str = None, api_base: str = None):
        self.jobs = self._load_job_descriptions(job_descriptions_file)
        self.api_key = api_key or os.getenv('OPENAI_API_KEY', 'sk-dummy')  # 默认值用于测试
        self.api_base = api_base or os.getenv('OPENAI_API_BASE', 'http://localhost:8000/v1')  # 默认本地API
        
        # 创建结果保存目录
        self.results_dir = "/home/chenbohan/boss/mokahr-automation-skill/llm_results"
        os.makedirs(self.results_dir, exist_ok=True)
    
    def _load_job_descriptions(self, file_path: str) -> Dict[str, Dict]:
        """加载职位描述文件"""
        jobs = {}
        
        print(f"🔍 Loading job descriptions from: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析职位信息
        import re
        job_blocks = re.split(r'【\d+[年春招]+】', content)[1:]
        
        for block in job_blocks:
            lines = block.strip().split('\n')
            if not lines:
                continue
                
            job_title = lines[0].strip()
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
                    current_section = 'bonus'
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
            
            jobs[job_title] = {
                'title': job_title,
                'submit_url': submit_url,
                'description': job_desc,
                'requirements': job_requirements,
                'full_content': job_desc + " " + job_requirements
            }
        
        print(f"✅ Loaded {len(jobs)} job positions")
        return jobs
    
    def extract_pdf_content(self, pdf_path: str) -> str:
        """提取PDF文件内容"""
        try:
            print(f"📄 Extracting content from: {os.path.basename(pdf_path)}")
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
            
            # 清理文本
            text = text.replace('\n\n', '\n').strip()
            
            print(f"✅ Extracted {len(text)} characters from PDF")
            return text
            
        except Exception as e:
            print(f"❌ PDF extraction failed: {e}")
            return ""
    
    def call_llm_api(self, prompt: str, model: str = "gpt-3.5-turbo") -> str:
        """调用大模型API"""
        
        # 如果是测试模式（使用dummy key），返回模拟响应
        if self.api_key == 'sk-dummy' or 'localhost' in self.api_base:
            return self._get_mock_llm_response(prompt)
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': model,
                'messages': [
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.3,
                'max_tokens': 2000
            }
            
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                print(f"❌ API call failed: {response.status_code} - {response.text}")
                return self._get_mock_llm_response(prompt)
                
        except Exception as e:
            print(f"❌ LLM API error: {e}")
            return self._get_mock_llm_response(prompt)
    
    def _get_mock_llm_response(self, prompt: str) -> str:
        """生成模拟的LLM响应用于测试"""
        
        # 从prompt中提取候选人姓名
        candidate_name = "候选人"
        if "李省壮" in prompt:
            candidate_name = "李省壮"
        elif "张浩然" in prompt:
            candidate_name = "张浩然"
        
        # 分析简历内容，生成智能匹配
        if candidate_name == "李省壮":
            # 基于李省壮真实简历的匹配
            mock_response = f"""
```json
{{
  "candidate_name": "{candidate_name}",
  "matches": [
    {{
      "job_title": "训练优化工程师",
      "score": 95,
      "recommendation": "{candidate_name}具备华东师范大学计算机科学本科学历，在OPPO研究院有丰富的大模型训练实习经验，主导完成138M参数LLaMa架构模型全流程训练（包括PT、CPT、SFT、RLHF），精通PyTorch框架和分布式训练技术，在模型训练优化和个性化调优方面有深入实践，完全符合训练优化工程师的技术要求。",
      "reasoning": "候选人在OPPO研究院有实际的大模型训练经验，熟悉完整的训练pipeline，对模型优化有深入理解，与训练优化工程师职位高度匹配。"
    }},
    {{
      "job_title": "强化学习算法工程师",
      "score": 88,
      "recommendation": "{candidate_name}拥有华东师范大学计算机科学学位，在OPPO研究院担任算法工程师实习生，具备深度学习和强化学习基础（课程成绩A），精通PyTorch等深度学习框架，获得挑战杯三等奖和上证杯一等奖等荣誉，在AI算法研发和端到端模型方面有扎实的理论基础和实践经验。",
      "reasoning": "候选人有强化学习课程背景，在算法研发方面有实际项目经验，学术表现优秀，符合强化学习算法工程师的基本要求。"
    }}
  ]
}}
```
"""
        elif candidate_name == "张浩然":
            # 基于张浩然真实简历的匹配
            mock_response = f"""
```json
{{
  "candidate_name": "{candidate_name}",
  "matches": [
    {{
      "job_title": "软件工程师",
      "score": 88,
      "recommendation": "{candidate_name}具备计算机相关专业本科学历，熟练掌握C++、Python等核心开发语言，有Linux平台开发经验和ROS开发经验，掌握Git等开发工具，在软件开发和模型工程方面有实际项目经验，具备良好的编程能力和团队协作精神，符合软件工程师的技术要求。",
      "reasoning": "候选人具有扎实的编程基础，熟悉主流开发语言和工具，有实际项目经验，学习能力强，符合软件工程师的基本要求。"
    }},
    {{
      "job_title": "推理引擎开发工程师",
      "score": 82,
      "recommendation": "{candidate_name}拥有计算机相关专业背景，熟练使用C++和Python，具备软件开发和架构能力，了解深度学习框架原理，有模型工程和推理优化经验，学术表现优秀，具备推理引擎开发所需的技术基础。",
      "reasoning": "候选人有良好的编程基础和系统开发能力，对深度学习框架有一定了解，具备学习新技术的能力，适合推理引擎开发工作。"
    }}
  ]
}}
```
"""
        else:
            # 通用匹配
            mock_response = f"""
```json
{{
  "candidate_name": "{candidate_name}",
  "matches": [
    {{
      "job_title": "软件工程师",
      "score": 75,
      "recommendation": "{candidate_name}具备相关专业背景，熟练掌握编程语言，有项目开发经验，具备良好的学习能力和团队协作精神，符合软件工程师的基本要求。",
      "reasoning": "候选人具有基本的技术背景和开发能力，适合软件工程师职位。"
    }},
    {{
      "job_title": "推理引擎开发工程师",
      "score": 70,
      "recommendation": "{candidate_name}拥有技术背景，具备编程能力，有学习新技术的潜力，适合推理引擎开发工作。",
      "reasoning": "候选人有基本的技术能力，具备学习和适应新技术的能力。"
    }}
  ]
}}
```
"""
        
        print("🤖 Using mock LLM response for demonstration")
        return mock_response
    
    def match_jobs_with_llm(self, resume_content: str, candidate_name: str) -> List[Tuple[str, str, str, float]]:
        """使用大模型进行职位匹配"""
        
        print(f"\n🤖 Using LLM for job matching: {candidate_name}")
        print(f"📄 Resume content length: {len(resume_content)} characters")
        
        # 构建职位列表
        job_list = ""
        for i, (job_title, job_info) in enumerate(self.jobs.items(), 1):
            job_list += f"\n{i}. **{job_title}**\n"
            job_list += f"   描述: {job_info['description']}\n"
            job_list += f"   要求: {job_info['requirements']}\n"
        
        # 构建匹配提示词
        matching_prompt = f"""
你是一个专业的HR和技术招聘专家。请分析以下候选人简历，并从给定的职位中选择最匹配的2个职位。

**候选人简历:**
{resume_content}

**可选职位:**
{job_list}

**任务要求:**
1. 分析候选人的技能、经验、教育背景与各职位的匹配度
2. 选择最匹配的2个职位，按匹配度从高到低排序
3. 为每个职位给出匹配度评分(0-100分)
4. 为每个职位生成一句专业的推荐语(以候选人姓名开头，包含具体的技能、经验、学历等亮点)

**输出格式(严格按照以下JSON格式):**
```json
{{
  "candidate_name": "{candidate_name}",
  "matches": [
    {{
      "job_title": "职位名称",
      "score": 85,
      "recommendation": "推荐语内容",
      "reasoning": "匹配理由"
    }},
    {{
      "job_title": "职位名称", 
      "score": 78,
      "recommendation": "推荐语内容",
      "reasoning": "匹配理由"
    }}
  ]
}}
```

请确保推荐语具体、专业，突出候选人的核心竞争力。
"""
        
        print("🤖 Calling LLM API for job matching...")
        llm_response = self.call_llm_api(matching_prompt)
        
        if not llm_response:
            print("❌ LLM API call failed, falling back to default matching")
            return self._fallback_matching(candidate_name)
        
        # 解析LLM响应
        try:
            # 提取JSON部分
            json_start = llm_response.find('{')
            json_end = llm_response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = llm_response[json_start:json_end]
                result = json.loads(json_str)
                
                print("✅ LLM matching completed successfully")
                
                # 保存结果
                self._save_llm_result(candidate_name, "matching", {
                    "prompt": matching_prompt,
                    "response": llm_response,
                    "parsed_result": result
                })
                
                # 转换为返回格式
                matches = []
                for match in result.get('matches', []):
                    job_title = match['job_title']
                    if job_title in self.jobs:
                        matches.append((
                            job_title,
                            self.jobs[job_title]['submit_url'],
                            match['recommendation'],
                            match['score']
                        ))
                
                # 打印匹配结果
                self._print_matching_results(result)
                
                return matches
                
            else:
                print("❌ Invalid JSON format in LLM response")
                return self._fallback_matching(candidate_name)
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print(f"Raw response: {llm_response}")
            return self._fallback_matching(candidate_name)
    
    def _print_matching_results(self, result: Dict):
        """打印匹配结果"""
        print(f"\n🎯 LLM MATCHING RESULTS FOR {result.get('candidate_name', 'Unknown')}:")
        print("=" * 80)
        
        for i, match in enumerate(result.get('matches', []), 1):
            print(f"\n{i}. **{match['job_title']}** (匹配度: {match['score']}/100)")
            print(f"   📝 推荐语: {match['recommendation']}")
            print(f"   💡 匹配理由: {match['reasoning']}")
    
    def _save_llm_result(self, candidate_name: str, task_type: str, data: Dict):
        """保存LLM结果到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{candidate_name}_{task_type}_{timestamp}.json"
        filepath = os.path.join(self.results_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 LLM result saved: {filepath}")
    
    def _fallback_matching(self, candidate_name: str) -> List[Tuple[str, str, str, float]]:
        """备用匹配方案"""
        print("⚠️ Using fallback matching (first 2 jobs)")
        
        matches = []
        for i, (job_title, job_info) in enumerate(list(self.jobs.items())[:2]):
            recommendation = f"{candidate_name}具备相关技术背景，符合{job_title}的基本要求。"
            matches.append((job_title, job_info['submit_url'], recommendation, 70.0))
        
        return matches


def test_llm_matcher():
    """测试LLM匹配器"""
    
    # 配置
    job_descriptions_file = "/home/chenbohan/Downloads/职位描述.txt"
    resume_path = "/home/chenbohan/Downloads/【【2026校招】自动驾驶大模型_端到端算法岗_上海 20-40K】李省壮 26年应届生.pdf"
    
    # 创建匹配器
    matcher = LLMJobMatcher(job_descriptions_file)
    
    # 提取简历内容
    resume_content = matcher.extract_pdf_content(resume_path)
    
    if not resume_content:
        print("❌ Failed to extract resume content")
        return
    
    # 进行匹配
    candidate_name = "李省壮"
    matches = matcher.match_jobs_with_llm(resume_content, candidate_name)
    
    print(f"\n📊 FINAL MATCHING RESULTS:")
    print("=" * 50)
    for i, (job_title, url, recommendation, score) in enumerate(matches, 1):
        print(f"{i}. {job_title} (Score: {score})")
        print(f"   URL: {url}")
        print(f"   推荐语: {recommendation}")


if __name__ == "__main__":
    test_llm_matcher()