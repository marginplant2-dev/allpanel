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


def test_board_prices_come_from_match_odds_not_fancy():
    """A fancy market's runners ("4th wkt", "6 over runs") must never land in the
    board's 1/X/2 columns — that is what the event page is for."""
    books = map_bookmakers(
        {
            "matchOdds": [
                {
                    "mid": "1",
                    "mname": "MATCH_ODDS",
                    "mstatus": "OPEN",
                    "oddDatas": [{"rname": "Boland", "b1": "1.5", "l1": "1.6"}],
                }
            ],
            "fancyOdds": [
                {"mid": "2", "mname": "4th wkt NWD", "oddDatas": [{"rname": "4th wkt NWD", "b1": "446", "l1": "446"}]}
            ],
        }
    )
    board = next(b for b in books if b["key"].startswith(("match_odds", "bookmaker")))
    assert board["title"] == "MATCH_ODDS"
    assert [o["name"] for o in board["markets"][0]["outcomes"]] == ["Boland"]


LADDER_PAYLOAD = {
    "matchOdds": [
        {
            "mid": "1",
            "mname": "MATCH_ODDS",
            "mstatus": "OPEN",
            "oddDatas": [
                {
                    "rname": "Afghanistan",
                    "b1": "200.0", "bs1": "29", "b2": "190.0", "bs2": "38", "b3": "170.0", "bs3": "2",
                    "l1": "210.0", "ls1": "36", "l2": "240.0", "ls2": "1", "l3": "280.0", "ls3": "1",
                    "status": "ACTIVE",
                },
                {
                    "rname": "India",
                    "b1": "0", "bs1": "0", "b2": "0", "b3": "0",
                    "l1": "1.01", "ls1": "328208", "l2": "1.02", "ls2": "87490", "l3": "1.03", "ls3": "12112",
                    "status": "ACTIVE",
                },
            ],
        }
    ],
    "fancyOdds": [
        {
            "mid": "9",
            "mname": "FANCY_ODDS",
            "gtype": "normal",
            "mstatus": "Ball Running",
            "oddDatas": [
                {"rname": "10 over run AFG", "b1": "0.0", "l1": "0.0", "status": "Ball Running"},
                {"rname": "6 over run AFG", "b1": "55", "bs1": "100", "l1": "57", "ls1": "100", "status": "SUSPENDED"},
            ],
        }
    ],
}


def test_three_price_levels_with_sizes_survive_the_mapping():
    book = map_bookmakers(LADDER_PAYLOAD)[0]
    afg = book["markets"][0]["outcomes"][0]
    assert [lvl["price"] for lvl in afg["back_ladder"]] == [200.0, 190.0, 170.0]
    assert [lvl["size"] for lvl in afg["back_ladder"]] == ["29", "38", "2"]
    assert [lvl["price"] for lvl in afg["lay_ladder"]] == [210.0, 240.0, 280.0]
    assert afg["price"] == 200.0 and afg["lay"] == 210.0


def test_a_runner_with_no_back_price_keeps_its_lay_side():
    book = map_bookmakers(LADDER_PAYLOAD)[0]
    india = book["markets"][0]["outcomes"][1]
    assert india["back_ladder"][0]["price"] is None
    assert india["lay_ladder"][0]["price"] == 1.01
    assert india["price"] == 1.01  # something to show, never a crash


def test_fancy_keeps_its_gtype_and_per_row_status():
    fancy = next(b for b in map_bookmakers(LADDER_PAYLOAD) if b["kind"] == "fancy")
    assert fancy["gtype"] == "normal"
    rows = fancy["markets"][0]["outcomes"]
    assert rows[0]["status"] == "Ball Running"   # priceless row is still listed
    assert rows[1]["status"] == "SUSPENDED"


SCORE_ROW = {
    "CurrentInning": "2",
    "Team1Name": "Afghanistan", "Team1Name_Short": "AFG",
    "Team1OnlyScore": "57-4 (7.0)", "Team1ScoreOnly": "57-4", "Team1Overs": "7.0",
    "Team2Name": "India", "Team2Name_Short": "IND",
    "Team2OnlyScore": "221-7 (20.0)", "Team2ScoreOnly": "221-7", "Team2Overs": "20.0",
    "CRR": "8.14", "RRR": "12.69", "Target": "222",
    "Last6Balls": ["0", "0", "0", "1", "0", "WB"],
}


def test_score_feeds_both_the_scoreboard_and_settlement():
    from app.modules.providers.proexch_provider import map_score

    out = map_score("cricket:1:1.1", SCORE_ROW)
    # flat shape the settlement worker compares
    assert out["score"] == {"AFG": 57.0, "IND": 221.0}
    board = out["board"]
    assert board["team1"]["score"] == "57-4 (7.0)" and board["team2"]["short"] == "IND"
    assert board["crr"] == "8.14" and board["target"] == "222"
    assert board["last6"] == ["0", "0", "0", "1", "0", "WB"]
    # 222 - 57 = 165 runs, 120 - 42 balls bowled = 78 balls
    assert board["message"] == "AFG need 165 runs from 78 balls"


def test_chase_message_is_dropped_when_there_is_no_target():
    from app.modules.providers.proexch_provider import map_score

    first_innings = {**SCORE_ROW, "Target": "0"}
    assert map_score("cricket:1:1.1", first_innings)["board"]["message"] is None
