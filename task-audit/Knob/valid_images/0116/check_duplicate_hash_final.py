#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查最终交付结果中的original_image_hash是否有重复
"""

import csv
import json
from pathlib import Path
from collections import defaultdict

# 路径配置
BASE_DIR = Path(__file__).parent
CSV_FILE = BASE_DIR / "旋钮_交付_最终.csv"

def check_duplicate_hash():
    """检查original_image_hash的重复情况"""
    hash_to_submissions = defaultdict(list)
    total_count = 0
    error_count = 0
    
    print("=" * 60)
    print("检查original_image_hash重复情况")
    print("=" * 60)
    print(f"读取文件: {CSV_FILE}\n")
    
    if not CSV_FILE.exists():
        print(f"错误: 文件不存在: {CSV_FILE}")
        return
    
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_count += 1
            submission_id = row['submission_id']
            
            try:
                # 解析JSON
                data_submission = json.loads(row['data_submission'])
                original_image_hash = data_submission.get('data', {}).get('original_image_hash', '')
                
                if original_image_hash:
                    hash_to_submissions[original_image_hash].append(submission_id)
                else:
                    print(f"警告: submission_id {submission_id} 没有original_image_hash")
            except Exception as e:
                error_count += 1
                print(f"错误: 解析submission_id {submission_id} 失败: {e}")
    
    # 统计重复情况
    duplicate_hashes = {h: subs for h, subs in hash_to_submissions.items() if len(subs) > 1}
    unique_hashes = len([h for h, subs in hash_to_submissions.items() if len(subs) == 1])
    
    print("\n" + "=" * 60)
    print("统计结果")
    print("=" * 60)
    print(f"总记录数: {total_count}")
    print(f"解析错误: {error_count}")
    print(f"唯一hash数: {unique_hashes}")
    print(f"重复hash数: {len(duplicate_hashes)}")
    
    if len(duplicate_hashes) > 0:
        print(f"\n发现 {len(duplicate_hashes)} 个重复的original_image_hash:")
        print("-" * 60)
        
        total_duplicate_records = 0
        for hash_value, submission_ids in sorted(duplicate_hashes.items(), key=lambda x: len(x[1]), reverse=True):
            count = len(submission_ids)
            total_duplicate_records += count
            print(f"\nHash: {hash_value}")
            print(f"  重复次数: {count}")
            print(f"  涉及的submission_id:")
            for sid in submission_ids:
                print(f"    - {sid}")
        
        print("\n" + "-" * 60)
        print(f"重复记录总数: {total_duplicate_records} 条")
        print(f"去重后应保留: {len(duplicate_hashes)} 条（每个hash保留1条）")
        print(f"需要删除: {total_duplicate_records - len(duplicate_hashes)} 条")
    else:
        print("\n✓ 没有发现重复的original_image_hash！")
    
    return duplicate_hashes

if __name__ == '__main__':
    check_duplicate_hash()
