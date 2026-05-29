# 图片去重工具

基于图片内容哈希的去重工具，用于对 `front_image` 进行去重处理。

## 功能特点

- **模块化设计**：图片下载、哈希计算、去重统计分离，方便后续扩展
- 自动下载所有 front_image 图片到 `download_images/front` 目录
- 使用 MD5 哈希值识别内容相同的图片
- 支持多个目录的哈希计算和重复统计
- 生成详细的统计报告

## 项目结构

```
check_unique/
├── download_images.py              # 图片下载脚本
├── calculate_hash_front.py         # 计算front目录图片哈希
├── calculate_hash_done_images.py   # 计算done_images目录图片哈希
├── statistics_duplicates.py        # 统计重复情况
├── deduplicate_images.py           # 原始去重脚本（保留兼容）
├── utils.py                        # 共享工具函数
├── files/                          # 哈希数据存储目录
│   ├── front.csv                   # front目录哈希数据
│   └── done_images.csv             # done_images目录哈希数据
├── requirements.txt                # 依赖包列表
└── README.md                       # 说明文档
```

## 安装依赖

```bash
pip3.10 install -r requirements.txt
```

## 使用流程

### 步骤1：下载图片（可选）

如果需要从CSV下载图片：

```bash
# 使用默认线程数（10个线程）
python3.10 download_images.py

# 自定义线程数（例如使用20个线程加速下载）
python3.10 download_images.py --workers 20
```

**功能：**
- 从 CSV 文件读取所有 front_image URL
- **并行下载**：使用多线程加速下载（默认10个线程，可通过 `--workers` 参数调整）
- 下载图片到 `download_images/front/` 目录
- 图片命名格式：`{submission_id}_{result}_front.{ext}`
- 生成图片映射文件 `image_mapping.csv`

**性能提示：**
- 网络条件好时，可以增加线程数（如 `--workers 20` 或 `--workers 30`）以加快下载速度
- 如果遇到连接错误，可以适当降低线程数（如 `--workers 5`）
- 默认10个线程在大多数情况下已经能显著提升下载速度

### 步骤2：计算图片哈希值

#### 2.1 计算front目录图片哈希

```bash
python3.10 calculate_hash_front.py
```

**功能：**
- 扫描 `download_images/front/` 目录下的所有图片
- 计算每张图片的 MD5 哈希值
- 保存结果到 `files/front.csv`

**输出文件：** `files/front.csv`
- `submission_id`: 提交ID
- `result`: 评价分数
- `filename`: 文件名
- `filepath`: 完整文件路径
- `hash`: MD5哈希值
- `file_size`: 文件大小（字节）

#### 2.2 计算done_images目录图片哈希

```bash
python3.10 calculate_hash_done_images.py
```

**功能：**
- 递归扫描 `done_images/` 目录及其所有子目录下的图片
- 计算每张图片的 MD5 哈希值
- 保存结果到 `files/done_images.csv`

**输出文件：** `files/done_images.csv`
- `submission_id`: 提交ID（如果可从文件名提取）
- `result`: 评价分数（如果可从文件名提取）
- `filename`: 文件名
- `filepath`: 完整文件路径
- `relative_path`: 相对路径
- `subdirectory`: 子目录名
- `hash`: MD5哈希值
- `file_size`: 文件大小（字节）

### 步骤3：统计重复情况

```bash
python3.10 statistics_duplicates.py
```

**功能：**
- 统计front目录下图片的重复情况
- 统计去重后的front目录和done_images目录的交叉重复情况
- 生成详细的统计报告

**输出文件：** `duplicate_statistics.txt`

**报告内容包括：**
1. **Front目录重复情况**
   - 总文件数
   - 唯一哈希数
   - 重复组数
   - 重复文件数
   - 去重后文件数
   - 重复详情（前10组）

2. **Front目录（去重后）与Done_images目录的重复情况**
   - Front目录唯一哈希数
   - Done_images目录唯一哈希数
   - 共同哈希数
   - 交叉重复详情（前10组）

## 完整工作流程示例

```bash
# 1. 下载图片（如果需要）
python3.10 download_images.py --workers 20

# 2. 计算front目录图片哈希
python3.10 calculate_hash_front.py

# 3. 计算done_images目录图片哈希
python3.10 calculate_hash_done_images.py

# 4. 统计重复情况
python3.10 statistics_duplicates.py
```

## 断点续传

下载脚本支持断点续传：
- 如果文件已存在，会自动跳过下载
- 程序中断后重新运行，已下载的文件不会被重复下载
- 只下载缺失的文件，节省时间和带宽

## 扩展说明

由于代码已模块化，你可以轻松扩展功能：

1. **修改下载逻辑**：编辑 `download_images.py`
2. **修改哈希算法**：修改 `utils.py` 中的 `get_image_hash()` 函数（如使用感知哈希）
3. **添加新的统计功能**：编辑 `statistics_duplicates.py`
4. **处理其他目录**：参考现有脚本创建新的哈希计算脚本

## 注意事项

- 确保有足够的磁盘空间存储所有图片
- 下载过程可能需要较长时间，请耐心等待
- 如果网络不稳定，脚本会自动重试（最多3次）
- 已下载的图片不会重复下载，提高效率
- 哈希计算过程可能需要一些时间，取决于图片数量和大小

## 兼容性说明

原始的 `deduplicate_images.py` 脚本仍然保留，用于基于 `image_mapping.csv` 的去重处理。新的模块化脚本提供了更灵活的功能，可以处理多个目录和更复杂的统计需求。
