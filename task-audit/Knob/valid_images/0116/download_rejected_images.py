#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载审核结果为拒绝（review_result=0）的记录对应的original_image图片
"""

import csv
import json
import requests
from pathlib import Path
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import argparse
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 路径配置
BASE_DIR = Path(__file__).parent
CSV_FILE = BASE_DIR / "旋钮_交付.csv"
REVIEW_RESULT_CSV = BASE_DIR / "result" / "review_results.csv"
OUTPUT_DIR = BASE_DIR / "images"
DEFAULT_MAX_WORKERS = 10

def get_file_extension_from_url(url):
    """从URL中提取文件扩展名"""
    parsed = urlparse(url)
    filename = parsed.path.split('/')[-1]
    
    if '.' in filename:
        ext = '.' + filename.rsplit('.', 1)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            return ext
    
    # 默认返回.jpg
    return '.jpg'

def download_image(url, save_path):
    """下载单张图片"""
    try:
        # 如果文件已存在，跳过下载
        if save_path.exists():
            return {'status': 'exists', 'path': save_path}
        
        # 禁用SSL验证（仅用于测试环境）
        response = requests.get(url, timeout=30, stream=True, verify=False)
        response.raise_for_status()
        
        # 保存图片
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return {'status': 'success', 'path': save_path}
    except Exception as e:
        return {'status': 'error', 'error': str(e), 'url': url}

def load_rejected_submission_ids():
    """加载拒绝的submission_id列表"""
    rejected_ids = []
    if not REVIEW_RESULT_CSV.exists():
        return rejected_ids
    
    with open(REVIEW_RESULT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['review_result'] == '0':
                rejected_ids.append(row['submission_id'])
    
    return rejected_ids

def load_data_mapping():
    """加载CSV数据，建立submission_id到original_image的映射"""
    mapping = {}
    if not CSV_FILE.exists():
        return mapping
    
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # 解析JSON
                data_submission = json.loads(row['data_submission'])
                original_image = data_submission.get('data', {}).get('original_image', '')
                
                if original_image:
                    mapping[row['submission_id']] = original_image
            except Exception as e:
                print(f"解析错误 {row.get('submission_id', 'unknown')}: {e}")
                continue
    
    return mapping

def download_single_image(submission_id, image_url):
    """下载单张图片"""
    ext = get_file_extension_from_url(image_url)
    filename = f"{submission_id}_original{ext}"
    save_path = OUTPUT_DIR / filename
    
    result = download_image(image_url, save_path)
    result['submission_id'] = submission_id
    return result

def main():
    parser = argparse.ArgumentParser(description='下载拒绝记录的图片')
    parser.add_argument(
        '--workers',
        type=int,
        default=DEFAULT_MAX_WORKERS,
        help=f'并行下载线程数（默认: {DEFAULT_MAX_WORKERS}）'
    )
    args = parser.parse_args()
    max_workers = args.workers
    
    print("=" * 60)
    print("下载拒绝记录的original_image图片")
    print("=" * 60)
    print(f"CSV文件: {CSV_FILE}")
    print(f"审核结果文件: {REVIEW_RESULT_CSV}")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"并行线程数: {max_workers}")
    
    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 加载拒绝的submission_id列表
    print(f"\n读取审核结果...")
    rejected_ids = load_rejected_submission_ids()
    print(f"找到 {len(rejected_ids)} 条拒绝记录")
    
    if len(rejected_ids) == 0:
        print("没有需要下载的图片！")
        return
    
    # 加载数据映射
    print(f"\n读取CSV数据...")
    data_mapping = load_data_mapping()
    print(f"加载了 {len(data_mapping)} 条数据记录")
    
    # 准备下载任务
    tasks = []
    for submission_id in rejected_ids:
        if submission_id in data_mapping:
            tasks.append((submission_id, data_mapping[submission_id]))
        else:
            print(f"警告: submission_id {submission_id} 在CSV中未找到")
    
    print(f"\n准备下载 {len(tasks)} 张图片")
    
    if len(tasks) == 0:
        print("没有可下载的图片！")
        return
    
    # 并行下载
    print(f"\n开始下载...")
    success_count = 0
    exists_count = 0
    error_count = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_task = {
            executor.submit(download_single_image, submission_id, image_url): (submission_id, image_url)
            for submission_id, image_url in tasks
        }
        
        with tqdm(total=len(tasks), desc="  下载进度") as pbar:
            for future in as_completed(future_to_task):
                try:
                    result = future.result()
                    if result.get('status') == 'success':
                        success_count += 1
                    elif result.get('status') == 'exists':
                        exists_count += 1
                    else:
                        error_count += 1
                        if 'error' in result:
                            print(f"\n错误 [{result.get('submission_id', 'unknown')}]: {result['error']}")
                except Exception as e:
                    error_count += 1
                    print(f"\n处理失败: {e}")
                
                pbar.update(1)
    
    # 统计结果
    print("\n" + "=" * 60)
    print("下载完成!")
    print("=" * 60)
    print(f"成功下载: {success_count} 张")
    print(f"已存在跳过: {exists_count} 张")
    print(f"失败: {error_count} 张")
    print(f"总计: {success_count + exists_count + error_count} 张")
    print(f"\n图片保存在: {OUTPUT_DIR}")

if __name__ == '__main__':
    main()
