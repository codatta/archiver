"""
Qwen审核器实现
包含入金和提现的Qwen审核器
"""
from .base_qwen_auditor import BaseQwenAuditor
from .models import TransactionRecord


class DepositQwenAuditor(BaseQwenAuditor):
    """入金数据Qwen审核器"""
    
    def _get_transaction_match_prompts(self, record: TransactionRecord) -> tuple[str, str]:
        """
        获取入金交易明细匹配的prompt（拆分为日期匹配和其他信息匹配）
        
        Args:
            record: 交易记录
            
        Returns:
            (交易日期匹配prompt, 其他交易信息匹配prompt) 元组
        """
        # 从raw_data中提取更多信息
        to_address = record.raw_data.get("to_address", "")  # 接收地址
        tx_hash = record.raw_data.get("tx_hash", "")  # 交易哈希
        
        # 交易日期匹配prompt
        date_match_prompt = f"""检查截图中的交易日期是否与提交数据中的日期匹配。

提交数据中的交易日期：{record.date}

审核步骤（请严格按照以下两步执行）：

**第一步：识别并提取截图中的交易日期**
- 从截图中识别交易日期，无论格式如何（如"2026-01-15"、"2026/01/15"、"Jan 15, 2026"、"2026年1月15日"、"01/15/2026"等）
- 遇到存在歧义的格式（例如 "01/05/2026"），请结合提交数据中的日期 {record.date} 来辅助理解：
  - 如果日/月对调后能与 {record.date} 对应，则采用对调后的日期
  - 优先采用与 {record.date} 更接近的日期解释
- 将识别到的日期统一格式化为 "YYYY-MM-DD" 格式，存入 `detected_date` 字段

**第二步：比较日期并判断是否匹配**
- 比较 `detected_date` 和提交数据中的日期 `{record.date}`（两者都是 YYYY-MM-DD 格式）
- 计算两个日期的差值（天数）
- **判定规则**：
  - 如果日期差在 **1天之内**（包括同一天、相差1天），则 `result: true`（匹配）
  - 如果日期差超过1天，则 `result: false`（不匹配）
- 如果截图中无法识别到交易日期，则 `result: false`，`detected_date` 可以为空或填写 "无法识别"

**重要**：请确保 `detected_date` 字段统一格式化为 "YYYY-MM-DD"（如 "2026-01-05"），并在理由中说明识别到的原始日期格式和转换后的日期。"""
        
        # 其他交易信息匹配prompt
        info_match_prompt = f"""检查截图中的其他交易信息是否与提交数据匹配（不包括日期，日期已在检查3中单独验证）。

提交数据：
- 交易类型：入金（Deposit）
- 币种：{record.token}
- 金额：{record.amount}
- 网络：{record.network}
- 接收地址（to_address）：{to_address if to_address else "未提供"}
- 交易哈希（tx_hash）：{tx_hash if tx_hash else "未提供"}

审核要求（宽松匹配，语义一致即可）：
1. **交易类型**：截图应该显示入金/Deposit相关的语义，不要求文本完全一致（如"入金"、"Deposit"、"充值"等都算匹配）

2. **币种**：币种名称可能以不同方式显示（如"USDT"和"Tether"、"BTC"和"Bitcoin"），只要指的是同一种币即可。也允许显示为"BSC-USDT"、"ERC20-USDT"等格式，只要基础币种一致即可

3. **金额**：金额格式可能不同（如"10"和"10.00"、"10 USDT"），只要数值相同即可。允许有微小的显示差异（如四舍五入导致的最后一位不同）

4. **网络**：网络名称可能有不同表示（如"BNB"和"BSC"、"Binance Smart Chain"），只要指的是同一网络即可

5. **接收地址**：地址在图片中可能被隐藏部分信息（如只显示前几位和后几位，中间用...代替），只要可见部分匹配即可。地址格式可能不同（大小写、有无0x前缀等），只要语义相同即可

6. **交易哈希**：交易哈希在图片中可能被隐藏部分信息（如只显示前几位和后几位，中间用...代替），只要可见部分匹配即可。哈希格式可能不同（大小写、有无0x前缀等），只要语义相同即可

**判定标准**：
- 只要截图中的信息与上述数据在语义上一致（不要求文本完全一致），就判定为匹配
- 只有当截图中的信息与上述数据在语义上有明显冲突时（如币种完全不同、金额差异很大等），才判定为不匹配
- 如果截图显示的是提现（Withdrawal）而不是入金，则判定为不匹配"""
        
        return date_match_prompt, info_match_prompt


