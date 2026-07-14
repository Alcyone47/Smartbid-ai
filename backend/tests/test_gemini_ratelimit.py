from types import SimpleNamespace

from app.core.llm.gemini_provider import _is_rate_limit, _retry_delay_from_error


def test_is_rate_limit_by_code():
    assert _is_rate_limit(SimpleNamespace(code=429, status="")) is True


def test_is_rate_limit_by_status():
    assert _is_rate_limit(SimpleNamespace(code=500, status="RESOURCE_EXHAUSTED")) is True


def test_is_not_rate_limit():
    assert _is_rate_limit(SimpleNamespace(code=500, status="INTERNAL")) is False


def test_retry_delay_from_list_details():
    exc = SimpleNamespace(
        details=[
            {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "12s"},
        ]
    )
    assert _retry_delay_from_error(exc) == 12.0


def test_retry_delay_from_nested_error_dict():
    exc = SimpleNamespace(
        details={"error": {"details": [{"@type": "google.rpc.RetryInfo", "retryDelay": "3.5s"}]}}
    )
    assert _retry_delay_from_error(exc) == 3.5


def test_retry_delay_absent():
    assert _retry_delay_from_error(SimpleNamespace(details=None)) is None
