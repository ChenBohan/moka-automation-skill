#!/usr/bin/env python3
"""
测试李省壮简历的批量处理
"""

import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.batch_resume_processor import ResumeProcessor


def main():
    """测试李省壮简历"""
    
    # 配置文件路径
    job_descriptions_file = "/home/chenbohan/Downloads/职位描述.txt"
    resume_folder = "/home/chenbohan/Downloads"
    
    # 李省壮简历文件名
    test_resume_file = "【【2026校招】自动驾驶大模型_端到端算法岗_上海 20-40K】李省壮 26年应届生.pdf"
    test_resume_path = os.path.join(resume_folder, test_resume_file)
    
    # 检查文件是否存在
    if not os.path.exists(test_resume_path):
        print(f"❌ Resume file not found: {test_resume_path}")
        return
    
    print(f"🧪 Testing single resume: 李省壮")
    print(f"📄 Resume path: {test_resume_path}")
    
    # 创建处理器并执行批量处理（只处理李省壮的简历）
    processor = ResumeProcessor(job_descriptions_file)
    processor.process_resumes_in_batch(resume_folder, [test_resume_file])
    
    # 打印结果
    print(f"\n📊 SINGLE RESUME TEST COMPLETED")
    print(f"Total results: {len(processor.results)}")
    
    for result in processor.results:
        status = "✅" if result['success'] else "❌"
        print(f"  {status} {result['candidate_name']} -> {result['job_title']}")
        if not result['success']:
            print(f"      Error details available in logs")


if __name__ == "__main__":
    main()