import os
import re
from unittest.mock import MagicMock, patch

import pytest
import requests

from constants import APP_VERSION
from update_checker import RELEASES_PAGE, check_for_update, is_newer, parse_version


def _release_response(payload, status=200):
    resp = MagicMock()
    resp.json = lambda: payload
    if status >= 400:
        resp.raise_for_status.side_effect = requests.HTTPError(f"{status}")
    else:
        resp.raise_for_status = lambda: None
    return resp


def test_app_version_matches_pyproject():
    """The version the app reports must be the one being released."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Regex rather than tomllib, which only exists on Python 3.11+ (CI also runs 3.10)
    with open(os.path.join(root, "pyproject.toml"), encoding="utf-8") as f:
        match = re.search(r'^version\s*=\s*"([^"]+)"', f.read(), re.MULTILINE)
    assert match and match.group(1) == APP_VERSION


@pytest.mark.parametrize("text,expected", [
    ("v0.7", (0, 7)),
    ("0.7.0", (0, 7, 0)),
    ("v1.2.3-beta", (1, 2, 3)),
    ("V2", ()),            # capital V isn't a tag format we use
    ("latest", ()),
    ("", ()),
])
def test_parse_version(text, expected):
    assert parse_version(text) == expected


@pytest.mark.parametrize("candidate,current,newer", [
    ("v0.8", "0.7.0", True),
    ("v0.7.1", "0.7.0", True),
    ("v1.0", "0.7.0", True),
    ("v0.10", "0.9.0", True),     # numeric, not string, comparison
    ("v0.7", "0.7.0", False),     # same version, different padding
    ("v0.7.0", "0.7", False),
    ("v0.6", "0.7.0", False),
    ("garbage", "0.7.0", False),
])
def test_is_newer(candidate, current, newer):
    assert is_newer(candidate, current) is newer


def test_newer_release_is_reported():
    payload = {"tag_name": "v0.8", "name": "v0.8", "html_url": "https://github.com/x/y/releases/tag/v0.8"}
    with patch("update_checker.requests.get", return_value=_release_response(payload)):
        assert check_for_update("0.7.0") == {
            "version": "v0.8",
            "url": "https://github.com/x/y/releases/tag/v0.8",
            "name": "v0.8",
        }


def test_same_or_older_release_is_ignored():
    for tag in ("v0.7", "v0.6"):
        with patch("update_checker.requests.get", return_value=_release_response({"tag_name": tag})):
            assert check_for_update("0.7.0") is None


def test_missing_html_url_falls_back_to_releases_page():
    with patch("update_checker.requests.get", return_value=_release_response({"tag_name": "v0.8"})):
        assert check_for_update("0.7.0")["url"] == RELEASES_PAGE


@pytest.mark.parametrize("flag", ["draft", "prerelease"])
def test_draft_and_prerelease_are_ignored(flag):
    payload = {"tag_name": "v0.8", flag: True}
    with patch("update_checker.requests.get", return_value=_release_response(payload)):
        assert check_for_update("0.7.0") is None


@pytest.mark.parametrize("failure", [
    requests.ConnectionError("offline"),
    requests.Timeout("slow"),
])
def test_network_errors_are_silent(failure):
    with patch("update_checker.requests.get", side_effect=failure):
        assert check_for_update("0.7.0") is None


def test_http_error_is_silent():
    """e.g. 403 when GitHub's unauthenticated rate limit is hit."""
    with patch("update_checker.requests.get", return_value=_release_response({}, status=403)):
        assert check_for_update("0.7.0") is None


def test_bad_json_is_silent():
    resp = _release_response(None)
    resp.json = MagicMock(side_effect=ValueError("not json"))
    with patch("update_checker.requests.get", return_value=resp):
        assert check_for_update("0.7.0") is None


def test_non_dict_json_is_silent():
    with patch("update_checker.requests.get", return_value=_release_response(["unexpected"])):
        assert check_for_update("0.7.0") is None


def test_request_sends_user_agent_and_timeout():
    with patch("update_checker.requests.get", return_value=_release_response({"tag_name": "v0.1"})) as get:
        check_for_update("0.7.0", timeout=5)
    _, kwargs = get.call_args
    assert kwargs["timeout"] == 5
    assert kwargs["headers"]["User-Agent"] == "DXVK-Manager/0.7.0"
