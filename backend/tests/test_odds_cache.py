"""Odds responses are memoized — one usage credit has to serve every visitor
polling the board for the length of the TTL."""
import app.modules.providers.the_odds_provider as provider


async def test_second_call_within_ttl_does_not_refetch():
    provider._cache.clear()
    calls = 0

    async def fetch():
        nonlocal calls
        calls += 1
        return ["odds"]

    assert await provider.cached("k", 60.0, fetch) == ["odds"]
    assert await provider.cached("k", 60.0, fetch) == ["odds"]
    assert calls == 1


async def test_expired_entry_refetches():
    provider._cache.clear()
    calls = 0

    async def fetch():
        nonlocal calls
        calls += 1
        return calls

    assert await provider.cached("k", 0.0, fetch) == 1
    assert await provider.cached("k", 0.0, fetch) == 2
