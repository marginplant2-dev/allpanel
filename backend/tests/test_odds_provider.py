"""Grid prices must be the best per outcome and keep the bookmaker that offered them."""
from app.modules.providers.base import best_h2h_odds as _h2h_odds


def test_best_price_per_outcome_keeps_bookmaker():
    bookmakers = [
        {
            "key": "bet365",
            "title": "Bet365",
            "markets": [
                {"key": "h2h", "outcomes": [{"name": "India", "price": 1.8}, {"name": "Draw", "price": 3.4}]},
                {"key": "totals", "outcomes": [{"name": "Over", "price": 99.0}]},
            ],
        },
        {
            "key": "pinnacle",
            "title": "Pinnacle",
            "markets": [{"key": "h2h", "outcomes": [{"name": "India", "price": 2.1}]}],
        },
    ]
    odds = {o["name"]: o for o in _h2h_odds(bookmakers)}

    assert set(odds) == {"India", "Draw"}  # totals market ignored
    assert odds["India"]["price"] == 2.1
    assert odds["India"]["bookmaker_key"] == "pinnacle"
    assert odds["Draw"]["bookmaker_key"] == "bet365"


def test_missing_or_bad_prices_are_skipped():
    assert _h2h_odds([]) == []
    assert _h2h_odds([{"key": "x", "markets": [{"key": "h2h", "outcomes": [{"name": "A", "price": None}]}]}]) == []
