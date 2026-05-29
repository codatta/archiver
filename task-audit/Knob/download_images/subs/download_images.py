#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 images.csv 下载图片到 jpgs 目录
"""

import requests
from pathlib import Path
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import argparse
import urllib3
import logging
import datetime

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 路径配置
BASE_DIR = Path(__file__).parent
CSV_FILE = BASE_DIR / "images.csv"
OUTPUT_DIR = BASE_DIR / "jpgs"
LOG_DIR = BASE_DIR / "logs"
DEFAULT_MAX_WORKERS = 50

# 配置日志
LOG_DIR.mkdir(parents=True, exist_ok=True)
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
log_file_path = LOG_DIR / f"download_log_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path, encoding='utf-8'),
        logging.StreamHandler()
    ]
)


def get_filename_from_url(url):
    """从URL中提取文件名"""
    parsed = urlparse(url)
    filename = parsed.path.split('/')[-1]
    if not filename:
        # 如果无法从URL提取，使用URL的hash作为文件名
        import hashlib
        filename = hashlib.md5(url.encode()).hexdigest() + '.jpg'
    return filename


def download_image(url, save_path):
    """下载单张图片"""
    try:
        # 如果文件已存在，跳过下载
        if save_path.exists():
            logging.debug(f"文件已存在，跳过: {save_path}")
            return {'status': 'exists', 'path': save_path, 'url': url}
        
        # 禁用SSL验证（仅用于测试环境）
        response = requests.get(url, timeout=30, stream=True, verify=False)
        response.raise_for_status()
        
        # 保存图片
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return {'status': 'success', 'path': save_path, 'url': url}
    except requests.exceptions.RequestException as req_err:
        return {'status': 'error', 'error': f'请求失败: {req_err}', 'url': url}
    except Exception as e:
        return {'status': 'error', 'error': str(e), 'url': url}


def load_urls():
    """从CSV文件加载URL列表"""
    urls = []
    if not CSV_FILE.exists():
        logging.error(f"CSV文件不存在: {CSV_FILE}")
        return urls
    
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            url = line.strip()
            if url and url.startswith('http'):
                urls.append(url)
    
    return urls


def main():
    parser = argparse.ArgumentParser(description='从 images.csv 下载图片')
    parser.add_argument(
        '--workers',
        type=int,
        default=DEFAULT_MAX_WORKERS,
        help=f'并行下载线程数（默认: {DEFAULT_MAX_WORKERS}）'
    )
    args = parser.parse_args()
    max_workers = args.workers
    
    logging.info("=" * 60)
    logging.info("下载图片")
    logging.info("=" * 60)
    logging.info(f"CSV文件: {CSV_FILE}")
    logging.info(f"输出目录: {OUTPUT_DIR}")
    logging.info(f"日志文件: {log_file_path}")
    logging.info(f"并行线程数: {max_workers}")
    
    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 加载URL列表
    logging.info(f"\n读取CSV文件...")
    urls = load_urls()
    
    if not urls:
        logging.error("没有找到有效的URL")
        return
    
    logging.info(f"找到 {len(urls)} 个图片URL")
    
    # 准备下载任务
    tasks = []
    for url in urls:
        filename = get_filename_from_url(url)
        save_path = OUTPUT_DIR / filename
        tasks.append({'url': url, 'save_path': save_path})
    
    # 并行下载
    logging.info(f"\n开始下载...")
    success_count = 0
    exists_count = 0
    error_count = 0
    error_records = []
    
    def download_task(task):
        return download_image(task['url'], task['save_path'])
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_task = {executor.submit(download_task, task): task for task in tasks}
        
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
                        error_records.append(result)
                        logging.error(f"下载失败 - URL: {result.get('url', 'N/A')} - 错误: {result.get('error', '未知错误')}")
                except Exception as e:
                    error_count += 1
                    logging.error(f"处理任务失败: {e}")
                
                pbar.update(1)
    
    # 统计结果
    logging.info("\n" + "=" * 60)
    logging.info("下载完成!")
    logging.info("=" * 60)
    logging.info(f"成功下载: {success_count} 张")
    logging.info(f"已存在跳过: {exists_count} 张")
    logging.info(f"失败: {error_count} 张")
    logging.info(f"总计: {success_count + exists_count + error_count} 张")
    logging.info(f"\n图片保存在: {OUTPUT_DIR}")
    
    if error_records:
        logging.warning("\n" + "=" * 60)
        logging.warning("发现未成功下载的图片:")
        logging.warning("=" * 60)
        for rec in error_records:
            logging.warning(f"URL: {rec.get('url', 'N/A')} - 错误: {rec.get('error', '未知错误')}")
        logging.warning(f"总计 {len(error_records)} 张图片下载失败。")
    else:
        logging.info("\n所有图片均已成功下载或已存在。")


if __name__ == '__main__':
    main()
