"""
Qwen审核器基类
包含共同的审核逻辑
"""
import os
import time
import base64
import requests
import json
import re
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timedelta
from abc import abstractmethod

from .auditor import Auditor
from .models import (
    TransactionRecord,
    AuditReport,
    AuditCheckResult,
    AuditResult,
    TransactionType,
)

# 尝试加载.env文件（如果存在）
try:
    from dotenv import load_dotenv
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass  # 如果没有安装python-dotenv，则跳过


class BaseQwenAuditor(Auditor):
    """Qwen审核器基类，包含共同的审核逻辑"""
    
    # 审核检查项名称
    CHECK_IS_EXCHANGE_RECORD = "is_exchange_record"
    CHECK_EXCHANGE_VERIFICATION = "exchange_verification"
    CHECK_TRANSACTION_DATE_MATCH = "transaction_date_match"
    CHECK_TRANSACTION_INFO_MATCH = "transaction_info_match"
    
    def __init__(self, api_key: str = None, base_url: str = None):
        """
        初始化Qwen审核器
        
        Args:
            api_key: Qwen API密钥，如果为None则从环境变量读取
            base_url: Qwen API基础URL，如果为None则从环境变量读取
        """
        super().__init__()
        self.api_key = api_key or os.getenv("QWEN_API_KEY")
        self.base_url = base_url or os.getenv(
            "QWEN_BASE_URL",
            "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        )
        
        if not self.api_key:
            raise ValueError("QWEN_API_KEY 未设置，请设置环境变量或传入参数")
    
    def audit(self, record: TransactionRecord) -> AuditReport:
        """
        审核单个交易记录
        
        Args:
            record: 交易记录
            
        Returns:
            审核报告
        """
        # 检查是否有缺失的必要字段
        missing_fields = record.raw_data.get("_missing_fields", [])
        if missing_fields:
            # 如果缺少必要字段，直接判定为失败，不调用LLM
            checks = [
                AuditCheckResult(
                    check_name=check_name,
                    result=AuditResult.FAIL,
                    reason=f"记录缺少必要字段: {', '.join(missing_fields)}",
                    llm_response=None,
                )
                for check_name in [
                    self.CHECK_IS_EXCHANGE_RECORD,
                    self.CHECK_EXCHANGE_VERIFICATION,
                    self.CHECK_TRANSACTION_DATE_MATCH,
                    self.CHECK_TRANSACTION_INFO_MATCH,
                ]
            ]
            reason = f"记录缺少必要字段: {', '.join(missing_fields)}"
            return AuditReport(
                submission_id=record.submission_id,
                record=record,
                checks=checks,
                overall_result=AuditResult.FAIL,
                timestamp=datetime.now().isoformat(),
                reason=reason,
                llm_raw_response=None,
            )
        
        checks = []
        
        # 下载并编码图片
        image_base64, mime_type = self._download_and_encode_image(record.exchange_ui_screenshot_url)
        if not image_base64:
            # 如果图片下载失败，所有检查都标记为未知
            checks = [
                AuditCheckResult(
                    check_name=check_name,
                    result=AuditResult.UNKNOWN,
                    reason="无法下载截图",
                )
                for check_name in [
                    self.CHECK_IS_EXCHANGE_RECORD,
                    self.CHECK_EXCHANGE_VERIFICATION,
                    self.CHECK_TRANSACTION_DATE_MATCH,
                    self.CHECK_TRANSACTION_INFO_MATCH,
                ]
            ]
            reason = "无法下载截图，无法进行审核"
            return AuditReport(
                submission_id=record.submission_id,
                record=record,
                checks=checks,
                overall_result=AuditResult.UNKNOWN,
                timestamp=datetime.now().isoformat(),
                reason=reason,
            )
        
        # 执行所有检查（合并为一次API调用以提高效率）
        checks, llm_raw_data = self._perform_all_checks(record, image_base64, mime_type)
        
        # 确定总体结果
        overall_result = self._determine_overall_result(checks)
        
        # 生成失败原因概述
        reason = None
        if overall_result == AuditResult.FAIL:
            failed_checks = [check for check in checks if check.result == AuditResult.FAIL]
            if failed_checks:
                check_names_cn = {
                    "is_exchange_record": "交易所记录验证",
                    "exchange_verification": "交易所身份验证",
                    "transaction_date_match": "交易日期匹配",
                    "transaction_info_match": "其他交易信息匹配",
                }
                failed_names = [check_names_cn.get(check.check_name, check.check_name) for check in failed_checks]
                reason = f"以下检查项失败: {', '.join(failed_names)}"
        elif overall_result == AuditResult.UNKNOWN:
            reason = "审核结果未知，可能由于API调用失败或数据解析错误"
        
        return AuditReport(
            submission_id=record.submission_id,
            record=record,
            checks=checks,
            overall_result=overall_result,
            timestamp=datetime.now().isoformat(),
            reason=reason,
            llm_raw_response=llm_raw_data,  # 保存LLM返回的完整原始数据
        )
    
    def _download_and_encode_image(self, image_url: str) -> tuple[str, str]:
        """
        下载图片并编码为base64
        
        Args:
            image_url: 图片URL
            
        Returns:
            (base64编码的图片字符串, MIME类型) 元组，失败返回(None, None)
        """
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            image_data = response.content
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # 根据URL或Content-Type确定MIME类型
            content_type = response.headers.get('Content-Type', '')
            if 'image/png' in content_type or image_url.lower().endswith('.png'):
                mime_type = 'image/png'
            elif 'image/jpeg' in content_type or 'image/jpg' in content_type or image_url.lower().endswith(('.jpg', '.jpeg')):
                mime_type = 'image/jpeg'
            elif 'image/gif' in content_type or image_url.lower().endswith('.gif'):
                mime_type = 'image/gif'
            elif 'image/webp' in content_type or image_url.lower().endswith('.webp'):
                mime_type = 'image/webp'
            else:
                # 默认使用jpeg
                mime_type = 'image/jpeg'
            
            return image_base64, mime_type
        except Exception as e:
            print(f"下载图片失败: {image_url}, 错误: {e}")
            return None, None
    
    def _call_qwen_vision(self, prompt: str, image_base64: str, mime_type: str = "image/jpeg") -> Dict[str, Any]:
        """
        调用Qwen视觉模型，超时或网络异常时自动重试。
        
        Args:
            prompt: 提示词
            image_base64: base64编码的图片
            mime_type: 图片MIME类型
            
        Returns:
            API响应结果
        """
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": "qwen-vl-max",  # 使用Qwen视觉模型
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            "max_tokens": 2000,
        }
        
        max_retries = 3
        base_wait = 10  # 首次失败后等待秒数，后续指数递增
        
        for attempt in range(max_retries):
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=60)
                response.raise_for_status()
                return response.json()
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                if attempt < max_retries - 1:
                    wait_sec = base_wait * (2 ** attempt)
                    print(f"调用Qwen API超时/连接异常，{wait_sec}s 后重试 ({attempt + 1}/{max_retries}): {e}")
                    time.sleep(wait_sec)
                else:
                    print(f"调用Qwen API失败（已重试 {max_retries} 次）: {e}")
                    return {}
            except Exception as e:
                print(f"调用Qwen API失败: {e}")
                return {}
        return {}
    
    def _parse_qwen_response(self, response: Dict[str, Any]) -> str:
        """
        解析Qwen API响应
        
        Args:
            response: API响应
            
        Returns:
            解析后的文本内容
        """
        try:
            return response.get("choices", [{}])[0].get("message", {}).get("content", "")
        except (KeyError, IndexError):
            return ""
    
    def _compare_dates_within_one_day(self, date1_str: str, date2_str: str) -> bool:
        """
        比较两个日期字符串，判断是否相差在1天之内（包括同一天）
        
        Args:
            date1_str: 第一个日期字符串（YYYY-MM-DD格式）
            date2_str: 第二个日期字符串（YYYY-MM-DD格式）
            
        Returns:
            如果日期差在1天之内返回True，否则返回False
        """
        try:
            date1 = datetime.strptime(date1_str, "%Y-%m-%d").date()
            date2 = datetime.strptime(date2_str, "%Y-%m-%d").date()
            delta = abs((date1 - date2).days)
            return delta <= 1
        except (ValueError, AttributeError):
            # 如果日期格式不正确，返回False
            return False
    
    def _perform_all_checks(self, record: TransactionRecord, image_base64: str, mime_type: str) -> tuple[List[AuditCheckResult], Dict[str, Any]]:
        """
        执行所有检查项（合并为一次API调用）
        
        Args:
            record: 交易记录
            image_base64: base64编码的图片
            mime_type: 图片MIME类型
            
        Returns:
            (检查结果列表, LLM返回的完整原始数据) 元组
        """
        transaction_type_cn = "入金" if record.type == TransactionType.DEPOSIT else "提现"
        
        # 获取交易明细匹配的prompt（由子类实现）
        transaction_date_match_prompt, transaction_info_match_prompt = self._get_transaction_match_prompts(record)
        
        # 合并所有检查的prompt
        prompt = f"""请仔细分析这张截图，完成以下4项检查：

【检查1：交易所记录验证】
判断截图是否来自交易所的{transaction_type_cn}记录页面。
要求：
- 截图应该显示交易所的{transaction_type_cn}记录
- 应该能看到交易所的界面元素（如交易所logo、导航栏、交易记录列表等）
- 应该能看到{transaction_type_cn}相关的信息

【检查2：交易所身份验证】
检查截图中是否有足够证据证明截图来自交易所"{record.exchange_name}"。
要求：
- 不要求必须有URL，只要有足够证据证明截图和交易所名称一致即可
- 可以接受的证据包括但不限于：
  * 浏览器地址栏中的URL（如果可见），URL应该与交易所名称匹配（例如，如果交易所是Binance，URL应该包含binance相关域名）
  * 交易所的logo或品牌标识
  * 交易所的名称文字
  * 交易所特有的界面元素或设计风格
- 只要能从截图中找到任何能够证明这是"{record.exchange_name}"交易所的证据即可，不要求所有证据都存在

【检查3：交易日期匹配】
{transaction_date_match_prompt}

【检查4：其他交易信息匹配】
{transaction_info_match_prompt}

请用JSON格式回复，格式如下：
{{
    "is_exchange_record": {{
        "result": true/false,
        "reason": "判断理由",
        "confidence": 0.0-1.0之间的置信度
    }},
    "exchange_verification": {{
        "result": true/false,
        "detected_url": "检测到的URL（如果有，可选）",
        "detected_evidence": "检测到的其他证据（如logo、交易所名称、界面元素等，如果有）",
        "reason": "判断理由（说明找到了哪些证据证明截图来自{record.exchange_name}交易所，不要求必须有URL）",
        "confidence": 0.0-1.0之间的置信度
    }},
    "transaction_date_match": {{
        "result": true/false,
        "detected_date": "检测到的日期（如果有）",
        "reason": "判断理由（说明截图中的日期是否与提交数据中的日期匹配）",
        "confidence": 0.0-1.0之间的置信度
    }},
    "transaction_info_match": {{
        "result": true/false,
        "detected_info": {{
            "token": "检测到的币种（如果有）",
            "amount": "检测到的金额（如果有）",
            "network": "检测到的网络（如果有）",
            "address": "检测到的地址（如果有）",
            "tx_hash": "检测到的交易哈希（如果有）"
        }},
        "reason": "判断理由（说明截图中的其他交易信息是否与提交数据匹配）",
        "confidence": 0.0-1.0之间的置信度
    }}
}}"""
        
        # 调用一次API
        response = self._call_qwen_vision(prompt, image_base64, mime_type)
        content = self._parse_qwen_response(response)
        
        # 解析所有检查结果
        checks, llm_raw_data = self._parse_all_checks_response(content, record)
        
        return checks, llm_raw_data
    
    @abstractmethod
    def _get_transaction_match_prompts(self, record: TransactionRecord) -> tuple[str, str]:
        """
        获取交易明细匹配的prompt（由子类实现）
        
        Args:
            record: 交易记录
            
        Returns:
            (交易日期匹配prompt, 其他交易信息匹配prompt) 元组
        """
        pass
    
    def _parse_all_checks_response(self, content: str, record: TransactionRecord) -> tuple[List[AuditCheckResult], Dict[str, Any]]:
        """
        解析包含所有检查结果的响应
        
        Args:
            content: API返回的内容
            record: 交易记录（用于错误提示）
            
        Returns:
            (检查结果列表, LLM返回的完整原始数据) 元组
        """
        checks = []
        
        # 尝试提取JSON（可能包含markdown代码块）
        # 先尝试移除markdown代码块标记
        content_clean = content
        if "```json" in content:
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                content_clean = json_match.group(1)
        elif "```" in content:
            json_match = re.search(r'```\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                content_clean = json_match.group(1)
        
        # 尝试直接解析
        data = None
        llm_raw_data = {}  # 初始化LLM原始数据
        
        try:
            data = json.loads(content_clean)
            llm_raw_data = data  # 保存解析到的完整数据
        except json.JSONDecodeError:
            # 如果直接解析失败，尝试用正则提取JSON对象
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}[^{}]*)*\}', content_clean, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                    llm_raw_data = data  # 保存解析到的完整数据
                except json.JSONDecodeError:
                    pass
        
        if data:
            try:
                # 调试：打印解析后的数据结构（仅前500字符）
                print(f"[调试] 解析到的JSON数据: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
                
                # 解析检查1：交易所记录验证
                check1_data = data.get("is_exchange_record", {})
                if isinstance(check1_data, dict):
                    result_value = check1_data.get("result", False)
                    if isinstance(result_value, str):
                        result_value = result_value.lower() in ("true", "1", "yes", "pass")
                    result1 = AuditResult.PASS if result_value else AuditResult.FAIL
                    reason1 = check1_data.get("reason") or check1_data.get("判断理由") or "未提供理由"
                    checks.append(AuditCheckResult(
                        check_name=self.CHECK_IS_EXCHANGE_RECORD,
                        result=result1,
                        reason=reason1,
                        confidence=check1_data.get("confidence", 0.5),
                        llm_response=check1_data,  # 保存LLM返回的完整原始数据
                    ))
                else:
                    checks.append(AuditCheckResult(
                        check_name=self.CHECK_IS_EXCHANGE_RECORD,
                        result=AuditResult.UNKNOWN,
                        reason="无法解析is_exchange_record结果",
                    ))
                
                # 解析检查2：交易所身份验证
                check2_data = data.get("exchange_verification", {})
                if isinstance(check2_data, dict):
                    result_value = check2_data.get("result", False)
                    if isinstance(result_value, str):
                        result_value = result_value.lower() in ("true", "1", "yes", "pass")
                    result2 = AuditResult.PASS if result_value else AuditResult.FAIL
                    reason2 = check2_data.get("reason") or check2_data.get("判断理由") or "未提供理由"
                    
                    # 收集所有检测到的证据
                    evidence_parts = []
                    detected_url = check2_data.get("detected_url") or check2_data.get("检测到的URL") or ""
                    if detected_url:
                        evidence_parts.append(f"URL: {detected_url}")
                    
                    detected_evidence = check2_data.get("detected_evidence") or check2_data.get("检测到的其他证据") or ""
                    if detected_evidence:
                        evidence_parts.append(f"其他证据: {detected_evidence}")
                    
                    if evidence_parts:
                        reason2 = f"{reason2} ({', '.join(evidence_parts)})"
                    
                    checks.append(AuditCheckResult(
                        check_name=self.CHECK_EXCHANGE_VERIFICATION,
                        result=result2,
                        reason=reason2,
                        confidence=check2_data.get("confidence", 0.5),
                        llm_response=check2_data,  # 保存LLM返回的完整原始数据
                    ))
                else:
                    checks.append(AuditCheckResult(
                        check_name=self.CHECK_EXCHANGE_VERIFICATION,
                        result=AuditResult.UNKNOWN,
                        reason="无法解析exchange_verification结果",
                    ))
                
                # 解析检查3：交易日期匹配
                check3_data = data.get("transaction_date_match", {})
                if isinstance(check3_data, dict):
                    result_value = check3_data.get("result", False)
                    if isinstance(result_value, str):
                        result_value = result_value.lower() in ("true", "1", "yes", "pass")
                    
                    reason3 = check3_data.get("reason") or check3_data.get("判断理由") or "未提供理由"
                    detected_date = check3_data.get("detected_date") or check3_data.get("检测到的日期")
                    
                    # 后处理：如果 detected_date 存在且与 record.date 相差在1天之内，强制设为 true
                    original_result = result_value  # 保存原始结果
                    if detected_date and detected_date != "无法识别":
                        try:
                            # 验证日期格式是否为 YYYY-MM-DD
                            datetime.strptime(detected_date, "%Y-%m-%d")
                            if self._compare_dates_within_one_day(detected_date, record.date):
                                # 日期相差在1天之内，强制设为 true
                                result_value = True
                                if not original_result:  # 如果原来 LLM 返回的是 false，添加修正说明
                                    reason3 = f"{reason3} [代码后处理：检测到日期 {detected_date} 与提交日期 {record.date} 相差在1天之内，已自动修正为匹配]"
                        except ValueError:
                            # detected_date 格式不正确，保持原结果
                            pass
                    
                    result3 = AuditResult.PASS if result_value else AuditResult.FAIL
                    if detected_date:
                        reason3 = f"{reason3} (检测到的日期: {detected_date})"
                    checks.append(AuditCheckResult(
                        check_name=self.CHECK_TRANSACTION_DATE_MATCH,
                        result=result3,
                        reason=reason3,
                        confidence=check3_data.get("confidence", 0.5),
                        llm_response=check3_data,  # 保存LLM返回的完整原始数据
                    ))
                else:
                    checks.append(AuditCheckResult(
                        check_name=self.CHECK_TRANSACTION_DATE_MATCH,
                        result=AuditResult.UNKNOWN,
                        reason="无法解析transaction_date_match结果",
                    ))
                
                # 解析检查4：其他交易信息匹配
                check4_data = data.get("transaction_info_match", {})
                if isinstance(check4_data, dict):
                    result_value = check4_data.get("result", False)
                    if isinstance(result_value, str):
                        result_value = result_value.lower() in ("true", "1", "yes", "pass")
                    result4 = AuditResult.PASS if result_value else AuditResult.FAIL
                    reason4 = check4_data.get("reason") or check4_data.get("判断理由") or "未提供理由"
                    detected_info = check4_data.get("detected_info") or check4_data.get("检测到的信息") or {}
                    if detected_info:
                        info_parts = [f"{k}: {v}" for k, v in detected_info.items() if v]
                        if info_parts:
                            reason4 = f"{reason4} (检测到的信息: {', '.join(info_parts)})"
                    checks.append(AuditCheckResult(
                        check_name=self.CHECK_TRANSACTION_INFO_MATCH,
                        result=result4,
                        reason=reason4,
                        confidence=check4_data.get("confidence", 0.5),
                        llm_response=check4_data,  # 保存LLM返回的完整原始数据
                    ))
                else:
                    checks.append(AuditCheckResult(
                        check_name=self.CHECK_TRANSACTION_INFO_MATCH,
                        result=AuditResult.UNKNOWN,
                        reason="无法解析transaction_info_match结果",
                    ))
                
                return checks, data  # 返回检查结果和完整的LLM原始数据
                
            except Exception as e:
                print(f"[错误] 解析检查结果时出错: {e}")
        
        # 如果无法解析JSON，创建未知状态的检查结果
        if not checks:
            print(f"[警告] 无法从API响应中提取JSON，原始内容: {content[:500]}")
            for check_name in [
                self.CHECK_IS_EXCHANGE_RECORD,
                self.CHECK_EXCHANGE_VERIFICATION,
                self.CHECK_TRANSACTION_DATE_MATCH,
                self.CHECK_TRANSACTION_INFO_MATCH,
            ]:
                checks.append(AuditCheckResult(
                    check_name=check_name,
                    result=AuditResult.UNKNOWN,
                    reason=f"无法解析API响应: {content[:200]}",
                ))
            # 如果无法解析，保存原始文本内容
            llm_raw_data = {"raw_content": content}
        
        return checks, llm_raw_data
