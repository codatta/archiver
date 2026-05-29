#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
计算front目录下所有图片的哈希值
"""

import sys
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from utils import get_image_hash, get_base_dir

# 配置路径
BASE_DIR = get_base_dir()
FRONT_DIR = BASE_DIR / "download_images" / "front"
OUTPUT_CSV = BASE_DIR / "check_unique" / "files" / "front.csv"

# 创建输出目录
OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)


def main():
    """
    主函数：计算front目录下所有图片的哈希值
    """
    print("=" * 60)
    print("计算front目录图片哈希值")
    print("=" * 60)
    
    # 1. 获取所有图片文件
    print(f"\n[1/2] 扫描图片目录: {FRONT_DIR}")
    if not FRONT_DIR.exists():
        print(f"  错误: 目录不存在 - {FRONT_DIR}")
        sys.exit(1)
    
    # 支持的图片格式
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    
    image_files = []
    for ext in image_extensions:
        image_files.extend(FRONT_DIR.glob(f"*{ext}"))
        image_files.extend(FRONT_DIR.glob(f"*{ext.upper()}"))
    
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
            # 从文件名提取submission_id和result
            filename = image_path.stem  # 不包含扩展名
            # 文件名格式: {submission_id}_{result}_front
            parts = filename.rsplit('_', 2)  # 从右边分割，最多分割2次
            if len(parts) >= 3 and parts[2] == 'front':
                submission_id = parts[0]
                result = parts[1] if parts[1].isdigit() else None
            elif len(parts) >= 2:
                submission_id = parts[0]
                result = parts[1] if parts[1].isdigit() else None
            else:
                submission_id = filename
                result = None
            
            hash_data.append({
                'submission_id': submission_id,
                'result': result,
                'filename': image_path.name,
                'filepath': str(image_path),
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

