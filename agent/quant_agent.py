from typing import Any, Dict, Optional

from tools.market_tools import get_data_status
from tools.screening_tools import screen_candidates


def run_quant_agent(
    as_of: Optional[str] = None,
    top_n: int = 10
) -> Dict[str, Any]:
    data_status = get_data_status()

    if data_status["status"] != "available":
        return {
            "status": "no_data",
            "data_status": data_status,
            "stocks": [],
            "missing_fields": ["stock_factor_daily.csv"]
        }

    result = screen_candidates(
        as_of=as_of,
        top_n=top_n
    )

    result["data_status"] = data_status

    return result