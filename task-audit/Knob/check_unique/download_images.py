#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片下载脚本
负责从CSV文件中读取图片URL并下载到本地
"""

import os
import sys
import argparse
import pandas as pd
import requests
from pathlib import Path
from tqdm import tqdm
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import get_file_extension_from_url, get_base_dir

# 配置路径
BASE_DIR = get_base_dir()
CSV_FILE = BASE_DIR / "raw_data" / "adm_binance_kitchen_images_0106.csv"
FRONT_DIR = BASE_DIR / "download_images" / "front"
IMAGE_MAPPING_FILE = BASE_DIR / "download_images" / "front" / "image_mapping.csv"

# 创建必要的目录
FRONT_DIR.mkdir(parents=True, exist_ok=True)

# 默认配置参数
DEFAULT_MAX_WORKERS = 50  # 默认并行下载线程数


def download_image(url, save_path, max_retries=3):
    """
    下载图片到指定路径
    
    Args:
        url: 图片URL
        save_path: 保存路径
        max_retries: 最大重试次数
    
    Returns:
        bool: 是否下载成功
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)  # 等待1秒后重试
                continue
            print(f"下载失败 {url}: {e}")
            return False
    
    return False


def download_single_image(row_data):
    """
    下载单张图片的任务函数（用于线程池）
    
    Args:
        row_data: 包含 (idx, row) 的元组
    
    Returns:
        dict: 图片映射信息
    """
    idx, row = row_data
    url = row['front_image']
    submission_id = row['submission_id']
    result = row['result']
    
    # 生成保存路径：{submission_id}_{result}_front.{ext}
    file_ext = get_file_extension_from_url(url)
    save_path = FRONT_DIR / f"{submission_id}_{result}_front{file_ext}"
    
    # 如果文件已存在，跳过下载
    if save_path.exists():
        return {
            'submission_id': submission_id,
            'image_path': str(save_path),
            'front_image': url,
            'side_image': row['side_image'],
            'result': result,
            'original_index': idx,
            'status': 'exists'
        }
    
    # 下载图片
    if download_image(url, save_path):
        return {
            'submission_id': submission_id,
            'image_path': str(save_path),
            'front_image': url,
            'side_image': row['side_image'],
            'result': result,
            'original_index': idx,
            'status': 'downloaded'
        }
    else:
        return {
            'submission_id': submission_id,
            'image_path': None,
            'front_image': url,
            'side_image': row['side_image'],
            'result': result,
            'original_index': idx,
            'status': 'failed'
        }


def main():
    """
    主函数：下载所有front_image图片
    """
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='图片下载工具')
    parser.add_argument(
        '--workers',
        type=int,
        default=DEFAULT_MAX_WORKERS,
        help=f'并行下载线程数（默认: {DEFAULT_MAX_WORKERS}）'
    )
    args = parser.parse_args()
    
    max_workers = args.workers
    
    print("=" * 60)
    print("图片下载工具")
    print("=" * 60)
    
    # 1. 读取CSV文件
    print(f"\n[1/2] 读取CSV文件: {CSV_FILE}")
    try:
        df = pd.read_csv(CSV_FILE)
        print(f"  总记录数: {len(df)}")
    except Exception as e:
        print(f"  错误: 无法读取CSV文件 - {e}")
        sys.exit(1)
    
    # 2. 下载所有图片（并行下载）
    print(f"\n[2/2] 下载图片到: {FRONT_DIR}")
    print(f"  并行线程数: {max_workers}")
    print("  正在下载图片...")
    
    image_mapping = []  # 存储图片映射信息
    failed_downloads = []
    
    # 准备任务列表
    tasks = [(idx, row) for idx, row in df.iterrows()]
    
    # 使用线程池并行下载
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_task = {executor.submit(download_single_image, task): task for task in tasks}
        
        # 使用tqdm显示进度
        with tqdm(total=len(tasks), desc="  下载进度") as pbar:
            for future in as_completed(future_to_task):
                try:
                    result = future.result()
                    image_mapping.append(result)
                    
                    if result['status'] == 'failed':
                        failed_downloads.append(result['submission_id'])
                except Exception as e:
                    task = future_to_task[future]
                    idx, row = task
                    print(f"\n  任务异常 {row['submission_id']}: {e}")
                    image_mapping.append({
                        'submission_id': row['submission_id'],
                        'image_path': None,
                        'front_image': row['front_image'],
                        'side_image': row['side_image'],
                        'result': row['result'],
                        'original_index': idx,
                        'status': 'failed'
                    })
                    failed_downloads.append(row['submission_id'])
                
                pbar.update(1)
    
    # 保存图片映射信息
    mapping_df = pd.DataFrame(image_mapping)
    mapping_df.to_csv(IMAGE_MAPPING_FILE, index=False)
    
    # 统计信息
    success_count = len([x for x in image_mapping if x['status'] in ['downloaded', 'exists']])
    exists_count = len([x for x in image_mapping if x['status'] == 'exists'])
    downloaded_count = len([x for x in image_mapping if x['status'] == 'downloaded'])
    
    print(f"\n  成功: {success_count} 张")
    print(f"    - 新下载: {downloaded_count} 张")
    print(f"    - 已存在: {exists_count} 张")
    if failed_downloads:
        print(f"  下载失败: {len(failed_downloads)} 张")
    
    print(f"\n  图片映射文件已保存: {IMAGE_MAPPING_FILE}")
    
    print("\n" + "=" * 60)
    print("下载完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

