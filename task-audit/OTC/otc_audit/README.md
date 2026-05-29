# OTC 截图识别模块（otc_audit）

本目录负责 **OTC 地址截图的识别阶段（detect）**，包含：

- 从 `data_submission` 中抽取截图 URL；
- 调用 Qwen 视觉模型对截图做图片质量检查和字段提取；
- 输出结构化的识别结果，供后续评级模块使用。

## 1. 核心数据模型

文件：`models.py`

- `OTCSubmission`
  - `submission_id`: 提交 ID
  - `screenshot_url`: 截图 URL
  - `chain`: 报送链名（来自 `data_submission.data.chain`，原始值）
  - `address`: 报送地址（来自 `data_submission.data.address`）
  - `otc_desk`: 报送 OTC 名称（来自 `data_submission.data.otcDesk`）
  - `raw_data`: 原始 DB 记录（包含 `data_submission` 等）

- `OTCAuditResult`
  - `image_quality`：
    - `clear`: 是否清晰可辨
    - `tampered`: 是否存在明显 PS/篡改痕迹
    - `text_readable`: 文字是否完整可读
    - `notes`: 质量说明
  - `extracted`：
    - `chain`: 标准化链名（如 `ethereum_mainnet`、`tron_mainnet` 等，或 `null`）
    - `address`: 截图中识别到的地址
    - `entities`: OTC 实体名称/品牌
    - `labels`: 对实体的标签（如 `Crypto OTC`、`Exchange` 等）
    - `website_link`: 网站链接（http/https 开头），若无则 `null`
    - `txid`: 截图中识别的交易哈希（可为空，后续评级阶段会用 DB 中的 hash 覆盖）
    - `screenshot_link`: 截图 URL（原样回填）
    - `trace_type`: 当识别到 `txid` 时，判断该截图更像是 `deposit` / `withdrawal` / `unknown`；若未识别到 `txid`，则为 `null`
  - `extensions`：
    - 可包含：`phone`、`country`、`city`、`fiat`、`token` 等额外结构化信息
  - `raw_llm_response`: Qwen 返回的原始 JSON
  - `error`: 错误说明（如无法下载截图、JSON 无法解析等）

## 2. Qwen 审核器

文件：`otc_qwen_auditor.py`

- `OTCQwenAuditor`：
  - 从 `OTC/.env` 读取：
    - `QWEN_API_KEY`
    - `QWEN_BASE_URL`
  - 下载 `OTCSubmission.screenshot_url` 指向的图片，并转为 base64；
  - 构造提示词 `_build_prompt(submission)`：
    - 告诉模型你是 OTC 截图审核专家；
    - 提供报送的 `data.chain/address/otcDesk` 作为补充信息；
    - 要求模型输出固定的 JSON 字段：
      - 图片质量：`image_quality_clear/tampered/text_readable/notes`
      - 关键字段：`chain/address/entities/labels/website_link/txid`
      - 扩展字段：`extensions`（包含 phone/country/city/fiat/token 等）
      - `chain` 需综合地址格式（如 `TVyXUMypPfHD17AvwgSxBTSbpaDTRGWRrz` → TRON）、token 网络标记、浏览器域名等信息来判断
  - `_call_qwen` 调用接口 `/chat/completions`，模型默认 `qwen-vl-max`；
  - `_parse_json` 负责从文本中提取出 JSON；
  - `_fill_result` 将 LLM JSON 原样拷贝到 `OTCAuditResult` 的对应字段。

## 3. 使用方式（通常通过 `OTC/main_from_db.py` 调用）

本目录通常不单独执行，而是由 `OTC/main_from_db.py` 驱动：

- `main_from_db.py` 会：
  - 用 `SubmissionDBClient` 拉取 `submission_id + data_submission`；
  - 解析出截图 URL 创建 `OTCSubmission`；
  - 调用 `OTCQwenAuditor.audit(submission)` 获得 `OTCAuditResult`；
  - 汇总写入：`OTC/output/otc_audit/otc_audit_results.json`。

**一键串联**（识别 → 评级 → 交付 CSV）：在仓库根目录执行 `python -m OTC.run_all`。  
评级阶段会先做 txid/address 去重，再按图片质量、字段完整性、与 DB 真值一致性、hash 合法性打分；通过后写回 DB 并生成 `output/output_rating/rating_results_*.json` 与 `output/delivery/` 下 4 分/5 分 CSV。

如需在代码中直接使用识别能力，可以：

```python
from OTC.otc_audit.models import OTCSubmission
from OTC.otc_audit.otc_qwen_auditor import OTCQwenAuditor

sub = OTCSubmission(
    submission_id="test",
    screenshot_url="https://...",
    chain="ethereum",
    address="0x...",
    otc_desk="Some OTC",
    raw_data={},
)

auditor = OTCQwenAuditor()
result = auditor.audit(sub)
print(result.to_dict())