#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级图片下载脚本：
1. 支持失败重试机制
2. 支持断点续传（检查已存在的文件）
3. 支持从失败点继续下载
4. 多线程并发下载
5. 详细的进度跟踪和日志记录
6. 状态保存和恢复
7. 文件完整性验证
"""

import csv
import json
import requests
import os
import time
import pickle
from pathlib import Path
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import argparse
import urllib3
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Set
import hashlib

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 路径配置
BASE_DIR = Path(__file__).parent
CSV_FILE = BASE_DIR / "旋钮_交付_0123.csv"
OUTPUT_DIR = BASE_DIR / "images_final_delivery"
LOG_DIR = BASE_DIR / "logs"
STATE_DIR = BASE_DIR / "download_state"
LOG_FILE = LOG_DIR / f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
STATE_FILE = STATE_DIR / "download_state.pkl"
DEFAULT_MAX_WORKERS = 20
DEFAULT_MAX_RETRIES = 3
DEFAULT_TIMEOUT = 60
MIN_FILE_SIZE = 100  # 最小文件大小（字节），用于检查文件完整性

# 创建必要的目录
for dir_path in [OUTPUT_DIR, LOG_DIR, STATE_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

@dataclass
class DownloadTask:
    """下载任务类"""
    submission_id: str
    image_type: str  # 'original' or 'annotated'
    url: str
    filename: str
    file_path: Path
    status: str = 'pending'  # 'pending', 'downloading', 'completed', 'failed', 'skipped'
    retries: int = 0
    error_message: str = ''
    file_size: int = 0
    download_time: float = 0.0
    
    def __hash__(self):
        return hash((self.submission_id, self.image_type))

@dataclass 
class DownloadState:
    """下载状态类"""
    tasks: Dict[str, DownloadTask]
    completed_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    total_count: int = 0
    start_time: float = 0.0
    last_save_time: float = 0.0

class ImageDownloader:
    def __init__(self, max_workers=DEFAULT_MAX_WORKERS, max_retries=DEFAULT_MAX_RETRIES, timeout=DEFAULT_TIMEOUT):
        self.max_workers = max_workers
        self.max_retries = max_retries
        self.timeout = timeout
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(LOG_FILE, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # 初始化状态
        self.state = self.load_state()
    
    def get_file_extension_from_url(self, url: str) -> str:
        """从URL中提取文件扩展名"""
        parsed = urlparse(url)
        filename = parsed.path.split('/')[-1]
        
        if '.' in filename:
            ext = '.' + filename.rsplit('.', 1)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                return ext
        
        return '.jpg'
    
    def load_tasks_from_csv(self) -> Dict[str, DownloadTask]:
        """从CSV文件加载下载任务"""
        tasks = {}
        
        if not CSV_FILE.exists():
            self.logger.error(f"CSV文件不存在: {CSV_FILE}")
            return tasks
        
        self.logger.info(f"读取CSV文件: {CSV_FILE}")
        
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
                        ext = self.get_file_extension_from_url(original_url)
                        filename = f"{submission_id}_original{ext}"
                        file_path = OUTPUT_DIR / filename
                        task_key = f"{submission_id}_original"
                        
                        tasks[task_key] = DownloadTask(
                            submission_id=submission_id,
                            image_type='original',
                            url=original_url,
                            filename=filename,
                            file_path=file_path
                        )
                    
                    # 处理annotated_image
                    if annotated_url:
                        ext = self.get_file_extension_from_url(annotated_url)
                        filename = f"{submission_id}_annotated{ext}"
                        file_path = OUTPUT_DIR / filename
                        task_key = f"{submission_id}_annotated"
                        
                        tasks[task_key] = DownloadTask(
                            submission_id=submission_id,
                            image_type='annotated',
                            url=annotated_url,
                            filename=filename,
                            file_path=file_path
                        )
                        
                except json.JSONDecodeError as e:
                    self.logger.error(f"JSON解析失败 - submission_id: {submission_id}, error: {e}")
        
        self.logger.info(f"从CSV中加载了 {len(tasks)} 个下载任务")
        return tasks
    
    def check_file_exists_and_valid(self, file_path: Path) -> bool:
        """检查文件是否存在且有效"""
        if not file_path.exists():
            return False
        
        # 检查文件大小
        if file_path.stat().st_size < MIN_FILE_SIZE:
            self.logger.warning(f"文件太小，可能损坏: {file_path.name}")
            return False
        
        return True
    
    def load_state(self) -> DownloadState:
        """加载下载状态"""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, 'rb') as f:
                    state_dict = pickle.load(f)
                    # 重建DownloadState对象
                    tasks = {k: DownloadTask(**v) if isinstance(v, dict) else v 
                            for k, v in state_dict.get('tasks', {}).items()}
                    state = DownloadState(
                        tasks=tasks,
                        completed_count=state_dict.get('completed_count', 0),
                        failed_count=state_dict.get('failed_count', 0),
                        skipped_count=state_dict.get('skipped_count', 0),
                        total_count=state_dict.get('total_count', 0),
                        start_time=state_dict.get('start_time', 0.0),
                        last_save_time=state_dict.get('last_save_time', 0.0)
                    )
                    self.logger.info(f"加载了上次的下载状态: {len(tasks)} 个任务")
                    return state
            except Exception as e:
                self.logger.warning(f"无法加载状态文件: {e}")
        
        return DownloadState(tasks={})
    
    def save_state(self):
        """保存下载状态"""
        try:
            # 转换为可序列化的字典
            state_dict = {
                'tasks': {k: asdict(v) for k, v in self.state.tasks.items()},
                'completed_count': self.state.completed_count,
                'failed_count': self.state.failed_count,
                'skipped_count': self.state.skipped_count,
                'total_count': self.state.total_count,
                'start_time': self.state.start_time,
                'last_save_time': time.time()
            }
            
            with open(STATE_FILE, 'wb') as f:
                pickle.dump(state_dict, f)
            
            self.state.last_save_time = time.time()
        except Exception as e:
            self.logger.error(f"保存状态失败: {e}")
    
    def download_single_image(self, task: DownloadTask) -> DownloadTask:
        """下载单张图片"""
        # 检查文件是否已存在且有效
        if self.check_file_exists_and_valid(task.file_path):
            task.status = 'skipped'
            task.file_size = task.file_path.stat().st_size
            self.logger.debug(f"文件已存在，跳过: {task.filename}")
            return task
        
        task.status = 'downloading'
        start_time = time.time()
        
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.get(
                    task.url, 
                    timeout=self.timeout, 
                    stream=True, 
                    verify=False,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                )
                response.raise_for_status()
                
                # 获取文件大小
                content_length = response.headers.get('content-length')
                if content_length:
                    expected_size = int(content_length)
                else:
                    expected_size = 0
                
                # 下载文件
                with open(task.file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # 验证文件
                if not self.check_file_exists_and_valid(task.file_path):
                    raise Exception("下载的文件无效或损坏")
                
                # 检查文件大小（如果服务器提供了大小信息）
                actual_size = task.file_path.stat().st_size
                if expected_size > 0 and abs(actual_size - expected_size) > 100:
                    self.logger.warning(f"文件大小不匹配: {task.filename}, 预期: {expected_size}, 实际: {actual_size}")
                
                task.status = 'completed'
                task.file_size = actual_size
                task.download_time = time.time() - start_time
                task.retries = attempt
                
                self.logger.info(f"下载成功: {task.filename} ({actual_size} bytes, {task.download_time:.2f}s)")
                return task
                
            except Exception as e:
                task.retries = attempt + 1
                task.error_message = str(e)
                
                if attempt < self.max_retries:
                    wait_time = min(2 ** attempt, 10)  # 指数退避，最大10秒
                    self.logger.warning(f"下载失败，{wait_time}秒后重试 ({attempt+1}/{self.max_retries}): {task.filename} - {e}")
                    time.sleep(wait_time)
                else:
                    task.status = 'failed'
                    self.logger.error(f"下载最终失败: {task.filename} - {e}")
                    
                    # 删除可能的损坏文件
                    if task.file_path.exists():
                        try:
                            task.file_path.unlink()
                        except Exception:
                            pass
        
        return task
    
    def download_all(self, resume=True, force_restart=False):
        """下载所有图片"""
        # 加载任务
        csv_tasks = self.load_tasks_from_csv()
        
        if not csv_tasks:
            self.logger.error("没有找到下载任务")
            return
        
        # 初始化或更新状态
        if force_restart or not self.state.tasks:
            self.logger.info("开始新的下载任务")
            self.state.tasks = csv_tasks
            self.state.completed_count = 0
            self.state.failed_count = 0
            self.state.skipped_count = 0
            self.state.total_count = len(csv_tasks)
            self.state.start_time = time.time()
        else:
            # 合并新任务和已有任务
            for key, task in csv_tasks.items():
                if key not in self.state.tasks:
                    self.state.tasks[key] = task
            self.state.total_count = len(self.state.tasks)
            
            if resume:
                self.logger.info(f"恢复上次的下载任务: {len(self.state.tasks)} 个任务")
        
        # 筛选需要下载的任务
        pending_tasks = []
        for task in self.state.tasks.values():
            if task.status in ['pending', 'failed'] or (task.status == 'downloading'):
                # 重置正在下载的任务状态
                if task.status == 'downloading':
                    task.status = 'pending'
                pending_tasks.append(task)
            elif task.status == 'completed' and not self.check_file_exists_and_valid(task.file_path):
                # 文件已标记为完成但实际不存在或损坏，重新下载
                task.status = 'pending'
                pending_tasks.append(task)
        
        if not pending_tasks:
            self.logger.info("所有任务已完成")
            return
        
        self.logger.info(f"开始下载 {len(pending_tasks)} 个待处理任务")
        
        # 并行下载
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {executor.submit(self.download_single_image, task): task for task in pending_tasks}
            
            with tqdm(total=len(pending_tasks), desc="下载进度", unit="张") as pbar:
                for future in as_completed(future_to_task):
                    task = future.result()
                    
                    # 更新统计
                    if task.status == 'completed':
                        self.state.completed_count += 1
                    elif task.status == 'failed':
                        self.state.failed_count += 1
                    elif task.status == 'skipped':
                        self.state.skipped_count += 1
                    
                    # 更新进度条描述
                    pbar.set_postfix({
                        'completed': self.state.completed_count,
                        'failed': self.state.failed_count,
                        'skipped': self.state.skipped_count
                    })
                    pbar.update(1)
                    
                    # 定期保存状态
                    if time.time() - self.state.last_save_time > 30:  # 每30秒保存一次
                        self.save_state()
        
        # 最终保存状态
        self.save_state()
        
        # 输出最终统计
        self.print_final_statistics()
    
    def print_final_statistics(self):
        """输出最终统计信息"""
        total_time = time.time() - self.state.start_time if self.state.start_time > 0 else 0
        
        # 统计各种状态的任务
        completed = sum(1 for task in self.state.tasks.values() if task.status == 'completed')
        failed = sum(1 for task in self.state.tasks.values() if task.status == 'failed')
        skipped = sum(1 for task in self.state.tasks.values() if task.status == 'skipped')
        
        print(f"\n" + "=" * 70)
        print("下载完成!")
        print("=" * 70)
        print(f"总任务数: {self.state.total_count}")
        print(f"成功下载: {completed} 张")
        print(f"跳过文件: {skipped} 张 (已存在)")
        print(f"下载失败: {failed} 张")
        print(f"总耗时: {total_time:.1f} 秒")
        
        if completed > 0:
            avg_time = sum(task.download_time for task in self.state.tasks.values() 
                          if task.status == 'completed') / completed
            print(f"平均下载时间: {avg_time:.2f} 秒/张")
        
        # 输出失败任务详情
        failed_tasks = [task for task in self.state.tasks.values() if task.status == 'failed']
        if failed_tasks:
            print(f"\n失败任务详情:")
            for task in failed_tasks[:10]:  # 只显示前10个
                print(f"  - {task.filename}: {task.error_message}")
            if len(failed_tasks) > 10:
                print(f"  ... 还有 {len(failed_tasks) - 10} 个失败任务")
        
        print(f"\n输出目录: {OUTPUT_DIR}")
        print(f"日志文件: {LOG_FILE}")
        
        self.logger.info(f"下载任务完成 - 成功: {completed}, 跳过: {skipped}, 失败: {failed}")
    
    def retry_failed(self):
        """重试失败的任务"""
        failed_tasks = [task for task in self.state.tasks.values() if task.status == 'failed']
        
        if not failed_tasks:
            self.logger.info("没有失败的任务需要重试")
            return
        
        self.logger.info(f"重试 {len(failed_tasks)} 个失败的任务")
        
        # 重置失败任务的状态
        for task in failed_tasks:
            task.status = 'pending'
            task.retries = 0
            task.error_message = ''
        
        # 重新下载
        self.download_all(resume=True)
    
    def clean_state(self):
        """清理状态文件"""
        if STATE_FILE.exists():
            STATE_FILE.unlink()
            self.logger.info("已清理状态文件")

def main():
    parser = argparse.ArgumentParser(description='高级图片下载脚本')
    parser.add_argument('--workers', type=int, default=DEFAULT_MAX_WORKERS,
                       help=f'并行下载线程数 (默认: {DEFAULT_MAX_WORKERS})')
    parser.add_argument('--retries', type=int, default=DEFAULT_MAX_RETRIES,
                       help=f'最大重试次数 (默认: {DEFAULT_MAX_RETRIES})')
    parser.add_argument('--timeout', type=int, default=DEFAULT_TIMEOUT,
                       help=f'下载超时时间/秒 (默认: {DEFAULT_TIMEOUT})')
    parser.add_argument('--resume', action='store_true', default=True,
                       help='恢复上次下载 (默认开启)')
    parser.add_argument('--restart', action='store_true',
                       help='强制重新开始下载')
    parser.add_argument('--retry-failed', action='store_true',
                       help='只重试失败的任务')
    parser.add_argument('--clean', action='store_true',
                       help='清理状态文件')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("高级图片下载脚本")
    print("=" * 70)
    print(f"CSV文件: {CSV_FILE}")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"并行线程: {args.workers}")
    print(f"最大重试: {args.retries}")
    print(f"超时时间: {args.timeout}秒")
    print(f"断点续传: {'是' if args.resume and not args.restart else '否'}")
    
    downloader = ImageDownloader(
        max_workers=args.workers,
        max_retries=args.retries,
        timeout=args.timeout
    )
    
    if args.clean:
        downloader.clean_state()
        return
    
    if args.retry_failed:
        downloader.retry_failed()
    else:
        downloader.download_all(resume=args.resume, force_restart=args.restart)

if __name__ == '__main__':
    main()