import sys
import tempfile
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from services.market_update_service import update_market_preview


def main():
    with tempfile.TemporaryDirectory() as temporary_dir:
        work_dir = Path(temporary_dir)
        preview_file = work_dir / "preview.csv"
        report_file = work_dir / "report.json"
        parts_dir = work_dir / "parts"

        preview_file.write_text("protected-content", encoding="utf-8")
        original_content = preview_file.read_text(encoding="utf-8")

        report = update_market_preview(
            source_file=BASE_DIR / "data" / "stock_daily_price.csv",
            preview_file=preview_file,
            report_file=report_file,
            codes=["999999"],
            parts_dir=parts_dir,
        )

        assert report["requested"] == 1
        assert report["succeeded"] == 0
        assert report["failed"] == 1
        assert report["preview_published"] is False
        assert preview_file.read_text(encoding="utf-8") == original_content
        assert report_file.exists()
        assert not list(parts_dir.glob("*.csv"))

        print("通过：失败股票写入报告")
        print("通过：失败批次不发布新预览")
        print("通过：原有预览内容保持不变")


if __name__ == "__main__":
    main()
