"""CLI for running promotion batches."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "services/mcp-server/src"))
sys.path.insert(0, str(PROJECT_ROOT / "shared/lib"))

from cli.promotion_cli import cli_main  # noqa: E402

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run promotion batch for a team")
    parser.add_argument("team_id", help="Team identifier")
    parser.add_argument("--dry-run", action="store_true", help="Evaluate without writing changes")
    args = parser.parse_args()

    summary = cli_main(args.team_id, dry_run=args.dry_run)
    LOGGER.info("Promotion summary: %s", summary)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
