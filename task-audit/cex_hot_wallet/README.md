# CEX 热钱包审核系统

用于审核中心化交易所（CEX）热钱包交易记录的系统，包含交易所截图审核和交易哈希验证两个主要模块。

## 项目结构

```
cex_hot_wallet/
├── utils.py                    # 公共工具函数（JSON处理、地址处理等）
├── network_mapping.py          # 网络映射配置（统一管理网络名称映射）
├── audit_check_config.json     # 审核子项 check_name 的物理含义说明（非代码必需）
├── audit_exchange_ui/          # 交易所截图审核模块
│   ├── main.py                 # 主程序入口
│   ├── auditor.py              # 审核器基类
│   ├── qwen_auditors.py        # Qwen审核器实现
│   └── README.md              # 模块说明文档
│
├── get_txhash_info/            # 交易哈希信息获取模块
│   ├── main.py                 # 主程序入口
│   ├── tx_fetcher.py          # 交易信息获取器
│   ├── chain_config.py        # 区块链配置
│   ├── models.py              # 数据模型
│   └── README.md              # 模块说明文档
│
├── audit_txhash/               # 交易哈希验证审核模块
│   └── txhash_auditor.py      # 交易哈希审核器
│
├── main_audit/                # 综合审核模块
│   ├── main_auditor.py        # 综合审核器主入口
│   └── README.md              # 模块说明文档
│
├── deliver_results/            # CSV交付数据生成模块
│   └── csv_generator.py       # CSV生成器
│
├── output/                     # 统一输出目录（所有结果文件）
│   ├── audit_exchange_ui/     # 交易所界面审核结果
│   │   └── audit_report.json
│   ├── audit_txhash/          # 交易哈希审核结果
│   │   └── txhash_verification_results.json
│   ├── main_audit/            # 综合审核结果
│   │   └── comprehensive_audit_results.json
│   └── deliver_results/       # CSV交付数据与统计报告
│       ├── delivery_results_rating_5.csv
│       ├── delivery_results_rating_4.csv
│       ├── delivery_results_duplicate.csv
│       ├── delivery_statistics_report.md   # 交付统计报告（含文件说明与字段文档跳转）
│       └── README.md                       # 面向客户的字段说明
│
├── raw_data/                   # 原始数据目录
│   └── submissions.json        # 提交的原始数据
│
├── requirements.txt            # Python依赖
├── env.sample                  # 环境变量示例
├── REFACTORING.md             # 代码重构说明文档
└── README.md                   # 本文档
```

## 功能模块

### 1. 交易所截图审核 (`audit_exchange_ui`)

使用 Qwen 视觉模型对交易所截图进行智能审核，验证：
- 是否为交易所记录页面
- 交易所身份验证（URL、logo、品牌标识等）
- 交易明细匹配（日期、币种、金额、网络、地址、交易哈希等）

**使用方法：**
```bash
cd cex_hot_wallet
python3.10 -m audit_exchange_ui.main
```

详细说明请参考：`audit_exchange_ui/README.md`

### 2. 交易哈希信息获取 (`get_txhash_info`)

支持从多条区块链获取交易信息，包括：
- 交易发送地址（from）
- 交易接收地址（to）
- 交易日期
- 交易金额、gas费用等详细信息

**支持的链：**
- EVM 链：BSC、ETH、BASE、ARB、OP、Polygon、ETC
- 非 EVM 链：BTC、TRON、BCH

**使用方法：**
```bash
# 命令行使用
python3.10 -m get_txhash_info.main <tx_hash> --chain <chain_name>

# 示例
python3.10 -m get_txhash_info.main 0x6870cdd18a1c1126af6e97312bfb7e1e72e80f4e27e0353cbecf7b090c68130b --chain bsc
```

详细说明请参考：`get_txhash_info/README.md`

### 3. 交易哈希验证审核 (`audit_txhash`)

对审核通过的记录进行交易哈希验证，确保：
- 交易哈希的 from/to 地址与记录一致
- 交易日期与记录一致（允许±1天误差）
- 对于 BTC 交易，支持多个地址的匹配验证
- 对于 deposit 交易，支持验证 outgoing 交易

**验证规则：**

**Withdrawal（提现）：**
- 验证 `tx_hash` 的 `from` 地址与 `sender_address` 一致（忽略大小写）
- 验证 `tx_hash` 的 `to` 地址与 `receiver_address` 一致（忽略大小写）
- 验证交易日期与 `transaction_date` 一致（允许±1天误差）

