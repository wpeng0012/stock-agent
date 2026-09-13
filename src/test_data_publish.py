import json
import os
import shutil
import sys
import tempfile
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from services.data_publish_service import publish_batch


PRICE_PREVIEW = BASE_DIR / "output" / "market_update_preview.csv"
FACTOR_PREVIEW = BASE_DIR / "output" / "factor_update_preview.csv"
REPORT_FILE = BASE_DIR / "output" / "market_update_report.json"


def load_expected_codes():
    report = json.loads(REPORT_FILE.read_text(encoding="utf-8"))
    return [item["code"] for item in report["details"]]


def main():
    expected_codes = load_expected_codes()

    with tempfile.TemporaryDirectory() as temporary_dir:
        work = Path(temporary_dir)
        official_price = work / "data" / "stock_daily_price.csv"
        official_factor = work / "data" / "stock_factor_daily.csv"
        backup_root = work / "backups"
        official_price.parent.mkdir(parents=True)

        official_price.write_text("old-price", encoding="utf-8")
        official_factor.write_text("old-factor", encoding="utf-8")

        result = publish_batch(
            price_preview_file=PRICE_PREVIEW,
            factor_preview_file=FACTOR_PREVIEW,
            report_file=REPORT_FILE,
            official_price_file=official_price,
            official_factor_file=official_factor,
            backup_root=backup_root,
            expected_codes=expected_codes,
        )

        assert result["status"] == "published"
        assert official_price.read_bytes() == PRICE_PREVIEW.read_bytes()
        assert official_factor.read_bytes() == FACTOR_PREVIEW.read_bytes()
        backup_dir = Path(result["backup_dir"])
        assert (backup_dir / official_price.name).read_text(encoding="utf-8") == "old-price"
        assert (backup_dir / official_factor.name).read_text(encoding="utf-8") == "old-factor"
        print("通过：质量门槛允许合格批次发布")
        print("通过：发布前文件已经备份")
        print("通过：行情和因子均发布成功")

        official_price.write_text("rollback-price", encoding="utf-8")
        official_factor.write_text("rollback-factor", encoding="utf-8")
        calls = {"count": 0}

        def fail_second_replace(source, target):
            calls["count"] += 1
            if calls["count"] == 2:
                raise OSError("模拟因子文件发布失败")
            os.replace(source, target)

        try:
            publish_batch(
                price_preview_file=PRICE_PREVIEW,
                factor_preview_file=FACTOR_PREVIEW,
                report_file=REPORT_FILE,
                official_price_file=official_price,
                official_factor_file=official_factor,
                backup_root=backup_root,
                expected_codes=expected_codes,
                replace_func=fail_second_replace,
            )
        except OSError:
            pass
        else:
            raise AssertionError("模拟发布失败没有触发")

        assert official_price.read_text(encoding="utf-8") == "rollback-price"
        assert official_factor.read_text(encoding="utf-8") == "rollback-factor"
        print("通过：中途发布失败后自动恢复两个旧文件")

        protected_price = official_price.read_bytes()
        protected_factor = official_factor.read_bytes()
        try:
            publish_batch(
                price_preview_file=PRICE_PREVIEW,
                factor_preview_file=FACTOR_PREVIEW,
                report_file=REPORT_FILE,
                official_price_file=official_price,
                official_factor_file=official_factor,
                backup_root=backup_root,
                expected_codes=expected_codes,
                max_stale_ratio=0,
            )
        except ValueError as exc:
            assert "日期落后股票比例过高" in str(exc)
        else:
            raise AssertionError("不合格批次没有被质量门槛拒绝")

        assert official_price.read_bytes() == protected_price
        assert official_factor.read_bytes() == protected_factor
        print("通过：不合格批次在写入前被拒绝")


if __name__ == "__main__":
    main()
