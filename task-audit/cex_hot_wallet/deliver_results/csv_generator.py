"""
CSV交付数据生成器
处理审核通过的记录，生成CSV格式的交付数据
"""
import json
import csv
import os
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
from collections import Counter

import pymysql
from pymysql.cursors import DictCursor

from utils import load_json, build_submissions_map, save_json
from network_mapping import get_enum_from_network


class CSVGenerator:
    """CSV交付数据生成器"""
    
    # ========= 数据源相关 =========
    
    def _get_db_connection(self):
        """获取用于交付生成的数据库连接（与 main_audit 共享同一套 DB_* 配置）。"""
        host = os.getenv("DB_HOST", "localhost")
        port = int(os.getenv("DB_PORT", "3306"))
        user = os.getenv("DB_USER", "")
        password = os.getenv("DB_PASSWORD", "")
        database = os.getenv("DB_NAME", "")
        
        if not user or not database:
            raise ValueError(
                "数据库配置不完整，请在环境变量中设置 DB_USER 和 DB_NAME "
                "(必要时还需要 DB_PASSWORD、DB_HOST、DB_PORT)"
            )
        
        return pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            cursorclass=DictCursor,
            autocommit=False,
            charset="utf8mb4",
        )
    
    def _fetch_rated_rows_from_db(self) -> List[Dict]:
        """
        从数据库读取已评级（4/5分）的记录，用于生成交付 CSV。
        
        SQL 来源：
        - 优先使用环境变量 DB_DELIVER_SQL
        - 如未设置，则使用内置默认 SQL（适配当前 CEX Hot Wallet 任务）
        
        要求 SQL 至少返回：
        - submission_id
        - data_submission（JSON 字符串，与 raw_data/submissions.json 中的 data_submission 一致）
        - rating（整数，且保证为 4 或 5）
        """
        sql = os.getenv(
            "DB_DELIVER_SQL",
            (
                "select submission_id, "
                "       data_submission ->> '$.data' as data_submission, "
                "       result as rating "
                "from cfp_task_submission "
                "where frontier_id in ('8114254168500106625') "
                "  and template_id in ('AIRDROP_CEX_HOT_WALLET_DEPOSIT', 'AIRDROP_CEX_HOT_WALLET_WITHDRAW') "
                "  and status = 'ADOPT'"
            ),
        )
        
        rows: List[Dict] = []
        conn = self._get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                rows = list(cursor.fetchall())
        finally:
            conn.close()
        
        # 只保留 rating 为 4 或 5 的记录，防止 SQL 被意外改坏
        filtered: List[Dict] = []
        for row in rows:
            try:
                rating_val = int(row.get("rating", 0))
            except (TypeError, ValueError):
                continue
            if rating_val in (4, 5):
                filtered.append(row)
        
        return filtered
    
    def _collect_screenshot_urls(self, submission_data: Dict) -> str:
        """
        收集所有截图URL，并以JSON字符串形式返回
        
        Args:
            submission_data: 原始提交数据
            
        Returns:
            JSON字符串，key 为原始数据中的字段名，value 为对应的URL
        """
        links: Dict[str, str] = {}
        
        # 收集所有可能的截图URL字段，key 与原始数据字段保持一致
        url_fields = [
            "explorer_screenshot_url",
            "exchange_ui_screenshot_url",
            "outgoing_tx_screenshot_url",
            "outgoing_transaction_screenshot_url",
        ]
        
        for field in url_fields:
            url = submission_data.get(field)
            if isinstance(url, str) and url.strip():
                links[field] = url.strip()
        
        # 返回JSON字符串（如果没有任何截图，则返回空字符串）
        return json.dumps(links, ensure_ascii=False) if links else ""
    
    def _map_chain(self, network: str) -> str:
        """将原始 network 映射为标准链枚举值"""
        return get_enum_from_network(network)
    
    def _get_address(self, submission_data: Dict, trace_type: str) -> str:
        """根据交易类型获取地址"""
        trace_type_lower = trace_type.lower()
        if trace_type_lower == 'withdrawal':
            return submission_data.get('sender_address', '')
        elif trace_type_lower == 'deposit':
            return submission_data.get('outgoing_tx_to_address', '')
        return ''
    
    def _extract_token(self, submission_data: Dict) -> str:
        """提取token，优先使用token字段，否则从coin字段提取"""
        token = submission_data.get('token', '')
        if not token:
            coin = submission_data.get('coin', '')
            token = coin.split('-')[-1] if '-' in coin else coin
        return token
    
    def _build_extensions(
        self,
        submission_data: Dict,
        submission_id: str,
        trace_type: str,
        detected_date: Optional[str] = None,
    ) -> str:
        """构建extensions JSON字符串"""
        # 优先使用 UI 审核中解析出的 detected_date（已归一化为 YYYY-MM-DD），否则退回到原始提交日期
        date_value = detected_date or submission_data.get('date') or submission_data.get('transaction_date', '')
        extensions = {
            'date': date_value,
            'token': self._extract_token(submission_data),
            'amount': submission_data.get('amount', ''),
            'submission_id': submission_id
        }
        
        # 根据交易类型增加地址信息
        trace_type_lower = (trace_type or "").lower()
        if trace_type_lower == "deposit":
            # deposit：使用 to_address，命名为 deposit_address
            extensions["deposit_address"] = submission_data.get("to_address", "")
        elif trace_type_lower == "withdrawal":
            # withdrawal：使用 address，命名为 withdraw_address
            extensions["withdraw_address"] = submission_data.get("address", "")
        
        return json.dumps(extensions, ensure_ascii=False)
    
    def _build_csv_row(
        self,
        verification: Dict,
        submissions_map: Dict[str, Dict],
        detected_date: Optional[str] = None,
    ) -> Optional[Dict]:
        """构建单行CSV数据"""
        submission_id = verification.get("submission_id")
        trace_type = verification.get("type", "")
        
        submission_data = submissions_map.get(submission_id, {})
        if not submission_data:
            print(f"[警告] 未找到submission_id {submission_id} 的原始数据，跳过")
            return None
        
        # deposit 且没有 outgoing_tx_to_address 的记录直接丢弃
        if trace_type.lower() == 'deposit' and not submission_data.get('outgoing_tx_to_address'):
            print(f"[信息] submission_id {submission_id} 为 deposit 且无 outgoing_tx_to_address，跳过")
            return None
        
        return {
            'chain': self._map_chain(submission_data.get('network', '')),
            'address': self._get_address(submission_data, trace_type),
            'entities': submission_data.get('exchange_name', ''),
            'labels': 'Exchange Hot Wallet, CEX',
            'source_type': 'ground_truth',
            'website_link': '',
            'description': '',
            'provider': 'Codatta',
            'provider_source': 'User Report',
            'screenshot_link': self._collect_screenshot_urls(submission_data),
            'txid': submission_data.get('tx_hash', ''),
            'trace_type': trace_type,
            'extensions': self._build_extensions(submission_data, submission_id, trace_type, detected_date)
        }
    
    def _write_csv_file(self, csv_rows: List[Dict], output_path: Path, force_create: bool = False) -> None:
        """
        将CSV数据写入文件
        
        Args:
            csv_rows: CSV行数据列表
            output_path: 输出文件路径
            force_create: 即使没有数据行也创建文件（只写表头）
        """
        if not csv_rows and not force_create:
            return
        
        fieldnames = [
            'chain', 'address', 'entities', 'labels', 'source_type',
            'website_link', 'description', 'provider', 'provider_source',
            'screenshot_link', 'txid', 'trace_type', 'extensions'
        ]
        
        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            if csv_rows:
                writer.writerows(csv_rows)
    
    def _load_detected_date_map(self, comprehensive_results_path: Optional[str]) -> Dict[str, str]:
        """
        从综合审核结果中提取 UI 审核的 detected_date（transaction_date_match）
        
        Returns:
            {submission_id: detected_date} 映射（detected_date 期望为 YYYY-MM-DD）
        """
        if not comprehensive_results_path:
            return {}
        
        data = load_json(comprehensive_results_path)
        if not data:
            return {}
        
        detected_map: Dict[str, str] = {}
        for item in data.get("audit_results", []):
            sid = item.get("submission_id")
            ui_audit = item.get("ui_audit") or {}
            checks = ui_audit.get("checks") or []
            for chk in checks:
                if chk.get("check_name") == "transaction_date_match":
                    llm_resp = chk.get("llm_response") or {}
                    val = llm_resp.get("detected_date")
                    if isinstance(val, str) and val.strip():
                        detected_map[sid] = val.strip()
                    break
        return detected_map
    
    def generate_csv(
        self,
        rating_results_path: str,
        submissions_path: str,
        output_dir: Optional[str] = None,
        comprehensive_results_path: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        生成CSV交付数据，分别生成4分和5分的文件
        
        Args:
            rating_results_path: 评级结果文件路径（main_audit/rating_results.json）
            submissions_path: 原始提交数据文件路径
            output_dir: 输出目录路径（可选）
            
        Returns:
            包含两个文件路径的字典 {"rating_5": path, "rating_4": path}
        """
        # 读取评级结果
        rating_data = load_json(rating_results_path)
        if not rating_data:
            raise Exception(f"读取评级结果失败: {rating_results_path}")
        
        # 读取原始提交数据
        submissions = load_json(submissions_path)
        if not submissions:
            raise Exception(f"读取原始提交数据失败: {submissions_path}")
        
        # 构建 submission_id -> 原始提交数据 映射
        submissions_map = build_submissions_map(submissions)
        
        # 构建 submission_id -> detected_date 映射（来自 UI 审核）
        detected_date_map = self._load_detected_date_map(comprehensive_results_path)
        
        # 筛选评级为 4 或 5 分的记录
        rated_results = rating_data.get("rated_results", [])
        rating_5_results = [r for r in rated_results if r.get("rating") == 5]
        rating_4_results = [r for r in rated_results if r.get("rating") == 4]
        
        print(f"找到 {len(rating_5_results)} 条评级为 5 分的记录")
        print(f"找到 {len(rating_4_results)} 条评级为 4 分的记录")
        
        # 确定输出目录
        if not output_dir:
            rating_file = Path(rating_results_path)
            output_dir = rating_file.parents[1] / "deliver_results"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 准备CSV数据
        csv_rows_5 = []
        for rated in rating_5_results:
            sid = rated.get("submission_id")
            detected_date = detected_date_map.get(sid)
            row = self._build_csv_row(rated, submissions_map, detected_date)
            if row:
                csv_rows_5.append(row)
        
        csv_rows_4 = []
        skipped_4 = []
        for rated in rating_4_results:
            sid = rated.get("submission_id")
            detected_date = detected_date_map.get(sid)
            row = self._build_csv_row(rated, submissions_map, detected_date)
            if row:
                csv_rows_4.append(row)
            else:
                skipped_4.append(sid)
        
        # 生成两个CSV文件
        output_path_5 = output_dir / "delivery_results_rating_5.csv"
        output_path_4 = output_dir / "delivery_results_rating_4.csv"
        
        # 生成5分CSV文件
        if csv_rows_5:
            self._write_csv_file(csv_rows_5, output_path_5)
            print(f"成功生成 {len(csv_rows_5)} 条5分记录到: {output_path_5}")
        elif rating_5_results:
            # 有5分记录但被过滤，创建空文件
            self._write_csv_file([], output_path_5, force_create=True)
            print(f"找到 {len(rating_5_results)} 条5分记录，但均被过滤，已创建空CSV文件: {output_path_5}")
        else:
            self._write_csv_file([], output_path_5, force_create=True)
            print(f"没有评级为5分的记录，已创建空CSV文件: {output_path_5}")
        
        # 生成4分CSV文件
        if csv_rows_4:
            self._write_csv_file(csv_rows_4, output_path_4)
            print(f"成功生成 {len(csv_rows_4)} 条4分记录到: {output_path_4}")
        elif rating_4_results:
            # 有4分记录但被过滤，创建空文件
            self._write_csv_file([], output_path_4, force_create=True)
            print(f"找到 {len(rating_4_results)} 条4分记录，但均被过滤，已创建空CSV文件: {output_path_4}")
            if skipped_4:
                print(f"  被过滤的submission_id: {', '.join(skipped_4)}")
        else:
            self._write_csv_file([], output_path_4, force_create=True)
            print(f"没有评级为4分的记录，已创建空CSV文件: {output_path_4}")
        
        return {
            "rating_5": str(output_path_5),
            "rating_4": str(output_path_4)
        }
    
    def generate_csv_from_db(
        self,
        output_dir: Optional[str] = None,
        comprehensive_results_path: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        从数据库直接读取评级为 4 或 5 分的记录，生成交付 CSV。
        
        数据来源 SQL 由 DB_DELIVER_SQL 控制（或使用内置默认 SQL），
        不再依赖 main_audit/rating_results.json 和 raw_data/submissions.json。
        """
        rows = self._fetch_rated_rows_from_db()
        if not rows:
            raise Exception("从数据库未获取到任何 rating=4/5 的记录，请检查 DB_DELIVER_SQL 或数据状态。")
        
        print(f"从数据库获取到 {len(rows)} 条 rating=4/5 的记录")
        
        # 构造 submissions 列表以复用现有 _build_csv_row 逻辑
        submissions: List[Dict] = []
        for row in rows:
            sid = row.get("submission_id")
            data_submission = row.get("data_submission")
            if not sid or data_submission is None:
                continue
            submissions.append(
                {
                    "submission_id": sid,
                    "data_submission": data_submission,
                }
            )
        
        submissions_map = build_submissions_map(submissions)
        
        # 构建 submission_id -> detected_date 映射（仍然可以复用 UI 审核的日期）
        detected_date_map = self._load_detected_date_map(comprehensive_results_path)
        
        # 构造「伪 rated_results」，只保留需要的字段
        rating_5_results: List[Dict] = []
        rating_4_results: List[Dict] = []
        
        for row in rows:
            sid = row.get("submission_id")
            if not sid:
                continue
            try:
                rating_val = int(row.get("rating", 0))
            except (TypeError, ValueError):
                continue
            
            submission_data = submissions_map.get(sid, {})
            trace_type = submission_data.get("type", "")
            rated_item = {
                "submission_id": sid,
                "type": trace_type,
                "rating": rating_val,
            }
            
            if rating_val == 5:
                rating_5_results.append(rated_item)
            elif rating_val == 4:
                rating_4_results.append(rated_item)
        
        print(f"最终用于生成交付的记录：5分 {len(rating_5_results)} 条，4分 {len(rating_4_results)} 条")
        
        # 确定输出目录
        if not output_dir:
            # 与原有逻辑保持一致：默认放在 output/deliver_results
            base_dir = Path(__file__).parent.parent
            output_dir_path = base_dir / "output" / "deliver_results"
        else:
            output_dir_path = Path(output_dir)
        
        output_dir_path.mkdir(parents=True, exist_ok=True)
        
        # 准备 CSV 数据（与原逻辑一致）
        csv_rows_5: List[Dict] = []
        for rated in rating_5_results:
            sid = rated.get("submission_id")
            detected_date = detected_date_map.get(sid)
            row = self._build_csv_row(rated, submissions_map, detected_date)
            if row:
                csv_rows_5.append(row)
        
        csv_rows_4: List[Dict] = []
        skipped_4: List[str] = []
        for rated in rating_4_results:
            sid = rated.get("submission_id")
            detected_date = detected_date_map.get(sid)
            row = self._build_csv_row(rated, submissions_map, detected_date)
            if row:
                csv_rows_4.append(row)
            else:
                skipped_4.append(sid)
        
        # 按 address 去重：优先保留 submission_id 最小的（最早的提交）
        def deduplicate_by_address(rows: List[Dict]) -> tuple[List[Dict], List[Dict]]:
            """
            按 address 字段去重，保留 submission_id 最小的记录。
            
            Returns:
                (去重后的记录列表, 被过滤的重复记录列表)
            """
            address_map: Dict[str, Dict] = {}  # address -> row
            duplicates: List[Dict] = []
            
            for row in rows:
                address = row.get("address", "").strip().lower()
                if not address:
                    # 没有 address 的记录直接保留（不参与去重）
                    continue
                
                existing_row = address_map.get(address)
                if existing_row is None:
                    # 首次出现该 address，直接保留
                    address_map[address] = row
                else:
                    # 已存在该 address，比较 submission_id
                    existing_ext_str = existing_row.get("extensions", "")
                    current_ext_str = row.get("extensions", "")
                    
                    # 从 extensions JSON 中提取 submission_id
                    try:
                        existing_ext = json.loads(existing_ext_str) if existing_ext_str else {}
                        current_ext = json.loads(current_ext_str) if current_ext_str else {}
                        existing_id = existing_ext.get("submission_id", "")
                        current_id = current_ext.get("submission_id", "")
                        
                        if existing_id and current_id:
                            # 比较 submission_id（字符串比较，通常按时间戳排序，越小越早）
                            if current_id < existing_id:
                                # 当前记录的 submission_id 更小，替换
                                duplicates.append(existing_row)
                                address_map[address] = row
                            else:
                                # 已存在的记录 submission_id 更小，保留已存在的
                                duplicates.append(row)
                        else:
                            # 无法提取 submission_id，保留已存在的
                            duplicates.append(row)
                    except (json.JSONDecodeError, KeyError, TypeError):
                        # 解析失败，保留已存在的
                        duplicates.append(row)
            
            # 返回去重后的记录和所有重复记录
            return list(address_map.values()), duplicates
        
        # 对 5 分和 4 分分别去重
        csv_rows_5_unique, csv_rows_5_duplicates = deduplicate_by_address(csv_rows_5)
        csv_rows_4_unique, csv_rows_4_duplicates = deduplicate_by_address(csv_rows_4)
        
        if csv_rows_5_duplicates or csv_rows_4_duplicates:
            print(f"\n去重统计:")
            print(f"  5分: 原始 {len(csv_rows_5)} 条，去重后 {len(csv_rows_5_unique)} 条，重复 {len(csv_rows_5_duplicates)} 条")
            print(f"  4分: 原始 {len(csv_rows_4)} 条，去重后 {len(csv_rows_4_unique)} 条，重复 {len(csv_rows_4_duplicates)} 条")
        
        output_path_5 = output_dir_path / "delivery_results_rating_5.csv"
        output_path_4 = output_dir_path / "delivery_results_rating_4.csv"
        output_path_duplicates = output_dir_path / "delivery_results_duplicate.csv"
        
        # 生成 5 分文件（去重后）
        if csv_rows_5_unique:
            self._write_csv_file(csv_rows_5_unique, output_path_5)
            print(f"成功生成 {len(csv_rows_5_unique)} 条5分记录到: {output_path_5}")
        else:
            self._write_csv_file([], output_path_5, force_create=True)
            print(f"没有可用的5分记录，已创建空CSV文件: {output_path_5}")
        
        # 生成 4 分文件（去重后）
        if csv_rows_4_unique:
            self._write_csv_file(csv_rows_4_unique, output_path_4)
            print(f"成功生成 {len(csv_rows_4_unique)} 条4分记录到: {output_path_4}")
        else:
            self._write_csv_file([], output_path_4, force_create=True)
            if rating_4_results:
                print(f"找到 {len(rating_4_results)} 条4分记录，但均被过滤，已创建空CSV文件: {output_path_4}")
                if skipped_4:
                    print(f"  被过滤的submission_id: {', '.join(skipped_4)}")
            else:
                print(f"没有可用的4分记录，已创建空CSV文件: {output_path_4}")
        
        # 生成重复记录文件（包含所有被过滤的重复记录）
        all_duplicates = csv_rows_5_duplicates + csv_rows_4_duplicates
        if all_duplicates:
            self._write_csv_file(all_duplicates, output_path_duplicates)
            print(f"成功生成 {len(all_duplicates)} 条重复记录到: {output_path_duplicates}")
        else:
            self._write_csv_file([], output_path_duplicates, force_create=True)
            print(f"没有重复记录，已创建空CSV文件: {output_path_duplicates}")
        
        # 生成统计报告（Markdown 格式）
        report_path = output_dir_path / "delivery_statistics_report.md"
        self._generate_statistics_report(
            csv_rows_5_unique,
            csv_rows_4_unique,
            all_duplicates,
            csv_rows_5,
            csv_rows_4,
            report_path,
        )
        
        return {
            "rating_5": str(output_path_5),
            "rating_4": str(output_path_4),
            "duplicates": str(output_path_duplicates),
            "statistics_report": str(report_path),
        }
    
    def _generate_statistics_report(
        self,
        csv_rows_5_unique: List[Dict],
        csv_rows_4_unique: List[Dict],
        csv_rows_duplicates: List[Dict],
        csv_rows_5_original: List[Dict],
        csv_rows_4_original: List[Dict],
        report_path: Path,
    ) -> None:
        """
        生成交付结果统计报告（Markdown 格式）
        
        Args:
            csv_rows_5_unique: 5分去重后的记录
            csv_rows_4_unique: 4分去重后的记录
            csv_rows_duplicates: 所有重复记录
            csv_rows_5_original: 5分原始记录（去重前）
            csv_rows_4_original: 4分原始记录（去重前）
            report_path: 报告输出路径（.md 文件）
        """
        # 统计总体数据
        total_unique = len(csv_rows_5_unique) + len(csv_rows_4_unique)
        total_original = len(csv_rows_5_original) + len(csv_rows_4_original)
        total_duplicates = len(csv_rows_duplicates)
        deduplication_rate = (
            round(total_duplicates / total_original * 100, 2)
            if total_original > 0
            else 0.0
        )
        
        # 按链（chain）统计
        chain_counter_unique = Counter()
        chain_counter_5 = Counter()
        chain_counter_4 = Counter()
        chain_counter_duplicates = Counter()
        
        for row in csv_rows_5_unique:
            chain_counter_unique[row.get("chain", "unknown")] += 1
            chain_counter_5[row.get("chain", "unknown")] += 1
        for row in csv_rows_4_unique:
            chain_counter_unique[row.get("chain", "unknown")] += 1
            chain_counter_4[row.get("chain", "unknown")] += 1
        for row in csv_rows_duplicates:
            chain_counter_duplicates[row.get("chain", "unknown")] += 1
        
        # 按交易类型（trace_type）统计
        trace_type_counter_unique = Counter()
        trace_type_counter_5 = Counter()
        trace_type_counter_4 = Counter()
        trace_type_counter_duplicates = Counter()
        
        for row in csv_rows_5_unique:
            trace_type = row.get("trace_type", "unknown")
            trace_type_counter_unique[trace_type] += 1
            trace_type_counter_5[trace_type] += 1
        for row in csv_rows_4_unique:
            trace_type = row.get("trace_type", "unknown")
            trace_type_counter_unique[trace_type] += 1
            trace_type_counter_4[trace_type] += 1
        for row in csv_rows_duplicates:
            trace_type_counter_duplicates[row.get("trace_type", "unknown")] += 1
        
        # 按交易所（entities）统计
        entities_counter_unique = Counter()
        entities_counter_5 = Counter()
        entities_counter_4 = Counter()
        entities_counter_duplicates = Counter()
        
        for row in csv_rows_5_unique:
            entities = row.get("entities", "unknown")
            entities_counter_unique[entities] += 1
            entities_counter_5[entities] += 1
        for row in csv_rows_4_unique:
            entities = row.get("entities", "unknown")
            entities_counter_unique[entities] += 1
            entities_counter_4[entities] += 1
        for row in csv_rows_duplicates:
            entities_counter_duplicates[row.get("entities", "unknown")] += 1
        
        # 生成 Markdown 报告
        md_lines = [
            "# 交付结果统计报告",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            "",
            "## 📁 输出文件",
            "",
            "本次交付生成了以下文件：",
            "",
            "### 主要交付文件",
            "",
            "1. **[`delivery_results_rating_5.csv`](./delivery_results_rating_5.csv)** - 5分记录（去重后）",
            "   - 所有审核子项均通过的高置信度记录",
            "   - 建议作为「高置信度、可直接交付需求方使用」的地址列表",
            "",
            "2. **[`delivery_results_rating_4.csv`](./delivery_results_rating_4.csv)** - 4分记录（去重后）",
            "   - 除交易日期外，其余审核子项均满足要求",
            "   - 建议作为「历史交易时间较久（超过30天），但整体证据完备」的高置信度地址",
            "",
            "3. **[`delivery_results_duplicate.csv`](./delivery_results_duplicate.csv)** - 重复记录",
            "   - 按 `address` 去重时被过滤的重复有效记录",
            "   - 保留 `submission_id` 最小的记录（最早的提交）",
            "",
            "### 字段说明文档",
            "",
            "📖 **[查看字段含义说明 →](./README.md)**",
            "",
            "详细字段说明请参考 `README.md`，包含：",
            "- 各字段的详细含义和取值说明",
            "- 不同交易类型（withdrawal/deposit）的字段差异",
            "- `extensions` JSON 字段的结构说明",
            "- 使用建议和注意事项",
            "",
            "---",
            "",
            "## 📊 总体统计",
            "",
            "| 指标 | 数量 |",
            "|------|------|",
            f"| 原始记录总数 | {total_original} |",
            f"| 去重后记录数 | {total_unique} |",
            f"| 重复记录数 | {total_duplicates} |",
            f"| 去重率 | {deduplication_rate}% |",
            "",
            "---",
            "",
            "## ⭐ 按评分统计",
            "",
            "| 评分 | 原始数量 | 去重后数量 | 重复数量 |",
            "|------|---------|-----------|---------|",
            f"| 5分 | {len(csv_rows_5_original)} | {len(csv_rows_5_unique)} | {len(csv_rows_5_original) - len(csv_rows_5_unique)} |",
            f"| 4分 | {len(csv_rows_4_original)} | {len(csv_rows_4_unique)} | {len(csv_rows_4_original) - len(csv_rows_4_unique)} |",
            "",
            "---",
            "",
            "## 🔗 按链（Chain）统计",
            "",
            "### 去重后记录",
            "",
            "| 链 | 数量 |",
            "|----|------|",
        ]
        
        for chain, count in sorted(chain_counter_unique.items(), key=lambda x: x[1], reverse=True):
            md_lines.append(f"| {chain} | {count} |")
        
        md_lines.extend([
            "",
            "### 5分记录",
            "",
            "| 链 | 数量 |",
            "|----|------|",
        ])
        
        for chain, count in sorted(chain_counter_5.items(), key=lambda x: x[1], reverse=True):
            md_lines.append(f"| {chain} | {count} |")
        
        md_lines.extend([
            "",
            "### 4分记录",
            "",
            "| 链 | 数量 |",
            "|----|------|",
        ])
        
        for chain, count in sorted(chain_counter_4.items(), key=lambda x: x[1], reverse=True):
            md_lines.append(f"| {chain} | {count} |")
        
        if chain_counter_duplicates:
            md_lines.extend([
                "",
                "### 重复记录",
                "",
                "| 链 | 数量 |",
                "|----|------|",
            ])
            for chain, count in sorted(chain_counter_duplicates.items(), key=lambda x: x[1], reverse=True):
                md_lines.append(f"| {chain} | {count} |")
        
        md_lines.extend([
            "",
            "---",
            "",
            "## 📝 按交易类型（Trace Type）统计",
            "",
            "### 去重后记录",
            "",
            "| 交易类型 | 数量 |",
            "|---------|------|",
        ])
        
        for trace_type, count in sorted(trace_type_counter_unique.items(), key=lambda x: x[1], reverse=True):
            md_lines.append(f"| {trace_type} | {count} |")
        
        md_lines.extend([
            "",
            "### 5分记录",
            "",
            "| 交易类型 | 数量 |",
            "|---------|------|",
        ])
        
        for trace_type, count in sorted(trace_type_counter_5.items(), key=lambda x: x[1], reverse=True):
            md_lines.append(f"| {trace_type} | {count} |")
        
        md_lines.extend([
            "",
            "### 4分记录",
            "",
            "| 交易类型 | 数量 |",
            "|---------|------|",
        ])
        
        for trace_type, count in sorted(trace_type_counter_4.items(), key=lambda x: x[1], reverse=True):
            md_lines.append(f"| {trace_type} | {count} |")
        
        if trace_type_counter_duplicates:
            md_lines.extend([
                "",
                "### 重复记录",
                "",
                "| 交易类型 | 数量 |",
                "|---------|------|",
            ])
            for trace_type, count in sorted(trace_type_counter_duplicates.items(), key=lambda x: x[1], reverse=True):
                md_lines.append(f"| {trace_type} | {count} |")
        
        md_lines.extend([
            "",
            "---",
            "",
            "## 🏢 按交易所（Entities）统计",
            "",
            "### 去重后记录",
            "",
            "| 交易所 | 数量 |",
            "|--------|------|",
        ])
        
        for entities, count in sorted(entities_counter_unique.items(), key=lambda x: x[1], reverse=True):
            md_lines.append(f"| {entities} | {count} |")
        
        md_lines.extend([
            "",
            "### 5分记录",
            "",
            "| 交易所 | 数量 |",
            "|--------|------|",
        ])
        
        for entities, count in sorted(entities_counter_5.items(), key=lambda x: x[1], reverse=True):
            md_lines.append(f"| {entities} | {count} |")
        
        md_lines.extend([
            "",
            "### 4分记录",
            "",
            "| 交易所 | 数量 |",
            "|--------|------|",
        ])
        
        for entities, count in sorted(entities_counter_4.items(), key=lambda x: x[1], reverse=True):
            md_lines.append(f"| {entities} | {count} |")
        
        if entities_counter_duplicates:
            md_lines.extend([
                "",
                "### 重复记录",
                "",
                "| 交易所 | 数量 |",
                "|--------|------|",
            ])
            for entities, count in sorted(entities_counter_duplicates.items(), key=lambda x: x[1], reverse=True):
                md_lines.append(f"| {entities} | {count} |")
        
        md_lines.extend([
            "",
            "---",
            "",
            f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        ])
        
        # 保存 Markdown 报告
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_lines))
        
        print(f"\n统计报告已生成: {report_path}")
        print(f"\n交付统计摘要:")
        print(f"  原始记录总数: {total_original}")
        print(f"  去重后记录数: {total_unique}")
        print(f"  重复记录数: {total_duplicates}")
        print(f"  去重率: {deduplication_rate}%")
        print(f"  5分记录: {len(csv_rows_5_unique)} 条（去重后）")
        print(f"  4分记录: {len(csv_rows_4_unique)} 条（去重后）")