**Deposit（入金）：**
- 验证 `tx_hash` 的 `from` 地址与 `from_address` 一致
- 验证 `tx_hash` 的 `to` 地址与 `to_address` 一致
- 验证交易日期与 `date` 一致（允许±1天误差）
- 如果 `has_outgoing_transaction` 为 `true`，验证 `outgoing_transaction_hash` 的地址

**BTC 特殊处理：**
- BTC 交易的 from/to 可能有多个地址
- 只要任意一个地址与记录中的地址匹配即可通过

**使用方法：**
```bash
cd cex_hot_wallet
python3.10 -m audit_txhash.txhash_auditor
```

程序会自动：
1. 读取 `output/audit_exchange_ui/audit_report.json` 中审核通过的记录（如果存在）
2. 读取 `raw_data/submissions.json` 中的原始数据
3. 对每条记录进行交易哈希验证
4. 输出验证结果到 `output/audit_txhash/txhash_verification_results.json`

## 公共工具模块

### `utils.py` - 公共工具函数

提供各模块通用的工具函数：

- **JSON 处理**：`load_json()`, `save_json()`
- **地址处理**：`normalize_address()`, `compare_addresses()`, `check_address_in_list()`
- **数据解析**：`parse_submission_data()`, `build_submissions_map()`

### `network_mapping.py` - 网络映射配置

统一管理网络名称映射：

- **链标识映射**：`get_chain_from_network()` - 用于交易获取
- **标准枚举映射**：`get_enum_from_network()` - 用于 CSV 生成

所有网络映射配置集中在此文件，便于维护和扩展。

## 审核子项配置说明（check_name）

项目在根目录维护 `audit_check_config.json`，用于**描述**审核过程中各个子项的物理含义，方便查看和对外解释，并非运行审核流程的必需代码文件。

- 文件中按模块列出各审核阶段的检查项：
  - `audit_exchange_ui`：如 `is_exchange_record`、`exchange_verification`、`transaction_date_match`、`transaction_info_match` 等
  - `audit_txhash`：withdrawal/deposit 下的地址、日期、has_outgoing_transaction 等检查
- 每项包含：`check_name`、`name_cn`、`description`、`trace_type`、`result_values`、`related_fields`、`implemented_in` 等元信息
- 可作为运营 / 风控 / 客户说明文档的「索引」，帮助理解每一个审核子项在业务上的含义

> 说明：当前代码中不再依赖专门的 loader 模块，`audit_check_config.json` 主要承担**文档和对齐规范**的作用；如需在代码中使用，可按需自行 `json.load` 读取。

## 安装依赖

```bash
pip3.10 install -r requirements.txt
```

## 配置

1. 复制环境变量配置文件：
```bash
cp env.sample .env
```

2. 编辑 `.env` 文件，填入必要的 API 密钥：
```
QWEN_API_KEY=your_qwen_api_key_here
```

## 执行顺序总览（从审核到交付）

要完成一整套「数据审核 + 评级 + 最终交付」，现在推荐**直接从 MySQL 读取原始数据**，按以下顺序执行：

1. **配置 `.env` 中的数据库和 SQL**
   - 在 `env.sample` 的基础上复制为 `.env`，并按实际环境填写：
     - `DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` / `DB_NAME`
     - `DB_SUBMISSIONS_SQL`：综合审核入口使用的 SQL，必须返回：
       - `submission_id`
       - `data_submission`（JSON 字符串，或 `data_submission ->> '$.data'`）
     - `DB_DELIVER_SQL`：交付生成使用的 SQL，必须返回：
       - `submission_id`
       - `data_submission`
       - `rating`（整型，且为 4 或 5）

2. **执行综合审核入口 `main_audit/main_auditor.py`**
   ```bash
   cd cex_hot_wallet
   python3.10 -m main_audit.main_auditor
   ```
   - 内部会根据 `.env` 中的 `DB_SUBMISSIONS_SQL` **直接从数据库读取待审核的 submissions**，并依次调用：
     - `audit_exchange_ui`：基于截图 / 文本信息进行 UI 审核（含日期抽取 `detected_date` 等）
     - `audit_txhash`：基于链上交易哈希进行核验
   - 对每条 `submission` 的所有审核子项给出结构化结果
   - 输出综合审核结果到：`output/main_audit/comprehensive_audit_results.json`

3. **执行评级模块 `main_audit/rating.py`**
   ```bash
   cd cex_hot_wallet
   python3.10 -m main_audit.rating
   ```
   - 读取 `output/main_audit/comprehensive_audit_results.json`
   - 按规则对每条记录打分（1–5 分），并生成简要理由
   - 输出：
     - `output/main_audit/rating_results.json`（详细结果）
     - `output/main_audit/rating_results_simple.csv`（仅 `submission_id` + `rating`）

