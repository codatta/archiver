#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合并两个CSV文件：
1. 旋钮_交付_2.csv（新的一批数据，都是审核通过的）
2. 旋钮_交付_通过_20260124_165422.csv（之前审核通过的记录）
3. 合并到一个最终交付文件中
4. 检查并去除重复的submission_id（如果有的话）
"""

import csv
from pathlib import Path
from datetime import datetime

# 路径配置
BASE_DIR = Path(__file__).parent
SOURCE_FILE_1 = BASE_DIR / "旋钮_交付_2.csv"
SOURCE_FILE_2 = BASE_DIR / "旋钮_交付_通过_20260124_165422.csv"
OUTPUT_FILE = BASE_DIR / ("旋钮_交付_最终合并_" + datetime.now().strftime('%Y%m%d_%H%M%S') + ".csv")

def merge_csv_files():
    """
    合并两个CSV文件，去除重复记录
    """
    print("=" * 60)
    print("合并CSV文件")
    print("=" * 60)
    print(f"源文件1: {SOURCE_FILE_1}")
    print(f"源文件2: {SOURCE_FILE_2}")
    print(f"输出文件: {OUTPUT_FILE}")
    
    # 检查源文件是否存在
    if not SOURCE_FILE_1.exists():
        print(f"错误: 源文件1不存在于 {SOURCE_FILE_1}")
        return
    
    if not SOURCE_FILE_2.exists():
        print(f"错误: 源文件2不存在于 {SOURCE_FILE_2}")
        return
    
    # 用于去重的集合
    seen_submission_ids = set()
    merged_records = []
    header = None
    
    # 读取第一个文件
    print(f"\n读取文件1: {SOURCE_FILE_1.name}")
    with open(SOURCE_FILE_1, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames
        for row in reader:
            submission_id = row['submission_id']
            if submission_id not in seen_submission_ids:
                seen_submission_ids.add(submission_id)
                merged_records.append(row)
    
    file1_count = len(merged_records)
    print(f"文件1包含 {file1_count} 条记录")
    
    # 读取第二个文件
    print(f"\n读取文件2: {SOURCE_FILE_2.name}")
    duplicate_count = 0
    with open(SOURCE_FILE_2, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            submission_id = row['submission_id']
            if submission_id not in seen_submission_ids:
                seen_submission_ids.add(submission_id)
                merged_records.append(row)
            else:
                duplicate_count += 1
    
    file2_unique_count = len(merged_records) - file1_count
    file2_total_count = file2_unique_count + duplicate_count
    
    print(f"文件2包含 {file2_total_count} 条记录")
    print(f"其中 {file2_unique_count} 条唯一记录，{duplicate_count} 条重复记录（已跳过）")
    
    # 写入合并后的文件
    print(f"\n写入合并文件...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(merged_records)
    
    # 输出统计信息
    print("\n" + "=" * 60)
    print("合并完成!")
    print("=" * 60)
    print(f"文件1记录数: {file1_count}")
    print(f"文件2唯一记录数: {file2_unique_count}")
    print(f"重复记录数: {duplicate_count}")
    print(f"合并后总记录数: {len(merged_records)}")
    print(f"\n合并文件: {OUTPUT_FILE}")
    print(f"文件大小: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")
    
    # 验证合并结果
    print(f"\n验证合并结果:")
    print(f"✓ 所有记录都有唯一的submission_id")
    print(f"✓ 保持了原始文件的格式和结构")
    
    if duplicate_count > 0:
        print(f"\n⚠️  发现 {duplicate_count} 条重复记录已自动去除")
    else:
        print(f"\n✓ 没有发现重复记录")

if __name__ == '__main__':
    merge_csv_files()