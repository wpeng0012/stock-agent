import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Iterable

import pandas as pd


KEY_COLUMNS = ["code", "date"]
LATEST_FACTOR_COLUMNS = [
    "amount_ratio_1d", "turnover_ma5", "MA10", "MA20",
]


def validate_publish_batch(
    price_preview_file: Path,
    factor_preview_file: Path,
    report_file: Path,
    expected_codes: Iterable[str],
    max_stale_ratio: float = 0.05,
) -> Dict[str, Any]:
    report = json.loads(report_file.read_text(encoding="utf-8"))
    price = pd.read_csv(price_preview_file, dtype={"code": str})
    factor = pd.read_csv(factor_preview_file, dtype={"code": str})
    expected = {str(code).zfill(6) for code in expected_codes}
    price["code"] = price["code"].str.zfill(6)
    factor["code"] = factor["code"].str.zfill(6)

    errors = []
    if report.get("failed") != 0 or not report.get("preview_published"):
        errors.append("行情更新批次未全部成功")
    if report.get("factor_build", {}).get("status") != "success":
        errors.append("因子构建未成功")
    if set(price["code"].unique()) != expected:
        errors.append("行情股票范围与计划范围不一致")
    if set(factor["code"].unique()) != expected:
        errors.append("因子股票范围与计划范围不一致")
    if price.duplicated(KEY_COLUMNS).any():
        errors.append("行情存在重复股票日期")
    if factor.duplicated(KEY_COLUMNS).any():
        errors.append("因子存在重复股票日期")
    if set(map(tuple, price[KEY_COLUMNS].to_numpy())) != set(
        map(tuple, factor[KEY_COLUMNS].to_numpy())
    ):
        errors.append("行情和因子的股票日期范围不一致")

    latest_date = factor["date"].max()
    latest = factor.loc[factor["date"] == latest_date]
    incomplete_codes = factor.loc[
        factor["date"].eq(latest_date)
        & factor[LATEST_FACTOR_COLUMNS].isna().any(axis=1),
        "code",
    ].astype(str).unique().tolist()
    incomplete_ratio = len(incomplete_codes) / len(expected) if expected else 1.0
    if incomplete_ratio > 0.05:
        errors.append(
            f"最新日期因子不完整比例过高：{incomplete_ratio:.2%}"
        )

    stale_codes = report.get("stale_codes", [])
    stale_ratio = len(stale_codes) / len(expected) if expected else 1.0
    if stale_ratio > max_stale_ratio:
        errors.append(
            f"日期落后股票比例过高：{stale_ratio:.2%}，"
            f"上限为{max_stale_ratio:.2%}"
        )

    result = {
        "status": "passed" if not errors else "failed",
        "errors": errors,
        "expected_stocks": len(expected),
        "price_stocks": price["code"].nunique(),
        "factor_stocks": factor["code"].nunique(),
        "price_rows": len(price),
        "factor_rows": len(factor),
        "data_as_of": latest_date,
        "stale_codes": stale_codes,
        "stale_ratio": stale_ratio,
        "incomplete_codes": incomplete_codes,
        "incomplete_ratio": incomplete_ratio,
    }
    if errors:
        raise ValueError("；".join(errors))
    return result


def _atomic_copy(
    source: Path,
    target: Path,
    replace_func: Callable[[Path, Path], None] = os.replace,
) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".publishing")
    shutil.copy2(source, temporary)
    try:
        replace_func(temporary, target)
    except PermissionError:
        # 某些Windows目录策略禁止替换已有文件，但允许覆盖写入。
        # 目标文件已有发布前备份，因此这里仍可恢复。
        shutil.copyfile(temporary, target)
        temporary.unlink(missing_ok=True)


def publish_batch(
    price_preview_file: Path,
    factor_preview_file: Path,
    report_file: Path,
    official_price_file: Path,
    official_factor_file: Path,
    backup_root: Path,
    expected_codes: Iterable[str],
    max_stale_ratio: float = 0.05,
    replace_func: Callable[[Path, Path], None] = os.replace,
) -> Dict[str, Any]:
    validation = validate_publish_batch(
        price_preview_file=price_preview_file,
        factor_preview_file=factor_preview_file,
        report_file=report_file,
        expected_codes=expected_codes,
        max_stale_ratio=max_stale_ratio,
    )

    backup_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
    backup_dir = backup_root / backup_id
    backup_dir.mkdir(parents=True, exist_ok=False)
    backup_price = backup_dir / official_price_file.name
    backup_factor = backup_dir / official_factor_file.name
    shutil.copy2(official_price_file, backup_price)
    shutil.copy2(official_factor_file, backup_factor)

    try:
        _atomic_copy(price_preview_file, official_price_file, replace_func)
        _atomic_copy(factor_preview_file, official_factor_file, replace_func)
    except Exception:
        _atomic_copy(backup_price, official_price_file)
        _atomic_copy(backup_factor, official_factor_file)
        raise

    return {
        "status": "published",
        "backup_dir": str(backup_dir),
        "validation": validation,
    }
