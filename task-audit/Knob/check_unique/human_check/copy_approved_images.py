#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据审核结果，将通过的图片拷贝到result/images目录
"""

import csv
import shutil
from pathlib import Path
import sys

# 添加父目录到路径以便导入utils
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import get_base_dir

# 配置路径
BASE_DIR = get_base_dir()
REVIEW_RESULT_CSV = Path(__file__).parent / "result" / "review_results.csv"
CLEAN_DATA_CSV = BASE_DIR / "check_unique" / "files" / "clean_data.csv"
TARGET_DIR = Path(__file__).parent / "result" / "images"

def main():
    # 读取审核结果
    print("=" * 60)
    print("拷贝审核通过的图片")
    print("=" * 60)
    
    if not REVIEW_RESULT_CSV.exists():
        print(f"错误: 审核结果文件不存在: {REVIEW_RESULT_CSV}")
        return
    
    if not CLEAN_DATA_CSV.exists():
        print(f"错误: 干净数据文件不存在: {CLEAN_DATA_CSV}")
        return
    
    # 读取审核结果，找出通过的submission_id
    approved_ids = set()
    total_reviews = 0
    
    try:
        with open(REVIEW_RESULT_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                total_reviews += 1
                if row['review_result'] == '1':
                    approved_ids.add(row['submission_id'])
        
        print(f"审核结果总数: {total_reviews}")
        print(f"通过的图片数: {len(approved_ids)}")
    except Exception as e:
        print(f"错误: 读取审核结果文件失败: {e}")
        return
    
    if len(approved_ids) == 0:
        print("没有通过的图片需要拷贝")
        return
    
    # 读取干净数据，创建submission_id到filepath的映射
    submission_to_filepath = {}
    total_clean = 0
    
    try:
        with open(CLEAN_DATA_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                total_clean += 1
                submission_id = row['submission_id']
                if submission_id in approved_ids:
                    submission_to_filepath[submission_id] = {
                        'filepath': row['filepath'],
                        'filename': row['filename']
                    }
        
        print(f"干净数据总数: {len(submission_to_filepath)} 张需要拷贝")
    except Exception as e:
        print(f"错误: 读取干净数据文件失败: {e}")
        return
    
    # 创建目标目录
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    print(f"目标目录: {TARGET_DIR}")
    print("开始拷贝...\n")
    
    # 统计信息
    copied_count = 0
    skipped_count = 0
    error_count = 0
    
    # 遍历通过的图片
    for submission_id, file_info in submission_to_filepath.items():
        source_path = Path(file_info['filepath'])
        filename = file_info['filename']
        target_path = TARGET_DIR / filename
        
        # 检查源文件是否存在
        if not source_path.exists():
            print(f"警告: 源文件不存在: {source_path}")
            error_count += 1
            continue
        
        # 如果目标文件已存在，跳过
        if target_path.exists():
            skipped_count += 1
            if skipped_count % 100 == 0:
                print(f"已跳过: {skipped_count} 张图片...")
            continue
        
        # 拷贝文件
        try:
            shutil.copy2(str(source_path), str(target_path))
            copied_count += 1
            if copied_count % 100 == 0:
                print(f"已拷贝: {copied_count} 张图片...")
        except Exception as e:
            print(f"错误: 拷贝失败 {filename}: {e}")
            error_count += 1
    
    # 输出统计信息
    print("\n" + "=" * 60)
    print("拷贝完成!")
    print("=" * 60)
    print(f"成功拷贝: {copied_count} 张")
    print(f"跳过 (已存在): {skipped_count} 张")
    print(f"错误: {error_count} 张")
    print(f"目标目录: {TARGET_DIR}")

if __name__ == '__main__':
    main()
