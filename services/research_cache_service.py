import json
import time
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, Optional


BASE_DIR = Path(__file__).resolve().parents[1]
CACHE_DIR = BASE_DIR / "output" / "research_cache"
MAX_CACHE_BYTES = 2 * 1024 * 1024 * 1024


def _cache_path(cache_key: str, cache_dir: Path) -> Path:
    digest = sha256(cache_key.encode("utf-8")).hexdigest()
    return cache_dir / f"{digest}.json"


def load_cache(
    cache_key: str,
    ttl_seconds: int,
    cache_dir: Path = CACHE_DIR,
) -> Optional[Dict[str, Any]]:
    path = _cache_path(cache_key, cache_dir)
    if not path.exists():
        return None
    if time.time() - path.stat().st_mtime > ttl_seconds:
        path.unlink(missing_ok=True)
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_cache(
    cache_key: str,
    payload: Dict[str, Any],
    cache_dir: Path = CACHE_DIR,
) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = _cache_path(cache_key, cache_dir)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(path)
    enforce_cache_limit(cache_dir=cache_dir)
    return path


def enforce_cache_limit(
    cache_dir: Path = CACHE_DIR,
    max_bytes: int = MAX_CACHE_BYTES,
):
    if not cache_dir.exists():
        return
    files = sorted(
        cache_dir.glob("*.json"), key=lambda item: item.stat().st_mtime
    )
    total = sum(item.stat().st_size for item in files)
    for path in files:
        if total <= max_bytes:
            break
        size = path.stat().st_size
        path.unlink(missing_ok=True)
        total -= size
