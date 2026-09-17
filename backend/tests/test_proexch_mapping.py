"""Mapping of the proexch feed onto the app's event/odds shape.

Recorded from live responses: the Swagger declares only Map<string,object>, so
these fixtures are the contract.
"""
from app.modules.providers.proexch_provider import (
    list_odds,
    map_bookmakers,
    map_event,
    price,
    to_utc,
)

CRICKET_ROW = {
    "gameId": "36076341",
    "marketId": "1.262483616",
    "eventId": "36076341",
    "eventName": "Zimbabwe W v South Africa W",
    "runnerName1": "Zimbabwe W",
    "runnerName2": "South Africa W",
    "runnerName3": None,
    "eventTime": "2026-09-17T17:00",
    "inPlay": False,
    "tv": True,
    "back1": 1.85,
    "lay1": 1.88,
    "back11": 2.02,
    "lay11": 2.06,
    "back12": 0.0,
    "lay12": 0.0,
    "seriesName": "Zimbabwe Women tour",
}

SOCCER_ROW = {
    "eventId": "36004955",
    "marketId": "1.261740131",
    "eventName": "PFC Levski Sofia v Red Bull Salzburg",
    "eventDate": "2026-09-17T22:15",
    "runnerName1": "PFC Levski Sofia",
    "runnerName2": "Red Bull Salzburg",
    "runnerName3": "The Draw",
    "seriesName": "EUROPE Europa League",
    "inPlay": None,
}

ODDS_PAYLOAD = {
    "matchOdds": [
        {
            "mid": "1.262469350",
            "market": "Match Odds",
            "mname": "MATCH_ODDS",
            "mstatus": "OPEN",
            "min": 100,
            "max": 50000,
            "oddDatas": [
                {"sid": 1, "rname": "Malaysia W", "b1": "55.0", "bs1": "1", "l1": "85.0", "status": "ACTIVE"},
                {"sid": 2, "rname": "Sri Lanka W", "b1": "1.01", "bs1": "224", "l1": "1.02", "status": "ACTIVE"},
            ],
        }
    ],
    "bookMakerOdds": [],
    "fancyOdds": [
        {
            "mid": "99",
            "mname": "6 OVER RUNS",
            "mstatus": "SUSPENDED",
            "oddDatas": [{"sid": 9, "rname": "6 over runs", "b1": "55", "l1": "57", "status": "ACTIVE"}],
        }
    ],
    "otherMarketOdds": [],
}


def test_times_are_ist_converted_to_utc():
    assert to_utc("2026-09-17T22:15") == "2026-09-17T16:45:00Z"
    assert to_utc(None) is None
    assert to_utc("garbage") is None


def test_zero_and_junk_prices_are_dropped():
    assert price("1.85") == 1.85
    assert price("0") == 0.0
    assert price(1.0) == 0.0  # a price of 1 pays nothing
    assert price(None) == 0.0


def test_cricket_row_maps_to_event_with_grid_odds():
    e = map_event("cricket", CRICKET_ROW)
    assert e["id"] == "cricket:36076341:1.262483616"
    assert e["participants"] == ["Zimbabwe W", "South Africa W"]  # no draw slot
    assert e["start_time"] == "2026-09-17T11:30:00Z"
    assert e["league"] == "Zimbabwe Women tour"
    names = [o["name"] for o in e["odds"]]
    assert names == ["Zimbabwe W", "South Africa W"]
    assert e["odds"][0]["price"] == 1.85 and e["odds"][0]["lay"] == 1.88


def test_soccer_row_keeps_the_draw_in_the_middle():
    e = map_event("soccer", SOCCER_ROW)
    assert e["id"] == "soccer:36004955:1.261740131"
    assert e["participants"] == ["PFC Levski Sofia", "The Draw", "Red Bull Salzburg"]
    assert e["odds"] == []  # the soccer list carries no prices


def test_rows_without_ids_are_skipped():
    assert map_event("cricket", {"eventName": "x"}) is None


def test_each_market_becomes_its_own_box():
    books = map_bookmakers(ODDS_PAYLOAD)
    assert [b["title"] for b in books] == ["MATCH_ODDS", "6 OVER RUNS"]
    assert books[0]["key"] == "match_odds:1.262469350"
    assert books[0]["suspended"] is False
    assert books[1]["suspended"] is True  # mstatus SUSPENDED
    outcomes = books[0]["markets"][0]["outcomes"]
    assert [o["name"] for o in outcomes] == ["Malaysia W", "Sri Lanka W"]
    assert outcomes[0]["price"] == 55.0 and outcomes[0]["lay"] == 85.0


def test_empty_payload_yields_no_books():
    assert map_bookmakers({}) == []
    assert list_odds({}) == []
