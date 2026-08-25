"""Download the UCI Heart Disease databases into ``data/raw/``.

The raw files are small and public, so they are committed to the repository.
This script exists so the download is reproducible — run it to refresh them, or
to fetch them if you cloned without LFS/history::

    python -m src.fetch_data
"""

from __future__ import annotations

import argparse
import io
import urllib.request
import zipfile
from pathlib import Path

from . import config as cfg

ARCHIVE_URL = "https://archive.ics.uci.edu/static/public/45/heart+disease.zip"

# The 14-attribute `processed.*` files plus the archive's own documentation.
WANTED = sorted(set(cfg.RAW_FILES.values()) | {"heart-disease.names"})


def fetch(raw_dir: Path | None = None, url: str = ARCHIVE_URL) -> list[Path]:
    """Download the archive and extract the files this project uses."""
    raw_dir = Path(raw_dir) if raw_dir is not None else cfg.RAW_DIR
    raw_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {url} ...")
    with urllib.request.urlopen(url, timeout=120) as response:
        payload = response.read()
    print(f"  {len(payload):,} bytes")

    written: list[Path] = []
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        available = set(archive.namelist())
        for name in WANTED:
            if name not in available:
                raise FileNotFoundError(f"{name!r} is not in the archive at {url}")
            target = raw_dir / name
            target.write_bytes(archive.read(name))
            written.append(target)
            print(f"  extracted {name} ({target.stat().st_size:,} bytes)")

    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m src.fetch_data", description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=None, help="override data/raw")
    parser.add_argument("--url", default=ARCHIVE_URL, help="override the archive URL")
    args = parser.parse_args(argv)

    written = fetch(raw_dir=args.raw_dir, url=args.url)
    print(f"\nDone — {len(written)} files in {written[0].parent}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
