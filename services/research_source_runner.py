import json
import multiprocessing
import os
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict


ALLOWED_PROVIDERS = {
    "stock_zh_a_disclosure_report_cninfo",
    "stock_restricted_release_queue_em",
    "stock_irm_cninfo",
    "stock_sns_sseinfo",
    "stock_news_em",
}


def _json_value(value: Any):
    if value is None:
        return None
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    try:
        if value != value:
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(value, "item"):
        value = value.item()
    return value if isinstance(value, (str, int, float, bool)) else str(value)


def _worker(provider: str, kwargs: Dict[str, Any], max_records: int, result_file: str):
    try:
        import akshare as ak

        frame = getattr(ak, provider)(**kwargs)
        original_count = len(frame)
        frame = frame.head(max_records)
        records = [
            {str(key): _json_value(value) for key, value in row.items()}
            for row in frame.to_dict("records")
        ]
        payload = {
            "status": "completed",
            "provider": provider,
            "records": records,
            "returned": len(records),
            "truncated": original_count > max_records,
        }
    except Exception as exc:
        payload = {
            "status": "failed",
            "provider": provider,
            "records": [],
            "returned": 0,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    Path(result_file).write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8"
    )


def run_akshare_provider(
    provider: str,
    kwargs: Dict[str, Any],
    timeout_seconds: int = 15,
    max_records: int = 50,
) -> Dict[str, Any]:
    if provider not in ALLOWED_PROVIDERS:
        raise ValueError(f"不允许的数据接口：{provider}")
    if timeout_seconds < 1 or timeout_seconds > 30:
        raise ValueError("timeout_seconds必须在1到30之间")
    if max_records < 1 or max_records > 200:
        raise ValueError("max_records必须在1到200之间")

    handle, result_file = tempfile.mkstemp(prefix="stock-research-", suffix=".json")
    os.close(handle)
    context = multiprocessing.get_context("spawn")
    process = context.Process(
        target=_worker,
        args=(provider, kwargs, max_records, result_file),
    )
    try:
        process.start()
        process.join(timeout_seconds)
        if process.is_alive():
            process.terminate()
            process.join(3)
            return {
                "status": "timeout",
                "provider": provider,
                "records": [],
                "returned": 0,
                "error": f"数据源超过{timeout_seconds}秒未完成，已终止",
            }
        path = Path(result_file)
        if not path.exists() or path.stat().st_size == 0:
            return {
                "status": "failed",
                "provider": provider,
                "records": [],
                "returned": 0,
                "error": f"数据进程异常退出：{process.exitcode}",
            }
        return json.loads(path.read_text(encoding="utf-8"))
    finally:
        Path(result_file).unlink(missing_ok=True)
