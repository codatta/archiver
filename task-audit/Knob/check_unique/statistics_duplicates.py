#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计图片重复情况
1. 统计front目录下图片的重复情况
2. 统计去重后的front目录下图片和done_images目录下图片的重复情况
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
OUTPUT_REPORT = FILES_DIR / "duplicate_statistics.txt"


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


def analyze_front_duplicates(front_df):
    """
    分析front目录下的重复情况
    
    Args:
        front_df: front目录的哈希数据
    
    Returns:
        dict: 统计结果
    """
    print("\n  分析front目录重复情况...")
    
    # 统计哈希值重复情况
    hash_counts = front_df['hash'].value_counts()
    duplicate_hashes = hash_counts[hash_counts > 1]
    
    total_files = len(front_df)
    unique_hashes = len(hash_counts)
    duplicate_groups = len(duplicate_hashes)
    duplicate_files = duplicate_hashes.sum() - duplicate_groups  # 重复的文件数（不包括每组保留的一个）
    
    # 获取重复详情
    duplicate_details = []
    for hash_val, count in duplicate_hashes.items():
        duplicate_group = front_df[front_df['hash'] == hash_val]
        duplicate_details.append({
            'hash': hash_val,
            'count': count,
            'files': duplicate_group[['filename', 'submission_id', 'result']].to_dict('records')
        })
    
    return {
        'total_files': total_files,
        'unique_hashes': unique_hashes,
        'duplicate_groups': duplicate_groups,
        'duplicate_files': duplicate_files,
        'duplicate_details': duplicate_details
    }


def analyze_cross_duplicates(front_df, done_images_df):
    """
    分析front目录（去重后）和done_images目录的重复情况
    
    Args:
        front_df: front目录的哈希数据（已去重）
        done_images_df: done_images目录的哈希数据
    
    Returns:
        dict: 统计结果
    """
    print("\n  分析front和done_images目录的交叉重复情况...")
    
    # 对front目录去重（保留每个hash的第一条记录）
    front_deduplicated = front_df.drop_duplicates(subset=['hash'], keep='first')
    
    # 找出在两个目录中都存在的hash
    front_hashes = set(front_deduplicated['hash'])
    done_images_hashes = set(done_images_df['hash'])
    common_hashes = front_hashes & done_images_hashes
    
    # 获取详细信息
    cross_duplicate_details = []
    for hash_val in common_hashes:
        front_files = front_deduplicated[front_deduplicated['hash'] == hash_val]
        done_files = done_images_df[done_images_df['hash'] == hash_val]
        
        cross_duplicate_details.append({
            'hash': hash_val,
            'front_files': front_files[['filename', 'submission_id', 'result']].to_dict('records'),
            'done_images_files': done_files[['relative_path']].to_dict('records')
        })
    
    return {
        'front_unique_hashes': len(front_hashes),
        'done_images_unique_hashes': len(done_images_hashes),
        'common_hashes': len(common_hashes),
        'cross_duplicate_details': cross_duplicate_details
    }


