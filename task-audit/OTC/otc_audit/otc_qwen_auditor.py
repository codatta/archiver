"""
OTC 交易所截图审核 - Qwen 视觉模型
读取 data_submission 中的截图 URL，进行：图片质量检查、关键字段提取、上下文分析。
"""

from __future__ import annotations

import base64
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests

from .models import OTCSubmission, OTCAuditResult

try:
    from dotenv import load_dotenv
    _otc_root = Path(__file__).resolve().parents[1]
    _env = _otc_root / ".env"
    if _env.exists():
        load_dotenv(_env)
except Exception:
    pass


class OTCQwenAuditor:
    """使用 Qwen 视觉模型审核 OTC 截图：质量检查 + 字段提取 + 上下文分析"""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: str = "qwen-vl-max"):
        self.api_key = api_key or os.getenv("QWEN_API_KEY")
        self.base_url = base_url or os.getenv(
            "QWEN_BASE_URL",
            "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        )
        self.model = model
        if not self.api_key:
            raise ValueError("QWEN_API_KEY 未设置，请在 OTC/.env 中配置")

    def audit(self, submission: OTCSubmission) -> OTCAuditResult:
        """对一条提交进行截图审核，返回结构化结果。"""
        result = OTCAuditResult(submission_id=submission.submission_id)
        result.screenshot_link = submission.screenshot_url
        if not submission.screenshot_url:
            result.error = "缺少截图 URL"
            return result

        image_b64, mime = self._download_image(submission.screenshot_url)
        if not image_b64:
            result.error = "无法下载截图"
            return result

        prompt = self._build_prompt(submission)
        resp = self._call_qwen(prompt, image_b64, mime)
        content = (resp.get("choices") or [{}])[0].get("message", {}).get("content", "")
        parsed = self._parse_json(content)
        if parsed:
            result.raw_llm_response = parsed
            self._fill_result(result, parsed)
        else:
            result.error = "LLM 返回无法解析为 JSON"
        return result

    def _download_image(self, url: str):
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            b64 = base64.b64encode(r.content).decode("utf-8")
            ct = (r.headers.get("Content-Type") or "").lower()
            mime = "image/png" if "png" in ct or url.lower().endswith(".png") else "image/jpeg"
            return b64, mime
        except Exception as e:
            print(f"[OTC] 下载图片失败 {url}: {e}")
            return None, None

    def _build_prompt(self, submission: OTCSubmission) -> str:
        """
        根据当前 submission 构造审核提示词。

        目标：
        - 图片质量检查
        - 规范化链名 chain
        - address / entities / labels / website_link / txid / extensions
        """
        user_chain = submission.chain or "未知"
        user_address = submission.address or "未知"
        user_otc = submission.otc_desk or "未知"

        return f"""你是一名 OTC 交易所截图审核专家。现在要审核一张截图，并从中提取关键信息。
用户在 data_submission 中报送的基础字段仅供参考（截图识别结果才是准绳）：
- 报送链名称 data.chain = {user_chain}
- 报送地址 data.address = {user_address}
- 报送 OTC 商家 data.otcDesk = {user_otc}

请根据提供的截图，严格按以下三项进行分析，并只输出一个 JSON 对象，不要输出其他文字。

## 一、图片质量检查
- image_quality_clear: 图片是否清晰可辨（true/false）
- image_quality_tampered: 是否存在明显的 PS/篡改痕迹（true/false）
- image_quality_text_readable: 文字是否完整可读（true/false）
- image_quality_notes: 简要说明（字符串）

## 二、关键字段提取（从截图中识别，无法识别则填 null）
- chain: 截图中体现的区块链网络。请综合利用一切你能看到的信号来判断，包括但不限于：
  - 地址前缀和格式（例如 0x... 通常为 EVM 地址，T 开头、长度类似 TVyXUMypPfHD17AvwgSxBTSbpaDTRGWRrz 的为 TRON 地址，bc1/1/3... 为 Bitcoin 等等）
  - Token 名称/网络标识（如 “USDT TRC20”、“Tether ERC-20”、“BSC-USDT” 等）
  - 网页或 App 上显示的网络标签/Logo（如 ETH/BSC/TRON 等图标或文字）
  - 区块链浏览器的域名或路径（如 etherscan.io、tronscan.org、bscscan.com、arbiscan.io 等）
  - 其它任何能指示链类型的文字或 UI 元素
  先按人类可读形式识别（如 ethereum、tron、bnb、bitcoin、solana、polygon、arbitrum、optimism、avalanche、base、litecoin），
  然后将其映射为以下枚举之一输出：
  - ethereum_mainnet
  - tron_mainnet
  - bnb_chain_mainnet
  - bitcoin_mainnet
  - solana_mainnet
  - polygon_mainnet
  - arbitrum_one
  - optimism_mainnet
  - avalanche_c_chain
  - base_mainnet
  - litecoin_mainnet
  如果无法判断链类型，则 chain 输出 null。
- address: 截图中出现的加密货币地址（可见部分足够唯一即可，如有隐藏中间字符则保留原样；无法识别填 null）
- entities: OTC 商家名称/品牌（如截图中有交易所名/OTC 名/个人昵称等用于标识商家的文字，则填入）
- labels: 对该实体的标签。示例：当用户信息中包含 “Crypto OTC | Manager Cheques | Investments via Crypto”，
  用户名为 @Darya_Stabit，头像含 “stabit” 标识时，可认为该用户是 OTC 相关服务，labels 输出 \"Crypto OTC\"。
  其他类似场景也请根据上下文给出简短标签（如 \"P2P OTC\"、\"Exchange\"），无法判断填 null。
- website_link: 如果截图中存在网站链接或浏览器地址栏 URL，请输出 http(s) 开头的完整链接；如果没有可见链接则输出 null。
- txid: 截图中识别到的链上交易哈希（如 0x 开头的 64 位十六进制，或比特币/其他链标准哈希），无法识别填 null。
- trace_type: 仅当 txid 可识别时再判断该截图更像“入金”还是“提现”场景：
  - deposit：页面/聊天/订单语义更像“向某地址付款/充值/入金/发送到对方地址”
  - withdrawal：页面/记录语义更像“从平台/商家向外转出/提现到某地址”
  - unknown：无法判断
  若 txid 为 null，则 trace_type 也输出 null。

## 三、扩展信息
- extensions: JSON 对象，包含你能从截图中额外提取到的结构化信息，例如：
  - phone: 电话号码（如有）
  - country: 国家（如通过语言/手机号区号等能较为明确判断）
  - city: 城市（如有）
  - fiat: 法币币种（如 RUB、USD、EUR 等）
  - token: 代币符号（如 USDT、BTC 等）
  以上字段均为可选；如果没有任何额外信息，extensions 输出 {{}}。

请直接输出一个 JSON 对象（不要用 markdown 代码块包裹，也不要输出解释性文字），
字段必须包含且仅包含以下键（值按实际识别填写）：
{{
  "image_quality_clear": true 或 false,
  "image_quality_tampered": true 或 false,
  "image_quality_text_readable": true 或 false,
  "image_quality_notes": "字符串，简单说明你对图片质量的判断理由",
  "chain": "上述枚举之一，或 null",
  "address": "截图里看到的地址原文，无法识别填 null",
  "entities": "OTC 实体名称（如有，否则 null）",
  "labels": "针对实体的标签（如 Crypto OTC/P2P OTC/Exchange 等，如无则 null）",
  "website_link": "http(s) 开头的链接，如无法识别则 null",
  "txid": "识别到的交易哈希，如无法识别则 null",
  "trace_type": "deposit/withdrawal/unknown 或 null（当 txid 为 null 时必须为 null）",
  "extensions": {{
    "phone": "如有电话号码，否则可省略或设为 null",
    "country": "如能较为明确判断的国家，否则可省略或设为 null",
    "city": "如能判断的城市，否则可省略或设为 null",
    "fiat": "如 RUB/USD/EUR 等，如无则可省略或设为 null",
    "token": "如 USDT/BTC 等，如无则可省略或设为 null"
  }}
}}
"""

    def _call_qwen(self, prompt: str, image_b64: str, mime: str) -> Dict[str, Any]:
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image_b64}"}},
                    {"type": "text", "text": prompt},
                ],
            }],
            "max_tokens": 2000,
        }
        for attempt in range(3):
            try:
                r = requests.post(url, json=payload, headers=headers, timeout=90)
                r.raise_for_status()
                return r.json()
            except (requests.Timeout, requests.ConnectionError) as e:
                if attempt < 2:
                    time.sleep(8 * (2 ** attempt))
                    print(f"[OTC] Qwen 调用失败，重试 {attempt + 1}/3: {e}")
                else:
                    print(f"[OTC] Qwen 调用最终失败: {e}")
                    return {}
            except Exception as e:
                print(f"[OTC] Qwen 异常: {e}")
                return {}
        return {}

    @staticmethod
    def _parse_json(content: str) -> Optional[Dict[str, Any]]:
        if not content:
            return None
        text = content.strip()
        for pattern in (r"```json\s*(\{.*?\})\s*```", r"```\s*(\{.*?\})\s*```"):
            m = re.search(pattern, text, re.DOTALL)
            if m:
                text = m.group(1)
                break
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        m = re.search(r"\{[^{}]*(?:\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}[^{}]*)*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
        return None

    @staticmethod
    def _normalize_chain(raw_chain: Optional[str]) -> Optional[str]:
        if not raw_chain:
            return None
        c = str(raw_chain).strip().lower()
        mapping = {
            "eth": "ethereum_mainnet",
            "ethereum": "ethereum_mainnet",
            "erc20": "ethereum_mainnet",
            "tron": "tron_mainnet",
            "trx": "tron_mainnet",
            "bnb": "bnb_chain_mainnet",
            "bsc": "bnb_chain_mainnet",
            "binance smart chain": "bnb_chain_mainnet",
            "btc": "bitcoin_mainnet",
            "bitcoin": "bitcoin_mainnet",
            "sol": "solana_mainnet",
            "solana": "solana_mainnet",
            "polygon": "polygon_mainnet",
            "matic": "polygon_mainnet",
            "arb": "arbitrum_one",
            "arbitrum": "arbitrum_one",
            "op": "optimism_mainnet",
            "optimism": "optimism_mainnet",
            "avax": "avalanche_c_chain",
            "avalanche": "avalanche_c_chain",
            "base": "base_mainnet",
            "ltc": "litecoin_mainnet",
            "litecoin": "litecoin_mainnet",
        }
        if c in mapping:
            return mapping[c]
        return None

    @staticmethod
    def _fill_result(result: OTCAuditResult, raw: Dict[str, Any]) -> None:
        """
        将 LLM 返回的 JSON 原样拷贝到结果结构中（除 image_quality_notes 做 str 处理），
        以便你在提示词里直接控制键名和取值。
        """
        # 图片质量相关字段保持不变
        result.image_quality_clear = raw.get("image_quality_clear")
        result.image_quality_tampered = raw.get("image_quality_tampered")
        result.image_quality_text_readable = raw.get("image_quality_text_readable")
        result.image_quality_notes = str(raw.get("image_quality_notes") or "")

        # 其余字段直接从 LLM JSON 中拷贝，对应你在提示词中定义的键
        result.chain = raw.get("chain")
        result.address = raw.get("address")
        result.entities = raw.get("entities")
        result.labels = "otc_desk"
        result.website_link = raw.get("website_link")
        result.txid = raw.get("txid")
        # trace_type 仅在识别到 txid 时才有意义
        trace_type = raw.get("trace_type")
        if raw.get("txid"):
            result.trace_type = trace_type
        else:
            result.trace_type = None

        ex = raw.get("extensions") or {}
        if isinstance(ex, dict):
            result.extensions = ex
        else:
            result.extensions = {"value": ex}
