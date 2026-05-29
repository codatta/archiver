# 数据审核模块

用于审核交易所截图数据的有效性，使用Qwen视觉模型进行智能审核。

## 功能特性

1. **交易所记录验证**: 检查截图是否来自交易所的提现或入金记录页面
2. **交易所身份验证**: 检查截图中是否有足够证据证明截图来自目标交易所（URL、logo、交易所名称等）
3. **交易明细匹配**: 检查截图中的交易明细与记录数据是否没有明显冲突

## 项目结构

```
audit_exchange_ui/
├── __init__.py              # 模块初始化
├── models.py                # 数据模型定义
├── data_loader.py           # 数据加载器
├── auditor.py               # 审核器基类
├── base_qwen_auditor.py     # Qwen审核器基类（共同逻辑）
├── qwen_auditors.py         # Qwen审核器实现（包含入金和提现审核器）
├── main.py                  # 主程序入口
└── README.md                # 本文档
```

### 架构说明

- **auditor.py**: 审核器抽象基类，定义审核接口
- **base_qwen_auditor.py**: Qwen审核器基类，包含所有审核器的共同逻辑（图片下载、API调用、前3个检查项）
- **qwen_auditors.py**: 包含两个具体的审核器实现：
  - **DepositQwenAuditor**: 专门处理入金数据的审核，包含入金特定的交易明细匹配逻辑
  - **WithdrawQwenAuditor**: 专门处理提现数据的审核，包含提现特定的交易明细匹配逻辑

主程序会根据记录类型自动选择合适的审核器。

## 安装依赖

```bash
pip3.10 install -r requirements.txt
```

## 配置

1. 复制环境变量配置文件：
```bash
cp env.sample .env
```

2. 编辑 `.env` 文件，填入你的Qwen API密钥：
```
QWEN_API_KEY=your_qwen_api_key_here
QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
```

## 使用方法

### 基本用法

审核所有数据（入金+提现）：
```bash
python3.10 -m audit_exchange_ui.main
```

### 高级用法

只审核入金数据：
```bash
python3.10 -m audit_exchange_ui.main --type deposit
```

只审核提现数据：
```bash
python3.10 -m audit_exchange_ui.main --type withdraw
```

指定输出文件：
```bash
python3.10 -m audit_exchange_ui.main --output results/my_report.json
```

指定数据目录：
```bash
python3.10 -m audit_exchange_ui.main --data-dir my_data
```

使用命令行参数指定API密钥（不推荐，建议使用环境变量）：
```bash
python3.10 -m audit_exchange_ui.main --api-key your_api_key
```

## 输出格式

审核结果会保存为JSON文件，格式如下：

```json
[
  {
    "submission_id": "2026011504082400108842",
    "overall_result": "pass",
    "timestamp": "2026-01-22T10:30:00",
    "record": {
      "submission_id": "2026011504082400108842",
      "date": "2026-01-15",
      "type": "deposit",
      "token": "USDT",
      "amount": "10",
      "network": "BNB",
      "exchange_name": "Binance",
      "exchange_ui_screenshot_url": "https://..."
    },
    "checks": [
      {
        "check_name": "is_exchange_record",
        "result": "pass",
        "reason": "截图显示Binance交易所的入金记录页面",
        "confidence": 0.95
      },
      {
        "result": "pass",
        "reason": "截图显示PC浏览器界面",
        "confidence": 0.9
      },
      {
        "check_name": "exchange_verification",
        "result": "pass",
        "reason": "URL包含binance.com域名",
        "confidence": 0.92
      },
      {
        "check_name": "transaction_match",
        "result": "pass",
        "reason": "交易明细与记录数据匹配",
        "confidence": 0.88
      }
    ]
  }
]
```

## 扩展性设计

### 添加新的审核检查项

1. 在 `base_qwen_auditor.py` 的 `_perform_all_checks` 方法中添加新的检查项到prompt中
2. 在 `_parse_all_checks_response` 方法中添加对应的解析逻辑

### 自定义入金/提现审核逻辑

如果需要修改入金或提现的审核逻辑：

1. **修改入金审核逻辑**：编辑 `qwen_auditors.py` 中 `DepositQwenAuditor` 类的 `_get_transaction_match_prompt` 方法
2. **修改提现审核逻辑**：编辑 `qwen_auditors.py` 中 `WithdrawQwenAuditor` 类的 `_get_transaction_match_prompt` 方法

这两个方法返回的prompt会被合并到完整的审核prompt中。

### 使用其他审核器

可以继承 `Auditor` 基类实现其他审核器（如使用其他AI模型）：

```python
from .auditor import Auditor
from .models import TransactionRecord, AuditReport

class CustomAuditor(Auditor):
    def audit(self, record: TransactionRecord) -> AuditReport:
        # 实现自定义审核逻辑
        pass
```

### 添加新的数据源

可以扩展 `DataLoader` 类以支持其他数据源：

```python
class DataLoader:
    def load_from_database(self, connection_string: str):
        # 从数据库加载数据
        pass
    
    def load_from_api(self, api_url: str):
        # 从API加载数据
        pass
```

## 注意事项

1. Qwen API调用需要网络连接，请确保网络畅通
2. 审核大量数据可能需要较长时间，建议分批处理
3. API调用可能产生费用，请注意使用量
4. 图片下载失败会导致该记录的审核结果为"未知"

## 故障排除

### API密钥错误
- 检查 `.env` 文件中的 `QWEN_API_KEY` 是否正确
- 或使用 `--api-key` 参数直接指定

### 图片下载失败
- 检查网络连接
- 确认图片URL是否可访问
- 检查URL是否有效

### 审核结果不准确
- 可以调整 `qwen_auditors.py` 中的提示词（prompt）以提高准确性
- 检查置信度（confidence）值，低置信度的结果可能需要人工复核
