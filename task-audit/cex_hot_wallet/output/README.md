# 输出目录

此目录用于统一存放所有模块的输出结果文件，实现代码与数据的完全分离。

## 目录结构

```
output/
├── audit_exchange_ui/          # 交易所界面审核结果
│   └── audit_report.json       # 交易所截图审核报告
│
├── audit_txhash/               # 交易哈希审核结果
│   └── txhash_verification_results.json  # 交易哈希验证结果
│
├── main_audit/                 # 综合审核结果
│   └── comprehensive_audit_results.json  # 综合审核结果（包含UI和交易哈希审核）
│
└── deliver_results/            # CSV交付数据
    └── delivery_results.csv    # 最终交付的CSV格式数据
```

## 文件说明

### audit_exchange_ui/audit_report.json
交易所截图审核的结果文件，包含：
- 每条记录的审核结果（pass/fail）
- 各项检查项的详细结果
- 审核时间戳

### audit_txhash/txhash_verification_results.json
交易哈希验证的结果文件，包含：
- 每条记录的验证结果（pass/fail）
- 地址匹配、日期匹配等检查项
- 验证统计信息

### main_audit/comprehensive_audit_results.json
综合审核的结果文件，整合了：
- UI审核结果
- 交易哈希审核结果
- 综合统计信息

### deliver_results/delivery_results.csv
最终交付的CSV格式数据，包含：
- 审核通过的记录
- 标准化的字段格式
- 可用于外部系统导入

## 注意事项

1. **自动创建**：各模块会自动创建对应的子目录
2. **版本控制**：建议将 `output/` 目录添加到 `.gitignore`，避免提交结果文件
3. **清理**：可以定期清理此目录，重新运行审核会生成新的结果文件

## 迁移说明

如果你之前使用的是旧路径，结果文件已经自动迁移到此目录。旧路径的文件已移动到新位置：

- `audit_exchange_ui/audit_results/audit_report.json` → `output/audit_exchange_ui/audit_report.json`
- `audit_txhash/txhash_verification_results.json` → `output/audit_txhash/txhash_verification_results.json`
- `main_audit/comprehensive_audit_results.json` → `output/main_audit/comprehensive_audit_results.json`
- `deliver_results/delivery_results.csv` → `output/deliver_results/delivery_results.csv`
