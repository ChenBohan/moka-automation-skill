#!/usr/bin/env python3
"""
处理jianli文件夹中的新简历
"""

import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the batch processor
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core'))
from batch_resume_processor import ResumeProcessor

def main():
    """处理jianli文件夹中的所有简历"""
    
    print("🚀 PROCESSING JIANLI FOLDER RESUMES")
    print("=" * 60)
    
    # 配置路径
    job_descriptions_file = "/home/chenbohan/Downloads/职位描述.txt"
    resume_folder = "/home/chenbohan/Downloads/jianli"
    
    # 检查文件夹是否存在
    if not os.path.exists(resume_folder):
        print(f"❌ Resume folder not found: {resume_folder}")
        return
    
    # 获取所有PDF文件
    pdf_files = [f for f in os.listdir(resume_folder) if f.endswith('.pdf')]
    
    if not pdf_files:
        print(f"❌ No PDF files found in {resume_folder}")
        return
    
    print(f"📁 Found {len(pdf_files)} PDF resumes:")
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"  {i}. {pdf_file}")
    
    print(f"\n⏰ Starting processing at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 创建处理器
    try:
        processor = ResumeProcessor(job_descriptions_file)
        print("✅ ResumeProcessor initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize ResumeProcessor: {e}")
        return
    
    # 执行批量处理
    try:
        processor.process_resumes_in_batch(resume_folder, pdf_files)
        print(f"\n⏰ Processing completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")
        import traceback
        traceback.print_exc()
        return

if __name__ == "__main__":
    main()