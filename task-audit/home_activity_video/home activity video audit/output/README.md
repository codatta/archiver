# output — 审核运行产物

本目录由 **`main.py`** 写入（默认 `--output-dir output`）。

## 文件

| 文件 | 说明 |
|------|------|
| `comprehensive_audit_results.json` | 每条 submission 的 `duplicate_audit` / `metadata_audit` / `scene_cut_audit` / `errors` 等详细结构 |
| `rating_results.json` | 与参考项目类似的汇总：`audit_grade_distribution`、`rated_results` |

## 注意

- 可将该目录加入 `.gitignore`（若含真实业务数据）  
- 路径可通过 `python main.py --output-dir 你的目录` 修改
