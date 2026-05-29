# main_audit — 综合编排与输出

对标 `cex_hot_wallet/main_audit/`：**不实现具体像素级规则**，只负责调度各 Phase 包、合并 JSON、触发数据库回写。

## 目录与文件

| 文件 | 职责 |
|------|------|
| `video_auditor.py` | `VideoAuditor`：读 DB 行 → `ffprobe` 一次 → Phase 0 → 1 → 2 → 3；处理跳过/阻断；调用 `db_client.update_video_status` |
| `output_builder.py` | `summarize_comprehensive`、`build_rating_results`：与 `output/*.json` 字段结构一致 |
| `__init__.py` | 对外导出 `VideoAuditor`、汇总函数 |

## 调用链（便于排查）

```
main.py
  └── VideoAuditDBClient.fetch_pending_videos
  └── VideoAuditor.audit_row(row)
        ├── video_common.ffprobe_utils（时长、宽高）
        ├── phase0_duplicate_check.run_duplicate_check
        ├── phase1_metadata_check.run_metadata_check   （仅当 Phase 0 pass）
        ├── phase2_scene_cut_check.run_scene_cut_check （仅当 Phase 1 pass）
        └── phase3_yolo_audit.run_yolo_audit          （仅当 Phase 2 pass）
```

## 运行方式

在项目根目录（`家务视频审核/`）执行：

```bash
python main.py --output-dir output --db-limit 50
```

详见仓库根目录 `README.md`。

## 修改指引

- **只改流程顺序或增加 Phase 3**：主要改 `video_auditor.py`  
- **只改汇总 JSON**：改 `output_builder.py`  
- **改某一阶段业务规则**：到对应 `phase*_*/` 目录，读该目录 `README.md`
