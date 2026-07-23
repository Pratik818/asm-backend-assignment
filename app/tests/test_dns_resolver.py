import dns.exception
import dns.resolver
import pytest

from app.models.enums import AssetType
from app.workers.dns_resolver import resolve_records


class _FakeRdata:
    def __init__(self, value: str):
        self._value = value

    def __str__(self) -> str:
        return self._value


def test_resolve_records_returns_values_on_success(monkeypatch):
    def fake_resolve(self, *args, **kwargs):
        return [_FakeRdata("93.184.216.34.")]

    monkeypatch.setattr(dns.resolver.Resolver, "resolve", fake_resolve)

    assert resolve_records("example.org", AssetType.A) == ["93.184.216.34"]


def test_resolve_records_returns_empty_on_no_answer(monkeypatch):
    def fake_resolve(self, *args, **kwargs):
        raise dns.resolver.NoAnswer()

    monkeypatch.setattr(dns.resolver.Resolver, "resolve", fake_resolve)

    assert resolve_records("example.org", AssetType.MX) == []


def test_resolve_records_returns_empty_on_nxdomain(monkeypatch):
    def fake_resolve(self, *args, **kwargs):
        raise dns.resolver.NXDOMAIN()

    monkeypatch.setattr(dns.resolver.Resolver, "resolve", fake_resolve)

    assert resolve_records("does-not-exist.invalid", AssetType.A) == []


def test_resolve_records_retries_transient_failures_then_succeeds(monkeypatch):
    calls = {"count": 0}

    def fake_resolve(self, *args, **kwargs):
        calls["count"] += 1
        if calls["count"] < 3:
            raise dns.exception.Timeout()
        return [_FakeRdata("93.184.216.34")]

    monkeypatch.setattr(dns.resolver.Resolver, "resolve", fake_resolve)

    assert resolve_records("example.org", AssetType.A) == ["93.184.216.34"]
    assert calls["count"] == 3


def test_resolve_records_raises_after_exhausting_retries(monkeypatch):
    calls = {"count": 0}

    def fake_resolve(self, *args, **kwargs):
        calls["count"] += 1
        raise dns.exception.Timeout()

    monkeypatch.setattr(dns.resolver.Resolver, "resolve", fake_resolve)

    with pytest.raises(dns.exception.Timeout):
        resolve_records("example.org", AssetType.A)

    assert calls["count"] == 4
