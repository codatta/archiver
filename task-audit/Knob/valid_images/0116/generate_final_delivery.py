#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成最终可交付的CSV文件：
1. 从旋钮_交付_1.csv中保留审核结果为1的记录
2. 加上旋钮_交付_补充.csv的所有记录
"""

import csv
from pathlib import Path

# 路径配置
BASE_DIR = Path(__file__).parent
CSV_FILE_1 = BASE_DIR / "旋钮_交付_1.csv"
REVIEW_RESULT_CSV = BASE_DIR / "result" / "review_results.csv"
CSV_FILE_SUPPLEMENT = BASE_DIR / "旋钮_交付_补充.csv"
OUTPUT_CSV = BASE_DIR / "旋钮_交付_最终.csv"

def load_approved_submission_ids():
    """加载审核结果为1的submission_id集合"""
    approved_ids = set()
    if not REVIEW_RESULT_CSV.exists():
        print(f"警告: 审核结果文件不存在: {REVIEW_RESULT_CSV}")
        return approved_ids
    
    with open(REVIEW_RESULT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['review_result'] == '1':
                approved_ids.add(row['submission_id'])
    
    return approved_ids

def load_csv_data(csv_file):
    """加载CSV文件数据"""
    data = []
    if not csv_file.exists():
        print(f"警告: 文件不存在: {csv_file}")
        return data
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    return data

def main():
    print("=" * 60)
    print("生成最终可交付CSV文件")
    print("=" * 60)
    
    # 1. 加载审核结果为1的submission_id
    print(f"\n1. 读取审核结果文件: {REVIEW_RESULT_CSV}")
    approved_ids = load_approved_submission_ids()
    print(f"   找到 {len(approved_ids)} 条审核通过的记录")
    
    # 2. 从旋钮_交付_1.csv中筛选审核通过的记录
    print(f"\n2. 读取并筛选: {CSV_FILE_1}")
    data_1 = load_csv_data(CSV_FILE_1)
    print(f"   原始数据: {len(data_1)} 条")
    
    approved_data = []
    for row in data_1:
        if row['submission_id'] in approved_ids:
            approved_data.append(row)
    
    print(f"   筛选后: {len(approved_data)} 条")
    
    # 3. 加载补充数据
    print(f"\n3. 读取补充数据: {CSV_FILE_SUPPLEMENT}")
    supplement_data = load_csv_data(CSV_FILE_SUPPLEMENT)
    print(f"   补充数据: {len(supplement_data)} 条")
    
    # 4. 合并数据
    print(f"\n4. 合并数据...")
    final_data = approved_data + supplement_data
    
    # 检查是否有重复的submission_id
    submission_ids = [row['submission_id'] for row in final_data]
    unique_ids = set(submission_ids)
    if len(submission_ids) != len(unique_ids):
        duplicates = len(submission_ids) - len(unique_ids)
        print(f"   警告: 发现 {duplicates} 条重复的submission_id")
        # 去重，保留第一次出现的记录
        seen = set()
        final_data_dedup = []
        for row in final_data:
            if row['submission_id'] not in seen:
                seen.add(row['submission_id'])
                final_data_dedup.append(row)
        final_data = final_data_dedup
        print(f"   去重后: {len(final_data)} 条")
    
    print(f"   最终数据: {len(final_data)} 条")
    
    # 5. 保存结果
    print(f"\n5. 保存结果到: {OUTPUT_CSV}")
    if len(final_data) == 0:
        print("   错误: 没有数据可保存！")
        return
    
    # 获取列名
    fieldnames = list(final_data[0].keys())
    
    with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(final_data)
    
    print(f"   保存成功！")
    
    # 6. 统计信息
    print("\n" + "=" * 60)
    print("统计信息")
    print("=" * 60)
    print(f"审核通过的数据: {len(approved_data)} 条")
    print(f"补充数据: {len(supplement_data)} 条")
    print(f"最终数据: {len(final_data)} 条")
    print(f"\n输出文件: {OUTPUT_CSV}")

if __name__ == '__main__':
    main()
