#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片审核Web应用 - 审核annotated_image
"""

import csv
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from pathlib import Path

# 配置路径
BASE_DIR = Path(__file__).parent
CSV_FILE = BASE_DIR / "旋钮_交付.csv"
RESULT_DIR = BASE_DIR / "result"
REVIEW_RESULT_CSV = RESULT_DIR / "review_results.csv"

app = Flask(__name__)

# 确保result目录存在
RESULT_DIR.mkdir(exist_ok=True)


def load_data():
    """加载CSV数据"""
    data = []
    if not CSV_FILE.exists():
        return data
    
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # 解析JSON
                data_submission = json.loads(row['data_submission'])
                annotated_image = data_submission.get('data', {}).get('annotated_image', '')
                
                if annotated_image:
                    data.append({
                        'submission_id': row['submission_id'],
                        'annotated_image': annotated_image,
                        'scale_value': data_submission.get('data', {}).get('scale_value', ''),
                    })
            except Exception as e:
                print(f"解析错误 {row.get('submission_id', 'unknown')}: {e}")
                continue
    
    return data


def load_review_results():
    """加载审核结果"""
    reviewed_ids = set()
    if not REVIEW_RESULT_CSV.exists():
        return reviewed_ids
    
    with open(REVIEW_RESULT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            reviewed_ids.add(row['submission_id'])
    
    return reviewed_ids


def save_review_result(submission_id, review_result):
    """保存审核结果"""
    # 检查文件是否存在，决定是否写入表头
    file_exists = REVIEW_RESULT_CSV.exists()
    
    with open(REVIEW_RESULT_CSV, 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['submission_id', 'review_result', 'review_time'])
        
        review_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        writer.writerow([submission_id, review_result, review_time])


@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/api/get_image')
def get_image():
    """获取未审核的图片"""
    all_data = load_data()
    reviewed_ids = load_review_results()
    
    # 找出未审核的图片
    unreviewed = [item for item in all_data if item['submission_id'] not in reviewed_ids]
    
    if len(unreviewed) == 0:
        return jsonify({
            'success': False,
            'message': '所有图片已审核完成！'
        })
    
    # 返回第一张未审核的图片
    image_data = unreviewed[0]
    return jsonify({
        'success': True,
        'submission_id': image_data['submission_id'],
        'annotated_image': image_data['annotated_image'],
        'scale_value': image_data.get('scale_value', ''),
        'total': len(all_data),
        'reviewed': len(reviewed_ids),
        'remaining': len(unreviewed)
    })


@app.route('/api/review', methods=['POST'])
def review():
    """提交审核结果"""
    data = request.json
    submission_id = data.get('submission_id')
    review_result = data.get('review_result')  # 1: 通过, 0: 拒绝
    
    if not submission_id or review_result is None:
        return jsonify({'success': False, 'message': '参数错误'})
    
    # 保存审核结果
    save_review_result(submission_id, review_result)
    
    return jsonify({'success': True})


@app.route('/api/stats')
def stats():
    """获取统计信息"""
    all_data = load_data()
    reviewed_ids = load_review_results()
    
    # 统计通过和拒绝的数量
    approved = 0
    rejected = 0
    
    if REVIEW_RESULT_CSV.exists():
        with open(REVIEW_RESULT_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['review_result'] == '1':
                    approved += 1
                else:
                    rejected += 1
    
    return jsonify({
        'total': len(all_data),
        'reviewed': len(reviewed_ids),
        'remaining': len(all_data) - len(reviewed_ids),
        'approved': approved,
        'rejected': rejected
    })


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='图片审核Web应用')
    parser.add_argument('--port', type=int, default=5002, help='端口号（默认: 5002）')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='主机地址（默认: 127.0.0.1）')
    args = parser.parse_args()
    
    print("=" * 60)
    print("图片审核系统")
    print("=" * 60)
    print(f"CSV文件: {CSV_FILE}")
    print(f"审核结果保存到: {REVIEW_RESULT_CSV}")
    print(f"访问地址: http://{args.host}:{args.port}")
    print("=" * 60)
    
    app.run(host=args.host, port=args.port, debug=True)
