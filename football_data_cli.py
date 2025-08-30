#!/usr/bin/env python3
# Football-Data.org CLI (Python 3.9+)
# PASTE YOUR API KEY HERE:

API_KEY = "077ce3f148ea4b05a9dca097ff96948f"

import argparse
import json
import sys
import time
from pathlib import Path

import requests

BASE = "https://api.football-data.org/v4"

if not API_KEY or "PASTE_" in API_KEY:
    print("❌ Set API_KEY at the top of the file.", file=sys.stderr)
    sys.exit(1)


def get_json(url: str, params: dict | None = None) -> dict:
    """GET JSON with simple 429 backoff."""
    tries = 0
    while tries < 3:
        res = requests.get(url, headers={"X-Auth-Token": API_KEY}, params=params)
        if res.status_code == 429:
            wait = 1.5 * (tries + 1)
            print(f"⚠️  429 rate-limit. Backing off {wait:.1f}s…", file=sys.stderr)
            time.sleep(wait)
            tries += 1
            continue
        if not res.ok:
            try:
                payload = res.json()
            except Exception:
                payload = res.text
            raise RuntimeError(f"HTTP {res.status_code} — {payload}")
        return res.json()
    raise RuntimeError("Too many 429s — try again later.")


def save_if_requested(data: dict, out: str | None):
    if not out:
        return
    fp = Path(out).resolve()
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"💾 Saved -> {fp}")


def cmd_competitions(args):
    url = f"{BASE}/competitions"
    data = get_json(url)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    save_if_requested(data, args.out)


def cmd_matches(args):
    params = {
        "dateFrom": args.dateFrom,  # YYYY-MM-DD
        "dateTo": args.dateTo,      # YYYY-MM-DD
        "status": args.status,      # SCHEDULED|LIVE|FINISHED|TIMED|IN_PLAY|PAUSED|POSTPONED|SUSPENDED|CANCELED
        "competitions": args.competition,  # PL, BL1, PD, SA, FL1, CL, EL, ... (comma-separated allowed)
    }
    url = f"{BASE}/matches"
    data = get_json(url, params=params)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    save_if_requested(data, args.out)


def cmd_standings(args):
    comp = args.competition or "PL"
    params = {}
    if args.season:
        params["season"] = args.season
    url = f"{BASE}/competitions/{comp}/standings"
    data = get_json(url, params=params)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    save_if_requested(data, args.out)


def cmd_scorers(args):
    comp = args.competition or "PL"
    params = {}
    if args.limit:
        params["limit"] = args.limit
    if args.season:
        params["season"] = args.season
    url = f"{BASE}/competitions/{comp}/scorers"
    data = get_json(url, params=params)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    save_if_requested(data, args.out)


def build_parser():
    p = argparse.ArgumentParser(description="Football-Data.org CLI")
    sub = p.add_subparsers(dest="cmd")

    s = sub.add_parser("competitions", help="List competitions")
    s.add_argument("--out", help="Save JSON to file")
    s.set_defaults(func=cmd_competitions)

    s = sub.add_parser("matches", help="List matches")
    s.add_argument("--dateFrom", help="YYYY-MM-DD")
    s.add_argument("--dateTo", help="YYYY-MM-DD")
    s.add_argument("--status", help="SCHEDULED|LIVE|FINISHED|TIMED|IN_PLAY|PAUSED|POSTPONED|SUSPENDED|CANCELED")
    s.add_argument("--competition", help="PL, BL1, PD, SA, FL1, CL, EL, ... (comma-separated allowed)")
    s.add_argument("--out", help="Save JSON to file")
    s.set_defaults(func=cmd_matches)

    s = sub.add_parser("standings", help="League standings")
    s.add_argument("--competition", help="e.g. PL")
    s.add_argument("--season", help="e.g. 2024")
    s.add_argument("--out", help="Save JSON to file")
    s.set_defaults(func=cmd_standings)

    s = sub.add_parser("scorers", help="Top scorers for league")
    s.add_argument("--competition", help="e.g. PL")
    s.add_argument("--limit", type=int, help="e.g. 10")
    s.add_argument("--season", help="e.g. 2024")
    s.add_argument("--out", help="Save JSON to file")
    s.set_defaults(func=cmd_scorers)

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        sys.exit(0)
    try:
        args.func(args)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
