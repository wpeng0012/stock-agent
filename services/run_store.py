import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


BASE_DIR = Path(__file__).resolve().parents[1]
RUNS_DIR = BASE_DIR / "output" / "runs"


def create_run_id() -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    short_id = uuid.uuid4().hex[:6]
    return f"{timestamp}-{short_id}"


def save_run(
    run_id: str,
    result: Dict[str, Any]
) -> Path:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    output_file = RUNS_DIR / f"{run_id}.json"

    output_file.write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    return output_file

def load_run(
    run_id: str
) -> Dict[str, Any]:
    output_file = RUNS_DIR / f"{run_id}.json"

    if not output_file.exists():
        raise FileNotFoundError(
            f"run not found: {run_id}"
        )

    return json.loads(
        output_file.read_text(
            encoding="utf-8"
        )
    )