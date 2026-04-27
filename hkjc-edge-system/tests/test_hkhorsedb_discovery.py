from __future__ import annotations

from src.hkhorsedb.discovery import _is_membership_restricted


def test_membership_restriction_detected() -> None:
    html = "<html><body>會員登入 Login Password</body></html>"
    assert _is_membership_restricted(html) is True


def test_membership_restriction_not_detected_for_public_text() -> None:
    html = "<html><body>public horse database home page</body></html>"
    assert _is_membership_restricted(html) is False
