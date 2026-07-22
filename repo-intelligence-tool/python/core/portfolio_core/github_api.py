from __future__ import annotations

import json
import re
from typing import Any
from urllib import error, parse, request

from .constants import API_BASE


def infer_org_from_api_base(api_base: str) -> str | None:
    match = re.search(r"/orgs/([^/]+)/repos/?$", api_base)
    if match:
        return match.group(1)
    return None


def build_headers(token: str) -> dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "github-org-repo-inventory-script",
    }


def github_get_json(url: str, headers: dict[str, str]) -> Any:
    req = request.Request(url, headers=headers, method="GET")
    try:
        with request.urlopen(req) as resp:
            payload = resp.read().decode("utf-8")
            return json.loads(payload)
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API request failed: {exc.code} {exc.reason}. Body: {body}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Network error calling GitHub API: {exc}") from exc


def get_org_repos(org: str, headers: dict[str, str]) -> list[dict[str, Any]]:
    repos: list[dict[str, Any]] = []
    page = 1
    per_page = 100

    api_base_org = infer_org_from_api_base(API_BASE)
    if api_base_org:
        base_url = API_BASE.rstrip("/")
    else:
        base_url = f"{API_BASE.rstrip('/')}/orgs/{org}/repos"

    while True:
        query = parse.urlencode({"per_page": per_page, "page": page, "type": "all"})
        url = f"{base_url}?{query}"
        batch = github_get_json(url, headers)
        if not isinstance(batch, list):
            raise RuntimeError(f"Unexpected API response while listing org repos: {batch}")
        if not batch:
            break
        repos.extend(batch)
        page += 1

    return repos
