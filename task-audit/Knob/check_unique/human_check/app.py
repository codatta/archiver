#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片审核Web应用
"""

import os
import sys
import pandas as pd
from flask import Flask, render_template, jsonify, request, send_from_directory
from pathlib import Path

# 添加父目录到路径以便导入utils
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import get_base_dir

# 配置路径
BASE_DIR = get_base_dir()
CLEAN_DATA_CSV = BASE_DIR / "check_unique" / "files" / "clean_data.csv"
RESULT_DIR = Path(__file__).parent / "result"
REVIEW_RESULT_CSV = RESULT_DIR / "review_results.csv"
FRONT_DIR = BASE_DIR / "download_images" / "front"

app = Flask(__name__)


def load_clean_data():
    """加载干净数据"""
    if not CLEAN_DATA_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(CLEAN_DATA_CSV)


def load_review_results():
    """加载审核结果"""
    if not REVIEW_RESULT_CSV.exists():
        return pd.DataFrame(columns=['submission_id', 'review_result', 'review_time'])
    return pd.read_csv(REVIEW_RESULT_CSV)


def get_unreviewed_images():
    """获取未审核的图片"""
    clean_df = load_clean_data()
    if len(clean_df) == 0:
        return pd.DataFrame()
    
    review_df = load_review_results()
    
    # 找出未审核的图片
    if len(review_df) > 0:
        reviewed_ids = set(review_df['submission_id'].astype(str))
        unreviewed_df = clean_df[~clean_df['submission_id'].astype(str).isin(reviewed_ids)]
    else:
        unreviewed_df = clean_df.copy()
    
    return unreviewed_df


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/api/get_image')
def get_image():
    """获取一张未审核的图片"""
    unreviewed_df = get_unreviewed_images()
    
    if len(unreviewed_df) == 0:
        return jsonify({
            'success': False,
            'message': '没有待审核的图片了！',
            'remaining': 0
        })
    
    # 获取第一张图片
    image_data = unreviewed_df.iloc[0].to_dict()
    
    # 检查文件大小，如果小于1MB则自动拒绝
    file_size = image_data.get('file_size', 0)
    if file_size < 1000000:  # 小于1MB
        submission_id = str(image_data['submission_id'])
        # 自动保存拒绝结果
        review_df = load_review_results()
        import time
        new_record = pd.DataFrame([{
            'submission_id': submission_id,
            'review_result': 0,  # 拒绝
            'review_time': time.strftime('%Y-%m-%d %H:%M:%S')
        }])
        
        if len(review_df) > 0:
            review_df = review_df[review_df['submission_id'].astype(str) != submission_id]
        
        review_df = pd.concat([review_df, new_record], ignore_index=True)
        REVIEW_RESULT_CSV.parent.mkdir(parents=True, exist_ok=True)
        review_df.to_csv(REVIEW_RESULT_CSV, index=False)
        
        # 递归获取下一张图片
        return get_image()
    
    # 转换为相对路径用于前端显示
    filepath = image_data['filepath']
    if os.path.exists(filepath):
        # 使用相对路径（从BASE_DIR开始）
        relative_path = os.path.relpath(filepath, BASE_DIR).replace('\\', '/')
    else:
        # 如果绝对路径不存在，尝试使用filename
        relative_path = f"download_images/front/{image_data['filename']}"
    
    return jsonify({
        'success': True,
        'submission_id': str(image_data['submission_id']),
        'result': int(image_data['result']) if pd.notna(image_data['result']) else None,
        'filename': image_data['filename'],
        'image_path': relative_path,
        'remaining': len(unreviewed_df),
        'file_size': file_size
    })


@app.route('/api/review', methods=['POST'])
def review():
    """提交审核结果"""
    data = request.json
    submission_id = data.get('submission_id')
    review_result = data.get('result')  # 1=通过, 0=拒绝
    
    if submission_id is None or review_result is None:
        return jsonify({'success': False, 'message': '参数错误'})
    
    # 加载现有审核结果
    review_df = load_review_results()
    
    # 添加新记录
    import time
    new_record = pd.DataFrame([{
        'submission_id': str(submission_id),
        'review_result': int(review_result),
        'review_time': time.strftime('%Y-%m-%d %H:%M:%S')
    }])
    
    # 合并并去重（如果已存在则更新）
    if len(review_df) > 0:
        review_df = review_df[review_df['submission_id'].astype(str) != str(submission_id)]
    
    review_df = pd.concat([review_df, new_record], ignore_index=True)
    
    # 保存
    REVIEW_RESULT_CSV.parent.mkdir(parents=True, exist_ok=True)
    review_df.to_csv(REVIEW_RESULT_CSV, index=False)
    
    return jsonify({'success': True, 'message': '审核结果已保存'})


@app.route('/api/stats')
def stats():
    """获取统计信息"""
    clean_df = load_clean_data()
    review_df = load_review_results()
    
    total = len(clean_df)
    reviewed = len(review_df) if len(review_df) > 0 else 0
    remaining = total - reviewed
    
    approved = 0
    rejected = 0
    if len(review_df) > 0:
        approved = len(review_df[review_df['review_result'] == 1])
        rejected = len(review_df[review_df['review_result'] == 0])
    
    return jsonify({
        'total': total,
        'reviewed': reviewed,
        'remaining': remaining,
        'approved': approved,
        'rejected': rejected
    })


@app.route('/images/<path:filename>')
def serve_image(filename):
    """提供图片文件"""
    # 从BASE_DIR开始查找图片
    image_path = BASE_DIR / filename.replace('\\', '/')
    if image_path.exists() and image_path.is_file():
        return send_from_directory(str(image_path.parent), image_path.name)
    
    # 如果找不到，尝试直接从front目录查找
    filename_only = os.path.basename(filename)
    front_path = FRONT_DIR / filename_only
    if front_path.exists() and front_path.is_file():
        return send_from_directory(str(FRONT_DIR), filename_only)
    
    return "Image not found", 404


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='图片审核系统')
    parser.add_argument(
        '--port',
        type=int,
        default=5001,
        help='服务器端口（默认: 5001，避免与macOS AirPlay冲突）'
    )
    args = parser.parse_args()
    
    print("=" * 60)
    print("图片审核系统")
    print("=" * 60)
    print(f"数据文件: {CLEAN_DATA_CSV}")
    print(f"审核结果: {REVIEW_RESULT_CSV}")
    print(f"\n访问地址: http://localhost:{args.port}")
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=args.port)

