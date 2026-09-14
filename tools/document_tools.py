import shutil
import tempfile
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from urllib.parse import urlparse

import requests
from pypdf import PdfReader


BASE_DIR = Path(__file__).resolve().parents[1]
TEMP_DIR = BASE_DIR / "output" / "research_temp"


@contextmanager
def temporary_pdf(
    url: str,
    timeout_seconds: int = 20,
    max_bytes: int = 10 * 1024 * 1024,
) -> Iterator[Path]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("只允许下载HTTP或HTTPS公告地址")
    if max_bytes < 1 or max_bytes > 50 * 1024 * 1024:
        raise ValueError("单份PDF上限必须在1字节到50MB之间")

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    handle, filename = tempfile.mkstemp(prefix="announcement-", suffix=".pdf", dir=TEMP_DIR)
    os.close(handle)
    path = Path(filename)
    try:
        with requests.get(url, stream=True, timeout=timeout_seconds) as response:
            response.raise_for_status()
            declared_size = int(response.headers.get("content-length") or 0)
            if declared_size > max_bytes:
                raise ValueError("公告PDF超过单文件大小限制")
            with path.open("wb") as output:
                copied = 0
                first_chunk = True
                for chunk in response.iter_content(chunk_size=64 * 1024):
                    if not chunk:
                        continue
                    if first_chunk and not chunk.startswith(b"%PDF"):
                        raise ValueError("公告地址返回的不是PDF文件")
                    first_chunk = False
                    copied += len(chunk)
                    if copied > max_bytes:
                        raise ValueError("公告PDF超过单文件大小限制")
                    output.write(chunk)
        yield path
    finally:
        path.unlink(missing_ok=True)
        try:
            if TEMP_DIR.exists() and not any(TEMP_DIR.iterdir()):
                shutil.rmtree(TEMP_DIR)
        except OSError:
            pass


def resolve_cninfo_pdf(detail_url: str, timeout_seconds: int = 15) -> str:
    from urllib.parse import parse_qs

    parsed = urlparse(detail_url)
    query = parse_qs(parsed.query)
    announcement_id = (query.get("announcementId") or [None])[0]
    announcement_time = (query.get("announcementTime") or [None])[0]
    plate = (query.get("plate") or [""])[0]
    if not announcement_id or not announcement_time:
        raise ValueError("巨潮公告链接缺少公告编号或时间")
    response = requests.post(
        "http://www.cninfo.com.cn/new/announcement/bulletin_detail",
        params={
            "announceId": announcement_id,
            "flag": str(plate == "szse").lower(),
            "announceTime": announcement_time,
        },
        headers={"User-Agent": "Mozilla/5.0", "Referer": "http://www.cninfo.com.cn/"},
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    adjunct_url = (response.json().get("announcement") or {}).get("adjunctUrl")
    if not adjunct_url:
        raise ValueError("巨潮详情接口没有返回PDF地址")
    return f"https://static.cninfo.com.cn/{adjunct_url.lstrip('/')}"


def extract_pdf_text(
    pdf_path: Path,
    max_pages: int = 8,
    max_characters: int = 12000,
) -> str:
    reader = PdfReader(str(pdf_path))
    parts = []
    length = 0
    for page in reader.pages[:max_pages]:
        text = page.extract_text() or ""
        remaining = max_characters - length
        if remaining <= 0:
            break
        parts.append(text[:remaining])
        length += len(parts[-1])
    return "\n".join(parts).strip()
