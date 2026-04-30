from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db import dedupe_existing_jobs, init_db


def main() -> None:
    init_db()
    stats = dedupe_existing_jobs()
    print(f"Deduplication complete: removed={stats['removed']}, kept={stats['kept']}")


if __name__ == "__main__":
    main()
