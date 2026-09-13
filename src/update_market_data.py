import argparse
import json
import sys
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from services.market_update_service import update_market_preview
from services.factor_service import build_factor_data


SOURCE_FILE = BASE_DIR / "data" / "stock_daily_price.csv"
PREVIEW_FILE = BASE_DIR / "output" / "market_update_preview.csv"
REPORT_FILE = BASE_DIR / "output" / "market_update_report.json"
FACTOR_PREVIEW_FILE = BASE_DIR / "output" / "factor_update_preview.csv"
PARTS_DIR = BASE_DIR / "output" / "market_update_parts"

REQUIRED_LATEST_FACTORS = [
    "amount_ratio_1d",
    "turnover_ma5",
    "MA10",
    "MA20",
]


def parse_args():
    parser = argparse.ArgumentParser(description="生成行情增量更新预览")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--codes", nargs="+", help="指定股票代码")
    group.add_argument("--limit", type=int, help="按本地顺序取前N只股票")
    group.add_argument("--all", action="store_true", help="更新本地全部股票")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="从上一次报告继续，只重试失败或未完成的股票",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=5,
        help="并发数量，范围1到10，默认5",
    )
    return parser.parse_args()


def select_codes(args):
    source = pd.read_csv(SOURCE_FILE, usecols=["code"], dtype={"code": str})
    available = source["code"].str.zfill(6).drop_duplicates().tolist()
    if args.codes:
        return [str(code).zfill(6) for code in args.codes]
    if args.all:
        return available
    limit = args.limit if args.limit is not None else 3
    if limit < 1:
        raise ValueError("limit必须大于0")
    return available[:limit]


def build_factor_preview(report):
    """使用本批行情预览生成因子预览，并补充批次报告。"""
    try:
        price = pd.read_csv(PREVIEW_FILE, dtype={"code": str})
        factor = build_factor_data(price)
        latest_date = factor["date"].max()
        latest = factor.loc[factor["date"] == latest_date]

        if latest.empty:
            raise ValueError("最新日期没有因子数据")
        incomplete_codes = latest.loc[
            latest[REQUIRED_LATEST_FACTORS].isna().any(axis=1),
            "code",
        ].astype(str).tolist()
        incomplete_ratio = len(incomplete_codes) / max(
            1, latest["code"].nunique()
        )
        if incomplete_ratio > 0.05:
            raise ValueError(
                f"最新日期因子不完整比例过高：{incomplete_ratio:.2%}"
            )
        if factor.duplicated(["code", "date"]).any():
            raise ValueError("因子数据存在重复股票日期")
        if factor["code"].nunique() != report["succeeded"]:
            raise ValueError("因子股票数量与行情更新成功数量不一致")

        repeated = build_factor_data(price)
        pd.testing.assert_frame_equal(
            factor.reset_index(drop=True),
            repeated.reset_index(drop=True),
        )

        temporary = FACTOR_PREVIEW_FILE.with_suffix(".tmp")
        factor.to_csv(temporary, index=False, encoding="utf-8-sig")
        temporary.replace(FACTOR_PREVIEW_FILE)

        report["factor_build"] = {
            "status": "success",
            "rows": len(factor),
            "stocks": factor["code"].nunique(),
            "data_as_of": latest_date,
            "latest_missing_values": int(
                latest[REQUIRED_LATEST_FACTORS].isna().sum().sum()
            ),
            "incomplete_codes": incomplete_codes,
            "incomplete_ratio": incomplete_ratio,
        }
    except Exception as exc:
        report["factor_build"] = {
            "status": "failed",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    REPORT_FILE.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return report["factor_build"]["status"] == "success"


def main():
    args = parse_args()
    if args.workers < 1 or args.workers > 10:
        raise SystemExit("参数错误：workers必须在1到10之间")
    previous_details = None
    if args.resume:
        if not REPORT_FILE.exists():
            raise SystemExit("无法续跑：找不到上一次更新报告")
        previous_report = json.loads(REPORT_FILE.read_text(encoding="utf-8"))
        previous_details = previous_report.get("details", [])
        codes = previous_report.get("requested_codes", [])
        if not codes:
            codes = [item["code"] for item in previous_details]
        if not codes:
            raise SystemExit("无法续跑：上一次报告没有股票记录")
    else:
        try:
            codes = select_codes(args)
        except ValueError as exc:
            raise SystemExit(f"参数错误：{exc}") from None
    print(f"本轮计划更新 {len(codes)} 只股票")
    report = update_market_preview(
        source_file=SOURCE_FILE,
        preview_file=PREVIEW_FILE,
        report_file=REPORT_FILE,
        codes=codes,
        parts_dir=PARTS_DIR,
        previous_details=previous_details,
        max_workers=args.workers,
    )
    print(f"完成：成功 {report['succeeded']} 只，失败 {report['failed']} 只")
    print("更新报告：", REPORT_FILE)
    if report["preview_published"]:
        print("行情预览：", PREVIEW_FILE)
        factor_ok = build_factor_preview(report)
        if factor_ok:
            print("因子预览：", FACTOR_PREVIEW_FILE)
        else:
            print("因子构建失败，详情见更新报告")
            raise SystemExit(1)
    else:
        print("存在失败，本轮没有发布新的行情预览")
    if report["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
