"""
Checks GitHub for a newer DXVK Manager release.

This only *detects* an update — it never downloads or installs anything.
The GUI shows a notice and links the user to the release page.
"""
import re

import requests

from constants import APP_VERSION

GITHUB_REPO = "xRetr000/DXVK-Manager"
LATEST_RELEASE_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
RELEASES_PAGE = f"https://github.com/{GITHUB_REPO}/releases/latest"


def parse_version(version):
    """
    Turns a version string or tag into a comparable tuple of ints.
    "v0.7" -> (0, 7), "0.7.0" -> (0, 7, 0), "v1.2.3-beta" -> (1, 2, 3).
    Returns () if no number is found.
    """
    match = re.match(r"\s*v?(\d+(?:\.\d+)*)", str(version))
    if not match:
        return ()
    return tuple(int(part) for part in match.group(1).split("."))


def is_newer(candidate, current):
    """True if version `candidate` is strictly newer than `current` (v0.7 == 0.7.0)."""
    a, b = parse_version(candidate), parse_version(current)
    if not a or not b:
        return False
    width = max(len(a), len(b))
    return a + (0,) * (width - len(a)) > b + (0,) * (width - len(b))


def check_for_update(current_version=APP_VERSION, timeout=10):
    """
    Asks GitHub for the latest release. Returns {"version", "url", "name"} when it
    is newer than current_version, otherwise None.

    Any failure (offline, rate-limited, unexpected response) also returns None:
    an update check must never get in the user's way.
    """
    try:
        response = requests.get(
            LATEST_RELEASE_API,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": f"DXVK-Manager/{current_version}",
            },
            timeout=timeout,
        )
        response.raise_for_status()
        release = response.json()
    except (requests.RequestException, ValueError):
        return None

    tag = release.get("tag_name") if isinstance(release, dict) else None
    # /releases/latest already skips drafts and pre-releases; double-check anyway
    if not tag or release.get("draft") or release.get("prerelease"):
        return None
    if not is_newer(tag, current_version):
        return None

    return {
        "version": tag,
        "url": release.get("html_url") or RELEASES_PAGE,
        "name": release.get("name") or tag,
    }
