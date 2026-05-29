#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从旋钮_交付.csv中筛选审核通过的记录：
1. 从review_results.csv中获取所有审核通过的submission_id (review_result == 1)
2. 从旋钮_交付.csv中筛选对应的记录
3. 保存到新的交付结果文件中，格式和源文件一致
"""

import csv
from pathlib import Path
from datetime import datetime
import logging

# 路径配置
BASE_DIR = Path(__file__).parent
REVIEW_RESULT_CSV = BASE_DIR / "result" / "review_results.csv"
SOURCE_CSV = BASE_DIR / "旋钮_交付.csv"
OUTPUT_CSV = BASE_DIR / f"旋钮_交付_通过_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_approved_submission_ids():
    """从审核结果中加载通过的submission_id列表"""
    approved_ids = set()
    
    if not REVIEW_RESULT_CSV.exists():
        logger.error(f"审核结果文件不存在: {REVIEW_RESULT_CSV}")
        return approved_ids
    
    logger.info(f"读取审核结果文件: {REVIEW_RESULT_CSV}")
    
    with open(REVIEW_RESULT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('review_result') == '1':
                approved_ids.add(row['submission_id'])
    
    logger.info(f"找到 {len(approved_ids)} 个审核通过的记录")
    return approved_ids

def filter_approved_records():
    """筛选审核通过的记录"""
    
    # 加载审核通过的submission_id
    approved_ids = load_approved_submission_ids()
    
    if not approved_ids:
        logger.error("没有找到审核通过的记录")
        return
    
    if not SOURCE_CSV.exists():
        logger.error(f"源CSV文件不存在: {SOURCE_CSV}")
        return
    
    logger.info(f"读取源CSV文件: {SOURCE_CSV}")
    
    approved_records = []
    total_records = 0
    
    # 读取源CSV文件，筛选审核通过的记录
    with open(SOURCE_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        for row in reader:
            total_records += 1
            if row['submission_id'] in approved_ids:
                approved_records.append(row)
    
    logger.info(f"源文件总记录数: {total_records}")
    logger.info(f"筛选出审核通过的记录数: {len(approved_records)}")
    
    # 保存筛选结果到新文件
    logger.info(f"保存筛选结果到: {OUTPUT_CSV}")
    
    with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(approved_records)
    
    logger.info(f"完成！审核通过的 {len(approved_records)} 条记录已保存到: {OUTPUT_CSV}")
    
    # 统计信息
    print("\n" + "=" * 60)
    print("筛选完成统计")
    print("=" * 60)
    print(f"源文件: {SOURCE_CSV}")
    print(f"审核结果文件: {REVIEW_RESULT_CSV}")
    print(f"输出文件: {OUTPUT_CSV}")
    print(f"")
    print(f"源文件总记录数: {total_records}")
    print(f"审核通过记录数: {len(approved_ids)}")
    print(f"筛选出的记录数: {len(approved_records)}")
    print(f"筛选成功率: {len(approved_records)/len(approved_ids)*100:.1f}%")
    
    # 检查是否有审核通过但在源文件中找不到的记录
    found_ids = {record['submission_id'] for record in approved_records}
    missing_ids = approved_ids - found_ids
    
    if missing_ids:
        print(f"\n警告: 有 {len(missing_ids)} 个审核通过的submission_id在源文件中找不到:")
        for missing_id in sorted(missing_ids)[:10]:  # 只显示前10个
            print(f"  - {missing_id}")
        if len(missing_ids) > 10:
            print(f"  ... 还有 {len(missing_ids) - 10} 个")
    else:
        print("\n✓ 所有审核通过的记录都在源文件中找到了")

def main():
    print("=" * 60)
    print("筛选审核通过的交付记录")
    print("=" * 60)
    print(f"源文件: {SOURCE_CSV}")
    print(f"审核结果: {REVIEW_RESULT_CSV}")
    print(f"输出文件: {OUTPUT_CSV}")
    print("=" * 60)
    
    try:
        filter_approved_records()
    except Exception as e:
        logger.error(f"处理失败: {e}")
        print(f"\n❌ 处理失败: {e}")

if __name__ == '__main__':
    main()