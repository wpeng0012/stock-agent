import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List

import akshare as ak
import numpy as np
import pandas as pd


PRICE_COLUMNS = ["open", "close", "high", "low", "volume", "amount", "turnover"]
COLUMNS = ["code", "date"] + PRICE_COLUMNS


def normalize_market_data(df: pd.DataFrame) -> pd.DataFrame:
    missing = sorted(set(COLUMNS) - set(df.columns))
    if missing:
        raise ValueError(f"缺少字段：{missing}")
    result = df[COLUMNS].copy()
    result["code"] = result["code"].astype(str).str.zfill(6)
    result["date"] = pd.to_datetime(result["date"], errors="raise").dt.strftime("%Y-%m-%d")
    for column in PRICE_COLUMNS:
        result[column] = pd.to_numeric(result[column], errors="raise")
    if result[COLUMNS].isna().any().any():
        raise ValueError("发现缺失值")
    if not np.isfinite(result[PRICE_COLUMNS].to_numpy()).all():
        raise ValueError("发现无穷大等异常数值")
    if (result[["open", "close", "high", "low"]] <= 0).any().any():
        raise ValueError("发现非正价格")
    if (result[["volume", "amount", "turnover"]] < 0).any().any():
        raise ValueError("发现负成交量、成交额或换手率")
    if (result["high"] < result[["open", "close", "low"]].max(axis=1)).any():
        raise ValueError("最高价与其他价格不一致")
    if (result["low"] > result[["open", "close", "high"]].min(axis=1)).any():
        raise ValueError("最低价与其他价格不一致")
    if (result["date"] > date.today().isoformat()).any():
        raise ValueError("发现未来日期")
    if result.duplicated(["code", "date"]).any():
        raise ValueError("存在重复股票日期")
    return result.sort_values(["code", "date"]).reset_index(drop=True)


def fetch_history(code: str, start_date: str, retries: int = 2) -> pd.DataFrame:
    symbol = ("sh" if code.startswith("6") else "sz") + code
    last_error = None
    for attempt in range(retries):
        try:
            result = ak.stock_zh_a_hist_tx(
                symbol=symbol,
                start_date=start_date,
                end_date=date.today().strftime("%Y%m%d"),
                adjust="",
                timeout=20,
            )
            if result is None or result.empty:
                raise ValueError("接口返回空数据")
            result["code"] = code
            return normalize_market_data(result)
        except Exception as exc:
            last_error = exc
            if attempt + 1 < retries:
                time.sleep(1)
    raise RuntimeError(str(last_error)) from last_error


def check_overlap(old: pd.DataFrame, new: pd.DataFrame) -> int:
    matched = old.merge(new, on=["code", "date"], suffixes=("_old", "_new"))
    if matched.empty:
        raise ValueError("没有重叠日期，无法验证数据口径")
    different = []
    for column in PRICE_COLUMNS:
        same = np.isclose(
            matched[f"{column}_old"], matched[f"{column}_new"],
            rtol=1e-6, atol=1e-8,
        )
        if not same.all():
            different.append(column)
    if different:
        raise ValueError(f"重叠数据有差异：{different}")
    return len(matched)


