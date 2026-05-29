#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从旋钮_交付_最终.csv下载图片：
1. 下载original_image和annotated_image
2. 图片命名为: submission_id + "_original" 和 submission_id + "_annotated"
3. 下载的图片存储到images_0109目录下
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
import logging
from datetime import datetime

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 路径配置
BASE_DIR = Path(__file__).parent
CSV_FILE = BASE_DIR / "旋钮_交付_最终.csv"
OUTPUT_DIR = BASE_DIR / "images_0109"
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / f"download_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
DEFAULT_MAX_WORKERS = 10

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
    
    # 默认返回.jpg
    return '.jpg'

def download_image(url, save_path, submission_id, image_type):
    """下载单张图片"""
    # 下载前检查文件是否已存在
    if save_path.exists():
        logger.debug(f"文件已存在，跳过: {save_path.name} (submission_id: {submission_id}, type: {image_type})")
        return {'status': 'exists', 'path': save_path}
    
    try:
        # 禁用SSL验证（仅用于测试环境）
        response = requests.get(url, timeout=30, stream=True, verify=False)
        response.raise_for_status()
        
        # 保存图片
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.debug(f"下载成功: {save_path.name} (submission_id: {submission_id}, type: {image_type})")
        return {'status': 'success', 'path': save_path}
    except Exception as e:
        error_msg = f"下载失败 - submission_id: {submission_id}, type: {image_type}, url: {url}, error: {str(e)}"
        logger.error(error_msg)
        return {'status': 'error', 'error': str(e), 'url': url}

def download_single_row(row_data):
    """处理单行数据，下载两张图片"""
    submission_id = row_data['submission_id']
    data_submission_str = row_data['data_submission']
    
    results = []
    
    try:
        # 解析JSON
        data_submission = json.loads(data_submission_str)
        
        # 从data字段中获取图片URL
        data = data_submission.get('data', {})
        original_image_url = data.get('original_image', '')
        annotated_image_url = data.get('annotated_image', '')
        
        # 下载original_image
        if original_image_url:
            ext = get_file_extension_from_url(original_image_url)
            original_filename = f"{submission_id}_original{ext}"
            original_path = OUTPUT_DIR / original_filename
            
            result = download_image(original_image_url, original_path, submission_id, 'original')
            result['submission_id'] = submission_id
            result['type'] = 'original'
            results.append(result)
        else:
            logger.warning(f"缺少original_image URL - submission_id: {submission_id}")
            results.append({
                'submission_id': submission_id,
                'status': 'error',
                'type': 'original',
                'error': '缺少original_image URL'
            })
        
        # 下载annotated_image
        if annotated_image_url:
            ext = get_file_extension_from_url(annotated_image_url)
            annotated_filename = f"{submission_id}_annotated{ext}"
            annotated_path = OUTPUT_DIR / annotated_filename
            
            result = download_image(annotated_image_url, annotated_path, submission_id, 'annotated')
            result['submission_id'] = submission_id
            result['type'] = 'annotated'
            results.append(result)
        else:
            logger.warning(f"缺少annotated_image URL - submission_id: {submission_id}")
            results.append({
                'submission_id': submission_id,
                'status': 'error',
                'type': 'annotated',
                'error': '缺少annotated_image URL'
            })
        
    except Exception as e:
        error_msg = f"解析JSON失败 - submission_id: {submission_id}, error: {str(e)}"
        logger.error(error_msg)
        results.append({
            'submission_id': submission_id,
            'status': 'error',
            'error': f'解析失败: {str(e)}'
        })
    
    return results

def main():
    parser = argparse.ArgumentParser(description='下载最终交付图片')
    parser.add_argument(
        '--workers',
        type=int,
        default=DEFAULT_MAX_WORKERS,
        help=f'并行下载线程数（默认: {DEFAULT_MAX_WORKERS}）'
    )
    args = parser.parse_args()
    max_workers = args.workers
    
    print("=" * 60)
    print("下载最终交付图片")
    print("=" * 60)
    print(f"CSV文件: {CSV_FILE}")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"日志文件: {LOG_FILE}")
    print(f"并行线程数: {max_workers}")
    
    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"开始下载任务 - CSV文件: {CSV_FILE}, 输出目录: {OUTPUT_DIR}")
    
    # 读取CSV文件
    print(f"\n读取CSV文件...")
    tasks = []
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tasks.append(row)
    
    print(f"找到 {len(tasks)} 条记录")
    print(f"预计下载 {len(tasks) * 2} 张图片（每条记录2张）")
    
    # 并行下载
    print(f"\n开始下载...")
    logger.info(f"开始下载，共 {len(tasks)} 条记录，预计下载 {len(tasks) * 2} 张图片")
    
    success_count = 0
    exists_count = 0
    error_count = 0
    error_records = []  # 记录失败的下载
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_task = {executor.submit(download_single_row, task): task for task in tasks}
        
        with tqdm(total=len(tasks), desc="  下载进度") as pbar:
            for future in as_completed(future_to_task):
                try:
                    results = future.result()
                    for result in results:
                        if result.get('status') == 'success':
                            success_count += 1
                        elif result.get('status') == 'exists':
                            exists_count += 1
                        else:
                            error_count += 1
                            error_records.append(result)
                            if 'error' in result:
                                error_msg = f"错误 [{result.get('submission_id', 'unknown')}][{result.get('type', 'unknown')}]: {result['error']}"
                                print(f"\n{error_msg}")
                except Exception as e:
                    error_count += 1
                    error_msg = f"处理失败: {e}"
                    print(f"\n{error_msg}")
                    logger.error(error_msg)
                
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
    
    # 记录统计信息到日志
    logger.info(f"下载完成统计 - 成功: {success_count}, 已存在: {exists_count}, 失败: {error_count}, 总计: {success_count + exists_count + error_count}")
    
    # 如果有失败记录，输出详细摘要
    if error_records:
        print("\n" + "=" * 60)
        print("失败记录摘要")
        print("=" * 60)
        print(f"共有 {len(error_records)} 条失败记录，详细信息已保存到日志文件: {LOG_FILE}")
        
        # 按submission_id分组统计
        error_by_submission = {}
        for record in error_records:
            sid = record.get('submission_id', 'unknown')
            if sid not in error_by_submission:
                error_by_submission[sid] = []
            error_by_submission[sid].append(record)
        
        print(f"\n涉及 {len(error_by_submission)} 个submission_id:")
        for sid, records in sorted(error_by_submission.items()):
            types = [r.get('type', 'unknown') for r in records]
            errors = [r.get('error', 'unknown error') for r in records]
            print(f"  - {sid}: {', '.join(types)} - {', '.join(errors[:2])}")  # 只显示前2个错误
        
        logger.info(f"失败记录详情已保存到: {LOG_FILE}")
    else:
        print("\n✓ 所有图片下载成功，没有失败记录！")
        logger.info("所有图片下载成功，没有失败记录")

if __name__ == '__main__':
    main()
