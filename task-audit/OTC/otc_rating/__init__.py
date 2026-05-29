"""
OTC 截图审核评级模块

从 otc_audit 产生的结果 + 数据库 data_submission 中的信息，给每条 submission 打状态与评分：
- status: REFUSED / ADOPT
- result: 1~5
"""

