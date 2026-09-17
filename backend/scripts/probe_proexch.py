"""Dump the real response shapes of the proexch odds feed.

The Swagger only declares `Map<string, object>` for every endpoint, so the field
names have to come from a live call — and the host answers 403 unless the calling
IP is whitelisted. Run this **from the whitelisted server**:

    python -m scripts.probe_proexch                 # all endpoints
    python -m scripts.probe_proexch --out feed.json # also save the raw payloads

It prints the key structure (not the full dump) so the output stays readable, and
writes the raw JSON when --out is given. Send that file over and the provider can
be mapped exactly instead of guessed.
"""
from __future__ import annotations

import argparse
import json
from typing import Any

import httpx

from app.core.config import settings


def shape(value: Any, depth: int = 0, max_depth: int = 4) -> Any:
    """Collapse a payload into its structure: keys kept, bulk values summarised."""
    if depth >= max_depth:
        return "…"
    if isinstance(value, dict):
        return {k: shape(v, depth + 1, max_depth) for k, v in value.items()}
    if isinstance(value, list):
        if not value:
            return []
        return [shape(value[0], depth + 1, max_depth), f"…{len(value)} items"]
    if isinstance(value, str):
        return value if len(value) <= 40 else value[:40] + "…"
    return value


def get(client: httpx.Client, path: str, **params: Any) -> Any:
    r = client.get(settings.proexch_base_url + path, params=params or None)
    r.raise_for_status()
    return r.json()


def first_game_id(payload: Any) -> str | None:
    """Pull any id-looking field out of a match list, whatever it is called."""
    data = payload.get("data") if isinstance(payload, dict) else payload
    while isinstance(data, dict):
        data = next((v for v in data.values() if isinstance(v, (list, dict))), None)
    if not isinstance(data, list) or not data:
        return None
    row = data[0]
    if not isinstance(row, dict):
        return None
    for key in ("gameId", "gmid", "eventId", "etid", "id", "marketId", "mid"):
        if row.get(key):
            return str(row[key])
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", help="write the raw payloads to this JSON file")
    parser.add_argument("--timeout", type=float, default=20.0)
    args = parser.parse_args()

    # The vendor whitelists a domain as well as an IP; send it or the call may 403
    # even from the right server.
    headers = {"Accept": "application/json"}
    if settings.proexch_origin:
        headers["Origin"] = settings.proexch_origin
        headers["Referer"] = settings.proexch_origin.rstrip("/") + "/"
    print(f"[probe] {settings.proexch_base_url} as {settings.proexch_origin or '(no Origin set)'}")

    raw: dict[str, Any] = {}
    with httpx.Client(timeout=args.timeout, headers=headers) as client:
        for sport in ("cricket", "soccer", "tennis"):
            path = f"/api/{sport}/matches"
            try:
                payload = get(client, path)
            except Exception as exc:  # noqa: BLE001 — a probe reports, it does not fail
                print(f"{path}: FAILED — {exc}")
                continue
            raw[path] = payload
            print(f"\n=== {path} ===")
            print(json.dumps(shape(payload), indent=1)[:2000])

            game_id = first_game_id(payload)
            if not game_id:
                print(f"({sport}: no game id found in the list — check the keys above)")
                continue
            odds_path = f"/api/cricket/odds" if sport == "cricket" else f"/api/{sport}/data"
            try:
                odds = get(client, odds_path, gameId=game_id)
            except Exception as exc:  # noqa: BLE001
                print(f"{odds_path}?gameId={game_id}: FAILED — {exc}")
                continue
            raw[f"{odds_path}?gameId={game_id}"] = odds
            print(f"\n=== {odds_path}?gameId={game_id} ===")
            print(json.dumps(shape(odds), indent=1)[:3000])

        for path in ("/api/score-fixture",):
            try:
                payload = get(client, path)
            except Exception as exc:  # noqa: BLE001
                print(f"{path}: FAILED — {exc}")
                continue
            raw[path] = payload
            print(f"\n=== {path} ===")
            print(json.dumps(shape(payload), indent=1)[:2000])

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(raw, fh, indent=1, ensure_ascii=False)
        print(f"\n[probe] raw payloads written to {args.out}")


if __name__ == "__main__":
    main()
