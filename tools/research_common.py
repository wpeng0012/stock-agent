from datetime import date, datetime
from typing import Any, Dict, Iterable, List, Optional


def normalize_stock_code(stock_code: str) -> str:
    code = str(stock_code or "").strip().upper()
    code = code.replace(".SH", "").replace(".SZ", "").replace(".BJ", "")
    if not (len(code) == 6 and code.isdigit()):
        raise ValueError("股票代码必须是6位数字")
    return code


def normalize_date(value: Optional[str], field: str) -> Optional[str]:
    if value in (None, ""):
        return None
    try:
        parsed = datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"{field}必须使用YYYY-MM-DD格式") from exc
    if parsed > date.today():
        raise ValueError(f"{field}不能晚于今天")
    return parsed.isoformat()


def value_from(record: Dict[str, Any], names: Iterable[str]):
    for name in names:
        if name in record and record[name] not in (None, ""):
            return record[name]
    return None


def sort_and_limit(
    records: List[Dict[str, Any]],
    date_field: str,
    max_items: int,
) -> List[Dict[str, Any]]:
    return sorted(
        records,
        key=lambda item: str(item.get(date_field) or ""),
        reverse=True,
    )[:max_items]
