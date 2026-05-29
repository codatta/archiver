"""
公共工具函数
提供 JSON 处理、路径处理、地址规范化等通用功能
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any


def load_json(file_path: str) -> Optional[Dict | List]:
    """
    加载 JSON 文件
    
    Args:
        file_path: JSON 文件路径
        
    Returns:
        JSON 数据（字典或列表），失败返回 None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"错误: 读取 JSON 文件失败 {file_path}: {e}")
        return None


def save_json(data: Dict | List, file_path: str, indent: int = 2) -> bool:
    """
    保存数据到 JSON 文件
    
    Args:
        data: 要保存的数据
        file_path: 输出文件路径
        indent: JSON 缩进（默认 2）
        
    Returns:
        是否保存成功
    """
    try:
        output_path = Path(file_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        return True
    except Exception as e:
        print(f"错误: 保存 JSON 文件失败 {file_path}: {e}")
        return False


def normalize_address(address: str) -> str:
    """
    规范化地址（转小写，去除空格）
    
    Args:
        address: 地址字符串
        
    Returns:
        规范化后的地址
    """
    if not address:
        return ""
    return address.strip().lower()


def compare_addresses(addr1: str, addr2: str) -> bool:
    """
    比较两个地址是否一致（忽略大小写）
    
    Args:
        addr1: 地址1
        addr2: 地址2
        
    Returns:
        是否一致
    """
    return normalize_address(addr1) == normalize_address(addr2)


def check_address_in_list(expected_address: str, address_list: List[str]) -> bool:
    """
    检查期望地址是否在地址列表中（任意一个匹配即可）
    
    Args:
        expected_address: 期望的地址
        address_list: 地址列表
        
    Returns:
        是否匹配
    """
    if not address_list:
        return False
    
    normalized_expected = normalize_address(expected_address)
    return any(normalize_address(addr) == normalized_expected for addr in address_list)


def parse_submission_data(submission: Dict) -> Optional[Dict]:
    """
    解析 submission 中的 data_submission JSON 字符串
    
    Args:
        submission: 提交记录字典
        
    Returns:
        解析后的 data_submission 字典，失败返回 None
    """
    try:
        data_str = submission.get("data_submission", "{}")
        return json.loads(data_str) if isinstance(data_str, str) else data_str
    except Exception as e:
        print(f"错误: 解析 data_submission 失败: {e}")
        return None


def build_submissions_map(submissions: List[Dict]) -> Dict[str, Dict]:
    """
    构建 submission_id 到 data_submission 的映射
    
    Args:
        submissions: submissions 列表
        
    Returns:
        {submission_id: data_submission} 映射字典
    """
    result = {}
    for sub in submissions:
        submission_id = sub.get("submission_id")
        if submission_id:
            data_submission = parse_submission_data(sub)
            if data_submission:
                result[submission_id] = data_submission
    return result


def load_existing_results_by_id(result_file: str, id_key: str = "submission_id") -> Dict[str, Dict]:
    """
    加载已有结果文件，返回 ID 到结果的映射（用于增量处理）
    
    Args:
        result_file: 结果文件路径
        id_key: ID 字段名（默认 "submission_id"）
        
    Returns:
        {id: result_dict} 映射字典
    """
    result_path = Path(result_file)
    if not result_path.exists():
        return {}
    
    try:
        with open(result_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 处理不同的结果文件格式
        if isinstance(data, dict):
            # 格式：{"result": "success", "verifications": [...]} 或 {"audit_results": [...]}
            if "verifications" in data:
                results_list = data.get("verifications", [])
            elif "audit_results" in data:
                results_list = data.get("audit_results", [])
            else:
                # 如果本身就是字典格式，尝试直接使用
                return {}
        elif isinstance(data, list):
            results_list = data
        else:
            return {}
        
        # 构建 ID 映射
        result_dict = {}
        for item in results_list:
            item_id = item.get(id_key)
            if item_id:
                result_dict[item_id] = item
        
        return result_dict
    except Exception as e:
        print(f"警告: 加载已有结果文件失败 {result_file}: {e}，将重新开始")
        return {}


def save_single_result(result_item: Dict, result_file: str, id_key: str = "submission_id", 
                       list_key: str = "verifications", summary_keys: Optional[List[str]] = None):
    """
    保存单条结果到文件（增量写入）
    
    Args:
        result_item: 单条结果字典
        result_file: 结果文件路径
        id_key: ID 字段名（默认 "submission_id"）
        list_key: 结果列表的键名（默认 "verifications"，也可能是 "audit_results"）
        summary_keys: 需要重新计算的汇总字段（如 ["total", "pass", "fail"]）
    """
    result_path = Path(result_file)
    result_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 加载已有结果
    existing_data = load_json(result_file)
    
    if not existing_data:
        # 创建新文件结构
        existing_data = {
            "result": "success",
            list_key: []
        }
        if summary_keys:
            for key in summary_keys:
                existing_data["summary"] = existing_data.get("summary", {})
                existing_data["summary"][key] = 0
    
    # 获取结果列表
    results_list = existing_data.get(list_key, [])
    
    # 更新或添加新结果
    item_id = result_item.get(id_key)
    if item_id:
        # 查找是否已存在
        found = False
        for i, existing_item in enumerate(results_list):
            if existing_item.get(id_key) == item_id:
                results_list[i] = result_item
                found = True
                break
        
        if not found:
            results_list.append(result_item)
        
        existing_data[list_key] = results_list
        
        # 重新计算汇总（如果提供了汇总字段）
        if summary_keys and results_list:
            summary = {}
            for key in summary_keys:
                if key == "total":
                    summary[key] = len(results_list)
                elif key == "pass":
                    summary[key] = sum(1 for r in results_list if r.get("result") == "pass")
                elif key == "fail":
                    summary[key] = sum(1 for r in results_list if r.get("result") == "fail")
                elif key == "pending":
                    summary[key] = sum(1 for r in results_list if r.get("result") == "pending")
                elif key == "success":
                    summary[key] = sum(1 for r in results_list if not r.get("errors"))
                elif key == "with_errors":
                    summary[key] = sum(1 for r in results_list if r.get("errors"))
            
            existing_data["summary"] = summary
        
        # 保存文件
        save_json(existing_data, result_file)
        print(f"✓ 已保存: {item_id}")