def merge_history(old: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
    merged = pd.concat([old, new], ignore_index=True)
    merged = merged.drop_duplicates(["code", "date"], keep="last")
    return normalize_market_data(merged)


def _update_one_stock(
    source: pd.DataFrame,
    code: str,
    part_file: Path,
):
    old = normalize_market_data(source.loc[source["code"] == code])
    if old.empty:
        raise ValueError("本地没有该股票历史数据")
    start_date = (
        pd.Timestamp(old["date"].max()) - timedelta(days=14)
    ).strftime("%Y%m%d")
    new = fetch_history(code, start_date)
    overlap_rows = check_overlap(old, new)
    merged = merge_history(old, new)
    pd.testing.assert_frame_equal(merged, merge_history(merged, new))
    if not set(old["date"]).issubset(set(merged["date"])):
        raise AssertionError("历史日期没有完整保留")

    temporary_part = part_file.with_suffix(".tmp")
    merged.to_csv(temporary_part, index=False, encoding="utf-8-sig")
    temporary_part.replace(part_file)
    detail = {
        "code": code,
        "status": "success",
        "old_latest": old["date"].max(),
        "new_latest": merged["date"].max(),
        "old_rows": len(old),
        "new_rows": len(merged),
        "added_rows": len(merged) - len(old),
        "overlap_rows": overlap_rows,
    }
    return detail, merged


def update_market_preview(
    source_file: Path,
    preview_file: Path,
    report_file: Path,
    codes: Iterable[str],
    parts_dir: Path = None,
    previous_details: List[Dict[str, Any]] = None,
    max_workers: int = 5,
) -> Dict[str, Any]:
    if max_workers < 1 or max_workers > 10:
        raise ValueError("max_workers必须在1到10之间")
    source = pd.read_csv(source_file, dtype={"code": str})
    source["code"] = source["code"].str.zfill(6)
    selected_codes = list(dict.fromkeys(str(code).zfill(6) for code in codes))
    results: List[pd.DataFrame] = []
    details: List[Dict[str, Any]] = []
    parts_dir = parts_dir or preview_file.parent / "market_update_parts"
    parts_dir.mkdir(parents=True, exist_ok=True)
    previous_by_code = {
        item["code"]: item for item in (previous_details or [])
    }

    def write_checkpoint(status: str = "running"):
        succeeded_now = sum(item["status"] == "success" for item in details)
        failed_now = sum(item["status"] == "failed" for item in details)
        checkpoint = {
            "status": status,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "requested": len(selected_codes),
            "requested_codes": selected_codes,
            "completed": len(details),
            "succeeded": succeeded_now,
            "failed": failed_now,
            "details": details,
        }
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text(
            json.dumps(checkpoint, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    write_checkpoint()

    pending_codes = []
    for code in selected_codes:
        part_file = parts_dir / f"{code}.csv"
        previous = previous_by_code.get(code)
        if previous and previous.get("status") == "success" and part_file.exists():
            merged = normalize_market_data(
                pd.read_csv(part_file, dtype={"code": str})
            )
            results.append(merged)
            detail = dict(previous)
            detail["resumed"] = True
            details.append(detail)
            print(f"跳过已完成 {code}")
            write_checkpoint()
            continue
        pending_codes.append(code)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        tasks = {}
        for code in pending_codes:
            print(f"提交更新 {code}")
            part_file = parts_dir / f"{code}.csv"
            future = executor.submit(_update_one_stock, source, code, part_file)
            tasks[future] = code

        for future in as_completed(tasks):
            code = tasks[future]
            try:
                detail, merged = future.result()
                results.append(merged)
                print(
                    f"成功 {code}：{detail['old_latest']} → "
                    f"{detail['new_latest']}，新增 {detail['added_rows']} 条"
                )
            except Exception as exc:
                detail = {
                    "code": code,
                    "status": "failed",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
                print(f"失败 {code}：{type(exc).__name__}: {exc}")
            details.append(detail)
            write_checkpoint()

    detail_order = {code: index for index, code in enumerate(selected_codes)}
    details.sort(key=lambda item: detail_order[item["code"]])

    succeeded = sum(item["status"] == "success" for item in details)
    failed = len(details) - succeeded
    successful_latest_dates = [
        item["new_latest"]
        for item in details
        if item["status"] == "success"
    ]
    batch_latest = max(successful_latest_dates) if successful_latest_dates else None
    stale_codes = [
        item["code"]
        for item in details
        if item["status"] == "success"
        and item["new_latest"] < batch_latest
    ] if batch_latest else []
    report: Dict[str, Any] = {
        "status": "completed",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "requested": len(selected_codes),
        "requested_codes": selected_codes,
        "completed": len(details),
        "succeeded": succeeded,
        "failed": failed,
        "batch_latest": batch_latest,
        "stale_codes": stale_codes,
        "preview_published": failed == 0 and succeeded > 0,
        "details": details,
    }
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if report["preview_published"]:
        preview = normalize_market_data(pd.concat(results, ignore_index=True))
        temporary = preview_file.with_suffix(".tmp")
        preview.to_csv(temporary, index=False, encoding="utf-8-sig")
        temporary.replace(preview_file)
    return report