def generate_report(front_stats, cross_stats):
    """
    生成统计报告
    
    Args:
        front_stats: front目录重复统计
        cross_stats: 交叉重复统计
    """
    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("图片重复情况统计报告")
    report_lines.append("=" * 60)
    report_lines.append(f"统计时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    
    # Front目录重复情况
    report_lines.append("=" * 60)
    report_lines.append("1. Front目录重复情况")
    report_lines.append("=" * 60)
    report_lines.append(f"总文件数: {front_stats['total_files']}")
    report_lines.append(f"唯一哈希数: {front_stats['unique_hashes']}")
    report_lines.append(f"重复组数: {front_stats['duplicate_groups']}")
    report_lines.append(f"重复文件数: {front_stats['duplicate_files']}")
    report_lines.append(f"去重后文件数: {front_stats['unique_hashes']}")
    
    if front_stats['duplicate_groups'] > 0:
        report_lines.append("")
        report_lines.append("重复详情:")
        for detail in front_stats['duplicate_details'][:10]:  # 只显示前10组
            report_lines.append(f"\n  哈希值: {detail['hash']}")
            report_lines.append(f"  重复数量: {detail['count']}")
            report_lines.append("  文件列表:")
            for file_info in detail['files']:
                report_lines.append(f"    - {file_info['filename']} (submission_id={file_info['submission_id']}, result={file_info['result']})")
        
        if len(front_stats['duplicate_details']) > 10:
            report_lines.append(f"\n  ... 还有 {len(front_stats['duplicate_details']) - 10} 组重复未显示")
    
    # 交叉重复情况
    report_lines.append("")
    report_lines.append("=" * 60)
    report_lines.append("2. Front目录（去重后）与Done_images目录的重复情况")
    report_lines.append("=" * 60)
    report_lines.append(f"Front目录唯一哈希数: {cross_stats['front_unique_hashes']}")
    report_lines.append(f"Done_images目录唯一哈希数: {cross_stats['done_images_unique_hashes']}")
    report_lines.append(f"共同哈希数: {cross_stats['common_hashes']}")
    
    if cross_stats['common_hashes'] > 0:
        report_lines.append("")
        report_lines.append("交叉重复详情:")
        for detail in cross_stats['cross_duplicate_details'][:10]:  # 只显示前10组
            report_lines.append(f"\n  哈希值: {detail['hash']}")
            report_lines.append("  Front目录文件:")
            for file_info in detail['front_files']:
                report_lines.append(f"    - {file_info['filename']} (submission_id={file_info['submission_id']}, result={file_info['result']})")
            report_lines.append("  Done_images目录文件:")
            for file_info in detail['done_images_files']:
                report_lines.append(f"    - {file_info['relative_path']}")
        
        if len(cross_stats['cross_duplicate_details']) > 10:
            report_lines.append(f"\n  ... 还有 {len(cross_stats['cross_duplicate_details']) - 10} 组交叉重复未显示")
    
    report_lines.append("")
    report_lines.append("=" * 60)
    
    return "\n".join(report_lines)


def main():
    """
    主函数：统计图片重复情况
    """
    print("=" * 60)
    print("图片重复情况统计")
    print("=" * 60)
    
    # 1. 加载数据
    print(f"\n[1/3] 加载哈希数据...")
    front_df = load_hash_data(FRONT_CSV, "front")
    done_images_df = load_hash_data(DONE_IMAGES_CSV, "done_images")
    
    if front_df is None or done_images_df is None:
        sys.exit(1)
    
    # 2. 分析front目录重复情况
    print(f"\n[2/3] 分析重复情况...")
    front_stats = analyze_front_duplicates(front_df)
    
    # 3. 分析交叉重复情况
    cross_stats = analyze_cross_duplicates(front_df, done_images_df)
    
    # 4. 生成报告
    print(f"\n[3/3] 生成统计报告...")
    report_content = generate_report(front_stats, cross_stats)
    
    # 保存报告
    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"  报告已保存: {OUTPUT_REPORT}")
    
    # 打印摘要
    print("\n" + "=" * 60)
    print("统计摘要")
    print("=" * 60)
    print(f"Front目录:")
    print(f"  - 总文件数: {front_stats['total_files']}")
    print(f"  - 唯一哈希数: {front_stats['unique_hashes']}")
    print(f"  - 重复组数: {front_stats['duplicate_groups']}")
    print(f"  - 重复文件数: {front_stats['duplicate_files']}")
    print(f"\n交叉重复:")
    print(f"  - Front唯一哈希数: {cross_stats['front_unique_hashes']}")
    print(f"  - Done_images唯一哈希数: {cross_stats['done_images_unique_hashes']}")
    print(f"  - 共同哈希数: {cross_stats['common_hashes']}")
    print("\n" + "=" * 60)
    print("统计完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

