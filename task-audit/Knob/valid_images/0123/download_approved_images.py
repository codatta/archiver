#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从审核结果中下载通过的图片：
1. 读取review_results.csv，找出审核通过的记录（review_result == 1）
2. 从旋钮_交付.csv中获取对应的图片URL
3. 下载original_image和annotated_image
4. 图片命名为: submission_id + "_original" 和 submission_id + "_annotated"
5. 下载的图片存储到images_0123目录下
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
REVIEW_RESULT_CSV = BASE_DIR / "result" / "review_results.csv"
CSV_FILE = BASE_DIR / "旋钮_交付.csv"
OUTPUT_DIR = BASE_DIR / "images_0123"
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / f"download_approved_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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

def load_approved_submission_ids():
    """加载审核通过的submission_id列表"""
    approved_ids = set()
    if not REVIEW_RESULT_CSV.exists():
        logger.warning(f"审核结果文件不存在: {REVIEW_RESULT_CSV}")
        return approved_ids
    
    with open(REVIEW_RESULT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('review_result') == '1':
                approved_ids.add(row['submission_id'])
    
    logger.info(f"从审核结果中读取到 {len(approved_ids)} 个通过的记录")
    return approved_ids

def load_csv_data():
    """加载CSV数据，返回以submission_id为key的字典"""
    data_dict = {}
    if not CSV_FILE.exists():
        logger.error(f"CSV文件不存在: {CSV_FILE}")
        return data_dict
    
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data_dict[row['submission_id']] = row['data_submission']
    
    logger.info(f"从CSV文件中读取到 {len(data_dict)} 条记录")
    return data_dict

def download_single_row(submission_id, data_submission_str):
    """处理单条记录，下载两张图片"""
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
    parser = argparse.ArgumentParser(description='下载审核通过的图片')
    parser.add_argument(
        '--workers',
        type=int,
        default=DEFAULT_MAX_WORKERS,
        help=f'并行下载线程数（默认: {DEFAULT_MAX_WORKERS}）'
    )
    args = parser.parse_args()
    max_workers = args.workers
    
    print("=" * 60)
    print("下载审核通过的图片")
    print("=" * 60)
    print(f"审核结果文件: {REVIEW_RESULT_CSV}")
    print(f"CSV文件: {CSV_FILE}")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"日志文件: {LOG_FILE}")
    print(f"并行线程数: {max_workers}")
    
    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 加载审核通过的submission_id
    print(f"\n读取审核结果...")
    approved_ids = load_approved_submission_ids()
    
    if len(approved_ids) == 0:
        print("没有找到审核通过的记录！")
        logger.warning("没有找到审核通过的记录")
        return
    
    print(f"找到 {len(approved_ids)} 个审核通过的记录")
    
    # 加载CSV数据
    print(f"\n读取CSV文件...")
    csv_data = load_csv_data()
    
    if len(csv_data) == 0:
        print("CSV文件中没有数据！")
        logger.error("CSV文件中没有数据")
        return
    
    # 找出需要下载的记录（审核通过且在CSV中存在）
    tasks = []
    missing_ids = []
    for submission_id in approved_ids:
        if submission_id in csv_data:
            tasks.append((submission_id, csv_data[submission_id]))
        else:
            missing_ids.append(submission_id)
            logger.warning(f"submission_id {submission_id} 在CSV文件中不存在")
    
    if missing_ids:
        print(f"\n警告: 有 {len(missing_ids)} 个审核通过的submission_id在CSV文件中找不到")
        logger.warning(f"有 {len(missing_ids)} 个审核通过的submission_id在CSV文件中找不到")
    
    if len(tasks) == 0:
        print("没有需要下载的记录！")
        logger.warning("没有需要下载的记录")
        return
    
    print(f"找到 {len(tasks)} 条需要下载的记录")
    print(f"预计下载 {len(tasks) * 2} 张图片（每条记录2张）")
    
    # 并行下载
    print(f"\n开始下载...")
    logger.info(f"开始下载，共 {len(tasks)} 条记录，预计下载 {len(tasks) * 2} 张图片")
    
    success_count = 0
    exists_count = 0
    error_count = 0
    error_records = []  # 记录失败的下载
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_task = {executor.submit(download_single_row, submission_id, data_submission): (submission_id, data_submission) 
                          for submission_id, data_submission in tasks}
        
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
