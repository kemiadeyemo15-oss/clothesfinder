from app.core.allowlist import get_allowlist


def test_trusted_and_denied():
    al = get_allowlist()
    assert al.is_trusted("COS")
    assert not al.is_trusted("SHEIN")
    assert al.is_denied("SHEIN")
    assert al.is_denied("temu")  # case-insensitive


def test_trust_score_monotonic_in_speed():
    al = get_allowlist()
    fast = al.trust_score("John Lewis")   # 2 days
    slow = al.trust_score("Everlane")     # 7 days
    assert fast > slow
    assert 0.0 <= slow <= fast <= 1.0
    assert al.trust_score("SHEIN") == 0.0  # untrusted
