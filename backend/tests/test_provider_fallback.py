"""A failing live provider must degrade to seeded data — and stay there briefly,
so the sports list and the events board keep coming from the same id space."""
import app.modules.providers.provider_factory as factory
from app.modules.providers.provider_factory import FallbackSportsProvider


class Boom:
    key = "boom"

    def __init__(self):
        self.calls = 0

    async def get_sports(self):
        self.calls += 1
        raise RuntimeError("401 Unauthorized")

    async def get_events(self, *, sport_id=None, status=None):
        self.calls += 1
        raise RuntimeError("401 Unauthorized")

    async def get_event_detail(self, event_id):
        raise RuntimeError("401 Unauthorized")

    async def get_live_data(self, event_id):
        raise RuntimeError("401 Unauthorized")


class Seeded:
    key = "seeded"

    async def get_sports(self):
        return [{"id": "cricket", "name": "Cricket"}]

    async def get_events(self, *, sport_id=None, status=None):
        return [{"id": "e1", "sport_id": "cricket"}]

    async def get_event_detail(self, event_id):
        return {"id": event_id}

    async def get_live_data(self, event_id):
        return {"event_id": event_id, "status": "live", "score": {}}


async def test_falls_back_and_sticks(monkeypatch):
    monkeypatch.setattr(factory, "_backup_until", 0.0)
    primary = Boom()
    provider = FallbackSportsProvider(primary, Seeded())

    assert await provider.get_sports() == [{"id": "cricket", "name": "Cricket"}]
    assert primary.calls == 1

    # cooldown: the dead provider is not retried on the next call
    assert await provider.get_events() == [{"id": "e1", "sport_id": "cricket"}]
    assert primary.calls == 1


async def test_unknown_event_id_falls_through_to_seeded(monkeypatch):
    """A healthy live provider returns None for a seeded event id — not an error,
    but the seeded board still has to answer or the event page breaks."""
    monkeypatch.setattr(factory, "_backup_until", 0.0)

    class NotMine(Seeded):
        key = "notmine"

        async def get_event_detail(self, event_id):
            return None

    provider = FallbackSportsProvider(NotMine(), Seeded())
    assert await provider.get_event_detail("6a9440a032ec2f6adb557155") == {"id": "6a9440a032ec2f6adb557155"}


async def test_live_provider_used_while_healthy(monkeypatch):
    monkeypatch.setattr(factory, "_backup_until", 0.0)
    provider = FallbackSportsProvider(Seeded(), Boom())
    assert await provider.get_sports() == [{"id": "cricket", "name": "Cricket"}]
