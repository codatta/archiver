#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
共享工具函数
"""

import os
import hashlib
from pathlib import Path
from urllib.parse import urlparse


def get_file_extension_from_url(url):
    """
    从URL中提取文件扩展名
    
    Args:
        url: 图片URL
    
    Returns:
        str: 文件扩展名（如 .jpg, .jpeg, .png），如果无法提取则返回 .jpg
    """
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)
    
    # 提取扩展名
    if filename and '.' in filename:
        ext = os.path.splitext(filename)[1].lower()
        # 确保扩展名有效
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            return ext
    
    # 默认返回 .jpg
    return '.jpg'


def get_image_hash(image_path):
    """
    计算图片的MD5哈希值
    
    Args:
        image_path: 图片路径
    
    Returns:
        str: 图片的MD5哈希值，如果文件不存在或读取失败返回None
    """
    if not os.path.exists(image_path):
        return None
    
    try:
        hash_md5 = hashlib.md5()
        with open(image_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"计算哈希失败 {image_path}: {e}")
        return None


def get_base_dir():
    """
    获取项目根目录
    
    Returns:
        Path: 项目根目录路径
    """
    return Path(__file__).parent.parent

