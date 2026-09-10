from pathlib import Path
from typing import Any, Dict

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
FACTOR_FILE = BASE_DIR / "data" / "stock_factor_daily.csv"


def get_data_status(
    factor_file: Path = FACTOR_FILE
) -> Dict[str, Any]:
    if not factor_file.exists():
        return {
            "status": "no_data",
            "file": str(factor_file),
            "rows": 0,
            "data_as_of": None
        }

    try:
        df = pd.read_csv(
            factor_file,
            usecols=["date"]
        )
    except (ValueError, pd.errors.EmptyDataError):
        return {
            "status": "no_data",
            "file": str(factor_file),
            "rows": 0,
            "data_as_of": None
        }

    if df.empty:
        return {
            "status": "no_data",
            "file": str(factor_file),
            "rows": 0,
            "data_as_of": None
        }

    return {
        "status": "available",
        "file": str(factor_file),
        "rows": len(df),
        "data_as_of": str(df["date"].max())
    }
