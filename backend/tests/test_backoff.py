from app.core.llm.backoff import compute_backoff, parse_retry_delay_seconds


def test_parse_retry_delay_seconds():
    assert parse_retry_delay_seconds("42s") == 42.0
    assert parse_retry_delay_seconds("1.5s") == 1.5
    assert parse_retry_delay_seconds("retryDelay: 7s") == 7.0
    assert parse_retry_delay_seconds(30) == 30.0
    assert parse_retry_delay_seconds(None) is None
    assert parse_retry_delay_seconds("nope") is None


def test_compute_backoff_jitter_bounds():
    # Equal jitter: result lands in [capped/2, capped]. capped = min(base*2**attempt, max).
    lo = compute_backoff(0, base_delay=2, max_delay=60, rand=lambda: 0.0)
    hi = compute_backoff(0, base_delay=2, max_delay=60, rand=lambda: 1.0)
    assert lo == 1.0  # capped=2, half=1, 1+0
    assert hi == 2.0  # 1+1*1


def test_compute_backoff_grows_and_caps():
    with_fixed = lambda a: compute_backoff(a, base_delay=2, max_delay=16, rand=lambda: 0.5)
    assert with_fixed(0) < with_fixed(1) < with_fixed(2)  # exponential growth
    # capped at max_delay=16 -> [8, 16]; further attempts stay capped
    assert with_fixed(5) == with_fixed(6) == 12.0


def test_compute_backoff_honors_server_delay():
    # Server asked for longer than our computed/capped value -> never retry sooner.
    assert compute_backoff(0, base_delay=2, max_delay=60, server_delay=45.0, rand=lambda: 0.0) == 45.0
    # Server asked for less than computed -> keep the computed (jittered) value.
    assert compute_backoff(3, base_delay=2, max_delay=60, server_delay=1.0, rand=lambda: 1.0) == 16.0
