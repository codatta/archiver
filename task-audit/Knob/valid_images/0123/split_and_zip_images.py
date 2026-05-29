#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片拆分压缩脚本：
1. 扫描images_0123目录下的所有图片文件
2. 按文件大小智能分组，分成10个部分
3. 为每个组创建压缩包
4. 提供详细的统计信息和进度显示
"""

import os
import zipfile
from pathlib import Path
from tqdm import tqdm
import argparse
from datetime import datetime
import math

# 路径配置
BASE_DIR = Path(__file__).parent
IMAGES_DIR = BASE_DIR / "images_0123"
OUTPUT_DIR = BASE_DIR / "zip_archives"
DEFAULT_PARTS = 10

def get_image_files():
    """获取所有图片文件及其大小"""
    if not IMAGES_DIR.exists():
        print(f"错误: 图片目录不存在 {IMAGES_DIR}")
        return []
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    image_files = []
    
    for file_path in IMAGES_DIR.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            file_size = file_path.stat().st_size
            image_files.append({
                'path': file_path,
                'name': file_path.name,
                'size': file_size
            })
    
    # 按文件大小排序（从大到小），便于后续均匀分配
    image_files.sort(key=lambda x: x['size'], reverse=True)
    
    return image_files

def split_files_by_size(files, num_parts):
    """按文件大小智能分组，尽量保持每组大小均匀"""
    if not files:
        return []
    
    # 初始化每个组
    groups = [{'files': [], 'total_size': 0} for _ in range(num_parts)]
    
    # 贪心算法：将每个文件分配到当前总大小最小的组
    for file_info in files:
        # 找到总大小最小的组
        min_group = min(groups, key=lambda g: g['total_size'])
        min_group['files'].append(file_info)
        min_group['total_size'] += file_info['size']
    
    return groups

def format_size(size_bytes):
    """格式化文件大小"""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def create_zip_archive(group_files, zip_path, part_num, total_parts):
    """创建单个zip压缩包"""
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        with tqdm(
            total=len(group_files), 
            desc=f"压缩第{part_num}/{total_parts}部分", 
            unit="张"
        ) as pbar:
            for file_info in group_files:
                # 添加文件到zip，使用相对路径
                arcname = file_info['name']
                zipf.write(file_info['path'], arcname)
                pbar.update(1)
    
    return zip_path.stat().st_size

def main():
    parser = argparse.ArgumentParser(description='图片拆分压缩脚本')
    parser.add_argument(
        '--parts', 
        type=int, 
        default=DEFAULT_PARTS,
        help=f'分割部分数 (默认: {DEFAULT_PARTS})'
    )
    parser.add_argument(
        '--prefix', 
        type=str, 
        default='images_batch',
        help='zip文件名前缀 (默认: images_batch)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        help='输出目录 (默认: ./zip_archives)'
    )
    
    args = parser.parse_args()
    
    # 设置输出目录
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = OUTPUT_DIR
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("图片拆分压缩脚本")
    print("=" * 70)
    print(f"源目录: {IMAGES_DIR}")
    print(f"输出目录: {output_dir}")
    print(f"分割部分: {args.parts}")
    print(f"文件前缀: {args.prefix}")
    
    # 1. 扫描图片文件
    print(f"\n步骤1: 扫描图片文件...")
    image_files = get_image_files()
    
    if not image_files:
        print("未找到图片文件")
        return
    
    total_files = len(image_files)
    total_size = sum(f['size'] for f in image_files)
    
    print(f"找到 {total_files} 个图片文件")
    print(f"总大小: {format_size(total_size)}")
    
    # 2. 智能分组
    print(f"\n步骤2: 分组文件...")
    groups = split_files_by_size(image_files, args.parts)
    
    # 显示分组信息
    print(f"分组详情:")
    for i, group in enumerate(groups, 1):
        avg_size = group['total_size'] / len(group['files']) if group['files'] else 0
        print(f"  第{i}组: {len(group['files'])} 个文件, "
              f"总大小: {format_size(group['total_size'])}, "
              f"平均: {format_size(avg_size)}")
    
    # 3. 创建压缩包
    print(f"\n步骤3: 创建压缩包...")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_files = []
    compressed_sizes = []
    
    for i, group in enumerate(groups, 1):
        if not group['files']:  # 跳过空组
            continue
            
        zip_filename = f"{args.prefix}_{i:02d}_of_{args.parts:02d}_{timestamp}.zip"
        zip_path = output_dir / zip_filename
        
        # 创建压缩包
        compressed_size = create_zip_archive(group['files'], zip_path, i, args.parts)
        
        zip_files.append({
            'path': zip_path,
            'filename': zip_filename,
            'file_count': len(group['files']),
            'original_size': group['total_size'],
            'compressed_size': compressed_size
        })
        compressed_sizes.append(compressed_size)
    
    # 4. 输出统计信息
    print(f"\n" + "=" * 70)
    print("压缩完成!")
    print("=" * 70)
    
    total_compressed_size = sum(compressed_sizes)
    compression_ratio = (1 - total_compressed_size / total_size) * 100 if total_size > 0 else 0
    
    print(f"压缩统计:")
    print(f"  原始大小: {format_size(total_size)}")
    print(f"  压缩后大小: {format_size(total_compressed_size)}")
    print(f"  压缩率: {compression_ratio:.1f}%")
    print(f"  创建文件数: {len(zip_files)}")
    
    print(f"\n详细信息:")
    for zip_info in zip_files:
        file_compression = (1 - zip_info['compressed_size'] / zip_info['original_size']) * 100
        print(f"  {zip_info['filename']}:")
        print(f"    文件数: {zip_info['file_count']} 张")
        print(f"    原始: {format_size(zip_info['original_size'])} → "
              f"压缩: {format_size(zip_info['compressed_size'])} "
              f"({file_compression:.1f}%)")
    
    print(f"\n输出目录: {output_dir}")
    
    # 5. 生成批处理脚本（可选）
    create_extract_script(output_dir, zip_files)

def create_extract_script(output_dir, zip_files):
    """创建解压脚本"""
    script_content = """#!/bin/bash
# 自动解压脚本
# 使用方法: bash extract_all.sh [target_directory]

TARGET_DIR=${1:-"extracted_images"}
mkdir -p "$TARGET_DIR"

echo "开始解压所有压缩包到: $TARGET_DIR"
echo "========================================"

"""
    
    for zip_info in zip_files:
        script_content += f'echo "解压: {zip_info["filename"]}"\n'
        script_content += f'unzip -q "{zip_info["filename"]}" -d "$TARGET_DIR"\n'
        script_content += f'echo "完成: {zip_info["file_count"]} 个文件"\n\n'
    
    script_content += """echo "========================================"
echo "所有文件解压完成!"
echo "解压目录: $TARGET_DIR"
echo "总文件数: $(find "$TARGET_DIR" -type f | wc -l)"
"""
    
    script_path = output_dir / "extract_all.sh"
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    # 设置执行权限
    script_path.chmod(0o755)
    print(f"已创建解压脚本: {script_path}")

if __name__ == '__main__':
    main()