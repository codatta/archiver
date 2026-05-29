#!/bin/bash
# 自动解压脚本
# 使用方法: bash extract_all.sh [target_directory]

TARGET_DIR=${1:-"extracted_images"}
mkdir -p "$TARGET_DIR"

echo "开始解压所有压缩包到: $TARGET_DIR"
echo "========================================"

echo "解压: images_batch_01_of_10_20260124_184306.zip"
unzip -q "images_batch_01_of_10_20260124_184306.zip" -d "$TARGET_DIR"
echo "完成: 216 个文件"

echo "解压: images_batch_02_of_10_20260124_184306.zip"
unzip -q "images_batch_02_of_10_20260124_184306.zip" -d "$TARGET_DIR"
echo "完成: 215 个文件"

echo "解压: images_batch_03_of_10_20260124_184306.zip"
unzip -q "images_batch_03_of_10_20260124_184306.zip" -d "$TARGET_DIR"
echo "完成: 215 个文件"

echo "解压: images_batch_04_of_10_20260124_184306.zip"
unzip -q "images_batch_04_of_10_20260124_184306.zip" -d "$TARGET_DIR"
echo "完成: 215 个文件"

echo "解压: images_batch_05_of_10_20260124_184306.zip"
unzip -q "images_batch_05_of_10_20260124_184306.zip" -d "$TARGET_DIR"
echo "完成: 215 个文件"

echo "解压: images_batch_06_of_10_20260124_184306.zip"
unzip -q "images_batch_06_of_10_20260124_184306.zip" -d "$TARGET_DIR"
echo "完成: 215 个文件"

echo "解压: images_batch_07_of_10_20260124_184306.zip"
unzip -q "images_batch_07_of_10_20260124_184306.zip" -d "$TARGET_DIR"
echo "完成: 215 个文件"

echo "解压: images_batch_08_of_10_20260124_184306.zip"
unzip -q "images_batch_08_of_10_20260124_184306.zip" -d "$TARGET_DIR"
echo "完成: 215 个文件"

echo "解压: images_batch_09_of_10_20260124_184306.zip"
unzip -q "images_batch_09_of_10_20260124_184306.zip" -d "$TARGET_DIR"
echo "完成: 215 个文件"

echo "解压: images_batch_10_of_10_20260124_184306.zip"
unzip -q "images_batch_10_of_10_20260124_184306.zip" -d "$TARGET_DIR"
echo "完成: 216 个文件"

echo "========================================"
echo "所有文件解压完成!"
echo "解压目录: $TARGET_DIR"
echo "总文件数: $(find "$TARGET_DIR" -type f | wc -l)"
