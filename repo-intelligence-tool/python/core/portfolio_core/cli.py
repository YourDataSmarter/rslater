from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .constants import API_BASE
from .github_api import infer_org_from_api_base
from .service import run_inventory_scan


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inventory GitHub organization repositories into JSON")
    parser.add_argument(
        "--org",
        required=False,
        help="GitHub organization login name. Optional if API_BASE already includes /orgs/<org>/repos",
    )
    parser.add_argument(
        "--token-env",
        default="GITHUB_TOKEN",
        help="Environment variable name that stores a GitHub token (default: GITHUB_TOKEN)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path to output JSON file. Default: ./org_repo_inventory_<org>_<timestamp>.json",
    )
    parser.add_argument(
        "--clone-root",
        default="./.cache/org-repo-clones",
        help="Directory where repositories are shallow-cloned for analysis",
    )
    parser.add_argument(
        "--no-clone",
        action="store_true",
        help="Skip cloning and only capture API metadata",
    )
    parser.add_argument(
        "--force-reclone",
        action="store_true",
        help="Delete and re-clone existing local repo folders",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    org = args.org or infer_org_from_api_base(API_BASE)

    if not org:
        print(
            "Missing organization. Pass --org or set API_BASE to include /orgs/<org>/repos.",
            file=sys.stderr,
        )
        return 1

    token = os.getenv(args.token_env)

    if not token:
        print(
            f"Missing token. Set env var {args.token_env} with a GitHub token that can read org repositories.",
            file=sys.stderr,
        )
        return 1

    output_path = Path(args.output) if args.output else None
    clone_root = Path(args.clone_root)
    do_clone = not args.no_clone

    _, report_path = run_inventory_scan(
        org=org,
        token=token,
        clone_root=clone_root,
        do_clone=do_clone,
        force_reclone=args.force_reclone,
        output_path=output_path,
        progress_callback=print,
    )
    print(f"Report path: {report_path.resolve()}")

    return 0
