#!/usr/bin/env python3
"""
测试新简历的批量处理
"""

import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.batch_resume_processor import ResumeProcessor


def main():
    """测试新简历批量处理"""
    
    # 配置文件路径
    job_descriptions_file = "/home/chenbohan/Downloads/职位描述.txt"
    resume_folder = "/home/chenbohan/Downloads/jianli"
    
    # 新简历文件列表
    new_resumes = [
        "【【2026春招】自动驾驶软件_模型工程师_上海 20-40K】钟利剑 26年应届生.pdf",
        "【【2026校招】自动驾驶大模型_端到端算法岗_上海 20-40K】Rue Wu 26年应届生.pdf", 
        "【【2026校招】自动驾驶大模型_端到端算法岗_上海 20-40K】樊文艳 26年应届生.pdf",
        "【【2026校招】软件_数据_后端_嵌入式工程岗_深圳 20-40K】明瑞煜 26年应届生.pdf"
    ]
    
    print(f"🧪 Testing {len(new_resumes)} new resumes")
    for i, resume in enumerate(new_resumes, 1):
        print(f"  {i}. {resume}")
    
    # 检查文件是否存在
    missing_files = []
    for resume in new_resumes:
        resume_path = os.path.join(resume_folder, resume)
        if not os.path.exists(resume_path):
            missing_files.append(resume)
    
    if missing_files:
        print(f"❌ Missing resume files:")
        for file in missing_files:
            print(f"  - {file}")
        return
    
    print(f"✅ All resume files found")
    
    # 创建处理器并执行批量处理
    processor = ResumeProcessor(job_descriptions_file)
    processor.process_resumes_in_batch(resume_folder, new_resumes)
    
    # 打印最终统计
    print(f"\n📊 FINAL BATCH PROCESSING RESULTS:")
    print(f"Total candidates processed: {len(set(r['candidate_name'] for r in processor.results))}")
    print(f"Total applications: {len(processor.results)}")
    
    success_count = sum(1 for r in processor.results if r['success'])
    print(f"Successful applications: {success_count}")
    print(f"Failed applications: {len(processor.results) - success_count}")
    print(f"Overall success rate: {success_count/len(processor.results)*100:.1f}%" if processor.results else "No applications")
    
    # 按候选人分组显示结果
    candidates = {}
    for result in processor.results:
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
            print(f"    {status} {result['job_title']}")


if __name__ == "__main__":
    main()