4. **执行交付结果生成 `deliver_results/csv_generator.py`**
   ```bash
   cd cex_hot_wallet
   python3.10 -m deliver_results.csv_generator
   ```
   - 内部会根据 `.env` 中的 `DB_DELIVER_SQL` **直接从数据库读取已采纳且评级为 4/5 分的记录**，并生成：
     - **交付 CSV**：
       - `output/deliver_results/delivery_results_rating_5.csv`：5 分记录（按 `address` 去重后，保留 `submission_id` 最小的那条）
       - `output/deliver_results/delivery_results_rating_4.csv`：4 分记录（同上）
       - `output/deliver_results/delivery_results_duplicate.csv`：所有被去重丢弃的重复有效记录（按 `address` 聚合）
     - **交付统计报告**：
       - `output/deliver_results/delivery_statistics_report.md`：当次交付的统计报告（总体统计、按评分/链/交易类型/交易所等维度），内含交付文件说明及跳转到字段说明文档的链接
   - 面向客户的**字段含义说明**见：`output/deliver_results/README.md`

## 评分逻辑

评级模块 `main_audit/rating.py` 根据综合审核结果中的各检查项，对每条 submission 打 1–5 分，规则如下：

| 条件 | 得分 |
|------|------|
| `is_exchange_record` 不通过 | 1 分 |
| `exchange_verification` 不通过 | 2 分 |
| 仅有 `transaction_date_match`（UI审核和交易哈希审核）不通过，其余检查项均通过 | 4 分 |
| 全部检查项通过 | 5 分 |
| 其他情况 | 3 分 |

其中「不通过」指该检查项结果为 `false` 或等效未通过；「通过」指结果为 `true` 或等效通过。评分理由由 `_generate_rating_reason()` 根据上述规则生成简要说明。

## 工作流程

### 完整审核流程

1. **交易所截图审核**
   ```bash
   python3.10 -m audit_exchange_ui.main
   ```
   - 读取 `raw_data/submissions.json`
   - 对每条记录进行截图审核
   - 输出结果到 `output/audit_exchange_ui/audit_report.json`

2. **交易哈希验证**
   ```bash
   python3.10 -m audit_txhash.txhash_auditor
   ```
   - 读取 `raw_data/submissions.json` 中的所有数据
   - 验证交易哈希信息
   - 输出结果到 `output/audit_txhash/txhash_verification_results.json`

### 单独使用交易哈希查询

如果需要单独查询某笔交易的信息：
```bash
python3.10 -m get_txhash_info.main <tx_hash> --chain <chain_name>
```

## 数据格式

### 输入数据 (`raw_data/submissions.json`)

每条记录包含：
- `submission_id`: 提交ID
- `data_submission`: JSON字符串，包含交易详情

### 审核报告 (`output/audit_exchange_ui/audit_report.json`)

每条记录包含：
- `submission_id`: 提交ID
- `overall_result`: 审核结果（"pass" 或 "fail"）
- `record`: 记录详情
- `checks`: 各项检查结果

### 验证结果 (`output/audit_txhash/txhash_verification_results.json`)

包含：
- `summary`: 汇总统计
- `verifications`: 每条记录的验证结果

## 特性

- ✅ 多链支持（BSC、ETH、BTC、BASE、ARB、TRON、OP、Polygon、ETC、BCH）
- ✅ 自动重试机制（最多3次）
- ✅ BTC 多地址支持
- ✅ 日期容差处理（±1天）
- ✅ 详细的错误信息和验证报告

## 注意事项

1. **网络连接**：需要稳定的网络连接访问区块链 RPC 节点和 API
2. **API 限制**：公共 RPC 节点可能有速率限制，建议使用自己的节点
3. **时区处理**：交易日期验证允许±1天误差，以处理时区差异
4. **BTC 地址**：BTC 交易可能有多个输入/输出地址，只要任意一个匹配即可

## 故障排除

### 连接失败
- 检查网络连接
- 确认 RPC 节点 URL 是否正确
- 系统会自动尝试备用 RPC 节点

### 交易未找到
- 确认交易哈希是否正确
- 确认交易是否在指定链上
- 检查交易是否已确认（pending 交易可能查询不到）

### 地址不匹配
- 检查地址格式是否正确
- 对于 BTC，确认是否在地址列表中
- 检查大小写是否一致（系统会自动忽略大小写）

## 许可证

[根据项目实际情况填写]
