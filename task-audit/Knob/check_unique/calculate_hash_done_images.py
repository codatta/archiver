#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
计算done_images目录下所有图片的哈希值
支持子目录扫描
"""

import sys
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from utils import get_image_hash, get_base_dir

# 配置路径
BASE_DIR = get_base_dir()
DONE_IMAGES_DIR = BASE_DIR / "done_images"
OUTPUT_CSV = BASE_DIR / "check_unique" / "files" / "done_images.csv"

# 创建输出目录
OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)


def scan_images_recursive(directory):
    """
    递归扫描目录下的所有图片文件
    
    Args:
        directory: 要扫描的目录
    
    Returns:
        list: 图片文件路径列表
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    image_files = []
    
    for ext in image_extensions:
        # 扫描所有子目录
        image_files.extend(directory.rglob(f"*{ext}"))
        image_files.extend(directory.rglob(f"*{ext.upper()}"))
    
    return sorted(image_files)




def main():
    """
    主函数：计算done_images目录下所有图片的哈希值
    """
    print("=" * 60)
    print("计算done_images目录图片哈希值")
    print("=" * 60)
    
    # 1. 扫描所有图片文件
    print(f"\n[1/2] 扫描图片目录: {DONE_IMAGES_DIR}")
    if not DONE_IMAGES_DIR.exists():
        print(f"  错误: 目录不存在 - {DONE_IMAGES_DIR}")
        sys.exit(1)
    
    image_files = scan_images_recursive(DONE_IMAGES_DIR)
    print(f"  找到图片文件: {len(image_files)} 个")
    
    if len(image_files) == 0:
        print("  警告: 未找到任何图片文件")
        sys.exit(0)
    
    # 2. 计算哈希值
    print(f"\n[2/2] 计算图片哈希值...")
    
    hash_data = []
    failed_files = []
    
    for image_path in tqdm(image_files, desc="  计算进度"):
        image_hash = get_image_hash(image_path)
        
        if image_hash:
            # 从路径提取信息
            relative_path = image_path.relative_to(DONE_IMAGES_DIR)
            
            hash_data.append({
                'relative_path': str(relative_path),
                'hash': image_hash,
                'file_size': image_path.stat().st_size
            })
        else:
            failed_files.append(str(image_path))
    
    # 保存结果
    if hash_data:
        df = pd.DataFrame(hash_data)
        df.to_csv(OUTPUT_CSV, index=False)
        print(f"\n  成功计算: {len(hash_data)} 个文件")
        print(f"  结果已保存: {OUTPUT_CSV}")
    else:
        print("\n  警告: 没有成功计算哈希的文件")
    
    if failed_files:
        print(f"  失败文件数: {len(failed_files)}")
        for f in failed_files[:5]:  # 只显示前5个
            print(f"    - {f}")
        if len(failed_files) > 5:
            print(f"    ... 还有 {len(failed_files) - 5} 个失败文件")
    
    print("\n" + "=" * 60)
    print("计算完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