class WithdrawQwenAuditor(BaseQwenAuditor):
    """提现数据Qwen审核器"""
    
    def _get_transaction_match_prompts(self, record: TransactionRecord) -> tuple[str, str]:
        """
        获取提现交易明细匹配的prompt（拆分为日期匹配和其他信息匹配）
        
        Args:
            record: 交易记录
            
        Returns:
            (交易日期匹配prompt, 其他交易信息匹配prompt) 元组
        """
        # 从raw_data中提取更多信息
        address = record.raw_data.get("address", "")  # 接收地址
        tx_hash = record.raw_data.get("tx_hash", "")  # 交易哈希
        network_fee = record.raw_data.get("network_fee", "")
        
        # 交易日期匹配prompt
        date_match_prompt = f"""检查截图中的交易日期是否与提交数据中的日期匹配。

提交数据中的交易日期：{record.date}

审核步骤（请严格按照以下两步执行）：

**第一步：识别并提取截图中的交易日期**
- 从截图中识别交易日期，无论格式如何（如"2026-01-04"、"2026/01/04"、"Jan 4, 2026"、"2026年1月4日"、"01/04/2026"等）
- 遇到存在歧义的格式（例如 "01/05/2026"），请结合提交数据中的日期 {record.date} 来辅助理解：
  - 如果日/月对调后能与 {record.date} 对应，则采用对调后的日期
  - 优先采用与 {record.date} 更接近的日期解释
- 将识别到的日期统一格式化为 "YYYY-MM-DD" 格式，存入 `detected_date` 字段

**第二步：比较日期并判断是否匹配**
- 比较 `detected_date` 和提交数据中的日期 `{record.date}`（两者都是 YYYY-MM-DD 格式）
- 计算两个日期的差值（天数）
- **判定规则**：
  - 如果日期差在 **1天之内**（包括同一天、相差1天），则 `result: true`（匹配）
  - 如果日期差超过1天，则 `result: false`（不匹配）
- 如果截图中无法识别到交易日期，则 `result: false`，`detected_date` 可以为空或填写 "无法识别"

**重要**：请确保 `detected_date` 字段统一格式化为 "YYYY-MM-DD"（如 "2026-01-05"），并在理由中说明识别到的原始日期格式和转换后的日期。"""
        
        # 其他交易信息匹配prompt
        info_match_prompt = f"""检查截图中的其他交易信息是否与提交数据匹配（不包括日期，日期已在检查3中单独验证）。

提交数据：
- 交易类型：提现（Withdrawal）
- 币种：{record.token}
- 金额：{record.amount}
- 网络：{record.network}
- 接收地址：{address if address else "未提供"}
- 交易哈希（tx_hash）：{tx_hash if tx_hash else "未提供"}
- 网络手续费：{network_fee if network_fee else "未提供"}

审核要求（宽松匹配，语义一致即可）：
1. **交易类型**：截图应该显示提现/Withdrawal相关的语义，不要求文本完全一致（如"提现"、"Withdrawal"、"Withdraw"、"转出"等都算匹配）

2. **币种**：币种名称可能以不同方式显示（如"USDT"和"Tether"、"BTC"和"Bitcoin"），只要指的是同一种币即可。也允许显示为"BSC-USDT"、"ERC20-USDT"等格式，只要基础币种一致即可

3. **金额**：金额格式可能不同（如"299.99"和"299.9900"、"299.99 USDT"），只要数值相同即可。允许有微小的显示差异（如四舍五入导致的最后一位不同）

4. **网络**：网络名称可能有不同表示（如"BNB"和"BSC"、"Binance Smart Chain"），只要指的是同一网络即可

5. **接收地址**：地址在图片中可能被隐藏部分信息（如只显示前几位和后几位，中间用...代替），只要可见部分匹配即可。地址格式可能不同（大小写、有无0x前缀等），只要语义相同即可

6. **交易哈希**：交易哈希在图片中可能被隐藏部分信息（如只显示前几位和后几位，中间用...代替），只要可见部分匹配即可。哈希格式可能不同（大小写、有无0x前缀等），只要语义相同即可

7. **网络手续费**：手续费格式可能不同，只要数值相同或接近即可

**判定标准**：
- 只要截图中的信息与上述数据在语义上一致（不要求文本完全一致），就判定为匹配
- 只有当截图中的信息与上述数据在语义上有明显冲突时（如币种完全不同、金额差异很大等），才判定为不匹配
- 如果截图显示的是入金（Deposit）而不是提现，则判定为不匹配"""
        
        return date_match_prompt, info_match_prompt
