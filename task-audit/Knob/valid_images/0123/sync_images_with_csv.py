#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步图片目录与CSV文件：
1. 以CSV文件为准，检查应该存在的图片
2. 删除目录中多余的图片文件
3. 下载缺失的图片文件
4. 确保CSV和images目录完全一致
"""

import csv
import json
import requests
import os
from pathlib import Path
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import argparse
import urllib3
import logging
from datetime import datetime

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 路径配置
BASE_DIR = Path(__file__).parent
CSV_FILE = BASE_DIR / "旋钮_交付_去重_20260124_180749.csv"
IMAGES_DIR = BASE_DIR / "images_0123"
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / f"sync_images_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
DEFAULT_MAX_WORKERS = 50

# 配置日志
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_file_extension_from_url(url):
    """从URL中提取文件扩展名"""
    parsed = urlparse(url)
    filename = parsed.path.split('/')[-1]
    
    if '.' in filename:
        ext = '.' + filename.rsplit('.', 1)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            return ext
    
    return '.jpg'

def get_expected_images_from_csv():
    """从CSV文件中获取应该存在的图片文件信息"""
    expected_images = {}  # {filename: {submission_id, url, type}}
    
    print(f"读取CSV文件: {CSV_FILE}")
    
    if not CSV_FILE.exists():
        print(f"错误: CSV文件不存在于 {CSV_FILE}")
        return expected_images
    
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            submission_id = row['submission_id']
            
            try:
                data_submission = json.loads(row['data_submission'])
                data = data_submission.get('data', {})
                
                original_url = data.get('original_image', '')
                annotated_url = data.get('annotated_image', '')
                
                # 处理original_image
                if original_url:
                    ext = get_file_extension_from_url(original_url)
                    filename = f"{submission_id}_original{ext}"
                    expected_images[filename] = {
                        'submission_id': submission_id,
                        'url': original_url,
                        'type': 'original'
                    }
                
                # 处理annotated_image
                if annotated_url:
                    ext = get_file_extension_from_url(annotated_url)
                    filename = f"{submission_id}_annotated{ext}"
                    expected_images[filename] = {
                        'submission_id': submission_id,
                        'url': annotated_url,
                        'type': 'annotated'
                    }
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败 - submission_id: {submission_id}, error: {e}")
    
    print(f"从CSV中解析出 {len(expected_images)} 个应该存在的图片文件")
    return expected_images

def get_existing_images():
    """获取目录中实际存在的图片文件"""
    existing_images = set()
    
    if not IMAGES_DIR.exists():
        print(f"图片目录不存在: {IMAGES_DIR}")
        return existing_images
    
    for file_path in IMAGES_DIR.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            existing_images.add(file_path.name)
    
    print(f"图片目录中存在 {len(existing_images)} 个图片文件")
    return existing_images

def download_image(filename, image_info):
    """下载单张图片"""
    url = image_info['url']
    save_path = IMAGES_DIR / filename
    submission_id = image_info['submission_id']
    image_type = image_info['type']
    
    try:
        response = requests.get(url, timeout=30, stream=True, verify=False)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"下载成功: {filename}")
        return {'status': 'success', 'filename': filename}
    except Exception as e:
        error_msg = f"下载失败: {filename} - {str(e)}"
        logger.error(error_msg)
        return {'status': 'error', 'filename': filename, 'error': str(e)}

def main():
    parser = argparse.ArgumentParser(description='同步图片目录与CSV文件')
    parser.add_argument(
        '--workers',
        type=int,
        default=DEFAULT_MAX_WORKERS,
        help=f'并行下载线程数（默认: {DEFAULT_MAX_WORKERS}）'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='只分析不执行实际操作'
    )
    args = parser.parse_args()
    
    print("=" * 70)
    print("同步图片目录与CSV文件")
    print("=" * 70)
    print(f"CSV文件: {CSV_FILE}")
    print(f"图片目录: {IMAGES_DIR}")
    print(f"并行线程数: {args.workers}")
    if args.dry_run:
        print("模式: 预览模式（不执行实际操作）")
    
    # 创建图片目录
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. 获取应该存在的图片
    print(f"\n步骤1: 分析CSV文件...")
    expected_images = get_expected_images_from_csv()
    expected_filenames = set(expected_images.keys())
    
    # 2. 获取实际存在的图片
    print(f"\n步骤2: 扫描图片目录...")
    existing_images = get_existing_images()
    
    # 3. 分析差异
    print(f"\n步骤3: 分析差异...")
    
    # 需要删除的文件（目录中有，但CSV中没有）
    files_to_delete = existing_images - expected_filenames
    
    # 需要下载的文件（CSV中有，但目录中没有）
    files_to_download = expected_filenames - existing_images
    
    # 已经存在且正确的文件
    files_correct = existing_images & expected_filenames
    
    print(f"分析结果:")
    print(f"  应该存在的图片: {len(expected_filenames)} 个")
    print(f"  实际存在的图片: {len(existing_images)} 个")
    print(f"  正确存在的图片: {len(files_correct)} 个")
    print(f"  需要删除的图片: {len(files_to_delete)} 个")
    print(f"  需要下载的图片: {len(files_to_download)} 个")
    
    # 显示详细信息
    if files_to_delete:
        print(f"\n需要删除的文件 (显示前10个):")
        for i, filename in enumerate(sorted(files_to_delete)):
            if i >= 10:
                print(f"  ... 还有 {len(files_to_delete) - 10} 个文件")
                break
            print(f"  - {filename}")
    
    if files_to_download:
        print(f"\n需要下载的文件 (显示前10个):")
        for i, filename in enumerate(sorted(files_to_download)):
            if i >= 10:
                print(f"  ... 还有 {len(files_to_download) - 10} 个文件")
                break
            print(f"  - {filename}")
    
    if args.dry_run:
        print(f"\n预览模式完成，未执行实际操作。")
        return
    
    # 4. 删除多余文件
    if files_to_delete:
        print(f"\n步骤4: 删除多余文件...")
        deleted_count = 0
        for filename in files_to_delete:
            file_path = IMAGES_DIR / filename
            try:
                file_path.unlink()
                deleted_count += 1
                logger.info(f"删除文件: {filename}")
            except Exception as e:
                logger.error(f"删除失败: {filename} - {str(e)}")
        
        print(f"删除完成: {deleted_count}/{len(files_to_delete)} 个文件")
    else:
        print(f"\n步骤4: 无需删除文件")
    
    # 5. 下载缺失文件
    if files_to_download:
        print(f"\n步骤5: 下载缺失文件...")
        
        download_tasks = []
        for filename in files_to_download:
            if filename in expected_images:
                download_tasks.append((filename, expected_images[filename]))
        
        success_count = 0
        error_count = 0
        
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            future_to_task = {
                executor.submit(download_image, filename, image_info): (filename, image_info)
                for filename, image_info in download_tasks
            }
            
            with tqdm(total=len(download_tasks), desc="  下载进度") as pbar:
                for future in as_completed(future_to_task):
                    result = future.result()
                    if result['status'] == 'success':
                        success_count += 1
                    else:
                        error_count += 1
                        print(f"\n下载失败: {result['filename']}")
                    pbar.update(1)
        
        print(f"下载完成: {success_count}/{len(download_tasks)} 个文件")
        if error_count > 0:
            print(f"下载失败: {error_count} 个文件")
    else:
        print(f"\n步骤5: 无需下载文件")
    
    # 6. 最终验证
    print(f"\n步骤6: 最终验证...")
    final_existing = get_existing_images()
    final_correct = final_existing & expected_filenames
    final_missing = expected_filenames - final_existing
    final_extra = final_existing - expected_filenames
    
    print(f"\n" + "=" * 70)
    print("同步完成!")
    print("=" * 70)
    print(f"预期图片数: {len(expected_filenames)}")
    print(f"实际图片数: {len(final_existing)}")
    print(f"正确匹配数: {len(final_correct)}")
    print(f"仍然缺失: {len(final_missing)}")
    print(f"多余文件: {len(final_extra)}")
    
    if len(final_missing) == 0 and len(final_extra) == 0:
        print(f"\n🎉 同步完成！CSV文件与图片目录完全一致")
    else:
        print(f"\n⚠️  同步未完全成功")
        if final_missing:
            print(f"   仍缺失 {len(final_missing)} 个文件")
        if final_extra:
            print(f"   仍多余 {len(final_extra)} 个文件")
    
    logger.info(f"同步完成 - 预期: {len(expected_filenames)}, 实际: {len(final_existing)}, 匹配: {len(final_correct)}")

if __name__ == '__main__':
    main()