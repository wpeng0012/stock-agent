import argparse
import json
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from services.data_publish_service import publish_batch, validate_publish_batch


PRICE_PREVIEW = BASE_DIR / "output" / "market_update_preview.csv"
FACTOR_PREVIEW = BASE_DIR / "output" / "factor_update_preview.csv"
REPORT_FILE = BASE_DIR / "output" / "market_update_report.json"
OFFICIAL_PRICE = BASE_DIR / "data" / "stock_daily_price.csv"
OFFICIAL_FACTOR = BASE_DIR / "data" / "stock_factor_daily.csv"
BACKUP_ROOT = BASE_DIR / "output" / "data_backups"


def parse_args():
    parser = argparse.ArgumentParser(description="检查或发布行情与因子批次")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="实际发布；不加此参数时只做预演检查",
    )
    parser.add_argument(
        "--max-stale-ratio",
        type=float,
        default=0.05,
        help="允许日期落后股票的最大比例，默认0.05",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.max_stale_ratio < 0 or args.max_stale_ratio > 1:
        raise SystemExit("参数错误：max-stale-ratio必须在0到1之间")
    if not REPORT_FILE.exists():
        raise SystemExit("找不到更新报告，请先生成完整更新批次")

    report = json.loads(REPORT_FILE.read_text(encoding="utf-8"))
    expected_codes = [item["code"] for item in report.get("details", [])]
    if not expected_codes:
        raise SystemExit("更新报告中没有股票记录")

    if args.apply:
        result = publish_batch(
            price_preview_file=PRICE_PREVIEW,
            factor_preview_file=FACTOR_PREVIEW,
            report_file=REPORT_FILE,
            official_price_file=OFFICIAL_PRICE,
            official_factor_file=OFFICIAL_FACTOR,
            backup_root=BACKUP_ROOT,
            expected_codes=expected_codes,
            max_stale_ratio=args.max_stale_ratio,
        )
        print("发布成功")
        print("备份目录：", result["backup_dir"])
        print("数据日期：", result["validation"]["data_as_of"])
    else:
        result = validate_publish_batch(
            price_preview_file=PRICE_PREVIEW,
            factor_preview_file=FACTOR_PREVIEW,
            report_file=REPORT_FILE,
            expected_codes=expected_codes,
            max_stale_ratio=args.max_stale_ratio,
        )
        print("预演检查通过，本次没有修改正式数据")
        print("计划股票：", result["expected_stocks"])
        print("数据日期：", result["data_as_of"])
        print("日期落后股票：", result["stale_codes"])
        print("日期落后比例：", f"{result['stale_ratio']:.2%}")


if __name__ == "__main__":
    main()
