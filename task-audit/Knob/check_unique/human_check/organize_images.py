#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将图片按每30张分组到不同文件夹
"""

import shutil
from pathlib import Path

# 配置路径
SOURCE_DIR = Path(__file__).parent / "result" / "images"
IMAGES_PER_FOLDER = 30

def main():
    print("=" * 60)
    print("组织图片到文件夹")
    print("=" * 60)
    
    if not SOURCE_DIR.exists():
        print(f"错误: 源目录不存在: {SOURCE_DIR}")
        return
    
    # 获取所有图片文件
    image_files = sorted([f for f in SOURCE_DIR.iterdir() if f.is_file()])
    total_images = len(image_files)
    
    print(f"源目录: {SOURCE_DIR}")
    print(f"图片总数: {total_images}")
    print(f"每个文件夹: {IMAGES_PER_FOLDER} 张")
    
    if total_images == 0:
        print("没有图片需要组织")
        return
    
    # 计算需要的文件夹数量
    num_folders = (total_images + IMAGES_PER_FOLDER - 1) // IMAGES_PER_FOLDER
    print(f"需要创建: {num_folders} 个文件夹\n")
    
    # 组织图片
    moved_count = 0
    
    for folder_idx in range(num_folders):
        # 创建文件夹
        folder_name = f"images_{folder_idx + 1:02d}"
        folder_path = SOURCE_DIR.parent / folder_name
        folder_path.mkdir(exist_ok=True)
        
        # 计算这个文件夹应该包含的图片范围
        start_idx = folder_idx * IMAGES_PER_FOLDER
        end_idx = min(start_idx + IMAGES_PER_FOLDER, total_images)
        folder_images = image_files[start_idx:end_idx]
        
        # 移动图片到文件夹
        for image_file in folder_images:
            try:
                target_path = folder_path / image_file.name
                if target_path.exists():
                    print(f"跳过 (已存在): {image_file.name} -> {folder_name}/")
                else:
                    shutil.move(str(image_file), str(target_path))
                    moved_count += 1
            except Exception as e:
                print(f"错误: 移动失败 {image_file.name}: {e}")
        
        print(f"文件夹 {folder_name}: {len(folder_images)} 张图片")
    
    # 输出统计信息
    print("\n" + "=" * 60)
    print("组织完成!")
    print("=" * 60)
    print(f"成功移动: {moved_count} 张图片")
    print(f"创建了 {num_folders} 个文件夹")
    print(f"每个文件夹最多包含 {IMAGES_PER_FOLDER} 张图片")

if __name__ == '__main__':
    main()