def main():
    """主函数（仅从环境变量读取配置，不支持命令行参数）"""
    # 加载 .env 文件
    try:
        from dotenv import load_dotenv
        script_dir = Path(__file__).parent.absolute()
        base_dir = script_dir.parent  # cex_hot_wallet目录
        env_file = base_dir / ".env"
        if env_file.exists():
            load_dotenv(env_file)
    except ImportError:
        pass  # 如果没有安装python-dotenv，则跳过
    
    generator = CSVGenerator()
    
    # 如果配置了 DB_DELIVER_SQL，则从数据库读取 4/5 分记录生成交付
    use_db = bool(os.getenv("DB_DELIVER_SQL"))
    
    if not use_db:
        print("错误: 未配置 DB_DELIVER_SQL，当前仅支持从数据库读取数据生成交付 CSV")
        print("请在 .env 中设置 DB_DELIVER_SQL")
        return 1
    
    # 从环境变量读取输出目录（可选）
    output_dir = os.getenv("CSV_OUTPUT_DIR")
    if not output_dir:
        script_dir = Path(__file__).parent.absolute()
        base_dir = script_dir.parent
        output_dir = str(base_dir / "output" / "deliver_results")
    
    # 从环境变量读取综合审核结果路径（用于获取 detected_date，可选）
    comprehensive_results_path = os.getenv("COMPREHENSIVE_RESULTS_PATH")
    if not comprehensive_results_path:
        script_dir = Path(__file__).parent.absolute()
        base_dir = script_dir.parent
        comprehensive_results_path = str(base_dir / "output" / "main_audit" / "comprehensive_audit_results.json")
    
    try:
        output_files = generator.generate_csv_from_db(
            output_dir=output_dir,
            comprehensive_results_path=comprehensive_results_path,
        )
        print(f"\nCSV文件已生成:")
        print(f"  5分记录: {output_files['rating_5']}")
        print(f"  4分记录: {output_files['rating_4']}")
        print(f"  重复记录: {output_files['duplicates']}")
        print(f"  统计报告: {output_files['statistics_report']}")
    except Exception as e:
        print(f"生成CSV失败: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
