#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成干净的数据
1. 对front目录下的图片去重
2. 排除与done_images目录下图片重复的
3. 保存到CSV文件
"""

import sys
import pandas as pd
from pathlib import Path
import time
from utils import get_base_dir

# 配置路径
BASE_DIR = get_base_dir()
FILES_DIR = BASE_DIR / "check_unique" / "files"
FRONT_CSV = FILES_DIR / "front.csv"
DONE_IMAGES_CSV = FILES_DIR / "done_images.csv"
OUTPUT_CSV = FILES_DIR / "clean_data.csv"


def load_hash_data(csv_path, source_name):
    """
    加载哈希数据
    
    Args:
        csv_path: CSV文件路径
        source_name: 数据源名称（用于错误提示）
    
    Returns:
        DataFrame: 包含hash数据的DataFrame
    """
    if not csv_path.exists():
        print(f"  错误: {source_name}的哈希数据文件不存在: {csv_path}")
        print(f"  提示: 请先运行 calculate_hash_{source_name}.py")
        return None
    
    try:
        df = pd.read_csv(csv_path)
        print(f"  加载 {source_name}: {len(df)} 条记录")
        return df
    except Exception as e:
        print(f"  错误: 无法读取 {source_name}的哈希数据 - {e}")
        return None


def deduplicate_front(front_df):
    """
    对front目录的图片进行去重
    保留策略：优先保留result=5的，如果result相同则保留第一个
    
    Args:
        front_df: front目录的哈希数据
    
    Returns:
        DataFrame: 去重后的数据
    """
    print("\n  对front目录图片去重...")
    
    # 按hash分组，对每组应用保留策略
    def keep_best(group):
        """保留策略：优先保留result=5的，如果result相同则保留第一个"""
        if len(group) == 1:
            return group.index[0]
        
        # 按result降序排序，result相同时保持原顺序
        sorted_group = group.sort_values('result', ascending=False)
        return sorted_group.index[0]
    
    # 对每个重复组应用保留策略
    keep_indices = []
    hash_counts = front_df['hash'].value_counts()
    duplicate_hashes = hash_counts[hash_counts > 1].index.tolist()
    
    for hash_val in duplicate_hashes:
        duplicate_group = front_df[front_df['hash'] == hash_val]
        keep_idx = keep_best(duplicate_group)
        keep_indices.append(keep_idx)
    
    # 获取所有需要保留的记录（包括唯一的和去重后保留的）
    unique_indices = front_df[~front_df['hash'].isin(duplicate_hashes)].index.tolist()
    all_keep_indices = unique_indices + keep_indices
    
    # 创建去重后的DataFrame
    deduplicated_df = front_df.loc[all_keep_indices].copy()
    
    print(f"    原始记录数: {len(front_df)}")
    print(f"    去重后记录数: {len(deduplicated_df)}")
    print(f"    删除重复记录数: {len(front_df) - len(deduplicated_df)}")
    
    return deduplicated_df


def remove_cross_duplicates(front_deduplicated_df, done_images_df):
    """
    移除与done_images目录重复的图片
    
    Args:
        front_deduplicated_df: front目录去重后的数据
        done_images_df: done_images目录的数据
    
    Returns:
        DataFrame: 移除交叉重复后的干净数据
    """
    print("\n  移除与done_images目录的重复...")
    
    # 获取两个目录的hash集合
    front_hashes = set(front_deduplicated_df['hash'])
    done_images_hashes = set(done_images_df['hash'])
    common_hashes = front_hashes & done_images_hashes
    
    # 移除共同hash的记录
    clean_df = front_deduplicated_df[~front_deduplicated_df['hash'].isin(common_hashes)].copy()
    
    print(f"    front去重后记录数: {len(front_deduplicated_df)}")
    print(f"    与done_images重复的hash数: {len(common_hashes)}")
    print(f"    最终干净记录数: {len(clean_df)}")
    print(f"    移除记录数: {len(front_deduplicated_df) - len(clean_df)}")
    
    return clean_df


def main():
    """
    主函数：生成干净的数据
    """
    print("=" * 60)
    print("生成干净数据")
    print("=" * 60)
    
    # 1. 加载数据
    print(f"\n[1/3] 加载哈希数据...")
    front_df = load_hash_data(FRONT_CSV, "front")
    done_images_df = load_hash_data(DONE_IMAGES_CSV, "done_images")
    
    if front_df is None or done_images_df is None:
        sys.exit(1)
    
    # 2. 对front目录去重
    print(f"\n[2/3] 处理数据...")
    front_deduplicated_df = deduplicate_front(front_df)
    
    # 3. 移除与done_images的重复
    clean_df = remove_cross_duplicates(front_deduplicated_df, done_images_df)
    
    # 4. 保存结果
    print(f"\n[3/3] 保存结果...")
    
    # 选择要保存的列（根据front.csv的列结构）
    output_columns = ['submission_id', 'result', 'filename', 'filepath', 'hash', 'file_size']
    # 确保所有列都存在
    available_columns = [col for col in output_columns if col in clean_df.columns]
    clean_output_df = clean_df[available_columns].copy()
    
    # 按submission_id排序
    if 'submission_id' in clean_output_df.columns:
        clean_output_df = clean_output_df.sort_values('submission_id')
    
    # 保存到CSV
    clean_output_df.to_csv(OUTPUT_CSV, index=False)
    
    print(f"  干净数据已保存: {OUTPUT_CSV}")
    print(f"  总记录数: {len(clean_output_df)}")
    
    # 打印统计信息
    print("\n" + "=" * 60)
    print("处理摘要")
    print("=" * 60)
    print(f"Front目录原始记录数: {len(front_df)}")
    print(f"Front目录去重后记录数: {len(front_deduplicated_df)}")
    print(f"与done_images重复的记录数: {len(front_deduplicated_df) - len(clean_df)}")
    print(f"最终干净记录数: {len(clean_df)}")
    print("\n" + "=" * 60)
    print("处理完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

