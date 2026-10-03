"""
NBA Data Client via ESPN Public API
Provides robust, reliable, and real-time access to NBA scoreboards, boxscores,
player statistics, standings, and game summaries without requiring API keys.
"""

import json
import logging
import urllib.request
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

BASE_API = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
STANDINGS_API = "https://site.api.espn.com/apis/v2/sports/basketball/nba/standings"


def _http_get(url: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return None


def get_target_date_str(override_date: str = "") -> str:
    """
    Returns the YYYYMMDD string for the games that happened during the night in France.
    At 7:30 AM French time, night games correspond to yesterday's US date.
    """
    if override_date and len(override_date) == 8 and override_date.isdigit():
        return override_date
    
    # Calculate yesterday's date in US Eastern Time (UTC-5)
    now_utc = datetime.now(timezone.utc)
    us_time = now_utc - timedelta(hours=8)
    return us_time.strftime("%Y%m%d")


def get_scoreboard(date_str: str) -> List[Dict[str, Any]]:
    """
    Fetches the games of the given date.
    """
    url = f"{BASE_API}/scoreboard?dates={date_str}"
    data = _http_get(url)
    if not data or "events" not in data:
        return []

    games = []
    for ev in data.get("events", []):
        try:
            comp = ev.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            
            home_comp = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0] if competitors else {})
            away_comp = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1] if len(competitors) > 1 else {})

            status_type = comp.get("status", {}).get("type", {})
            is_final = status_type.get("completed", False) or status_type.get("state") == "post"
            is_live = status_type.get("state") == "in"
            
            # Broadcasts
            broadcasts = []
            for b in comp.get("broadcasts", []):
                for name in b.get("names", []):
                    broadcasts.append(name)
            for geo in comp.get("geoBroadcasts", []):
                media_name = geo.get("media", {}).get("shortName", "")
                if media_name and media_name not in broadcasts:
                    broadcasts.append(media_name)

            game = {
                "id": ev.get("id"),
                "name": ev.get("name"),
                "shortName": ev.get("shortName"),
                "date": ev.get("date"),
                "is_final": is_final,
                "is_live": is_live,
                "status_detail": status_type.get("detail", "Inconnu"),
                "broadcasts": broadcasts,
                "home": {
                    "id": home_comp.get("team", {}).get("id"),
                    "name": home_comp.get("team", {}).get("displayName"),
                    "shortName": home_comp.get("team", {}).get("shortDisplayName"),
                    "abbrev": home_comp.get("team", {}).get("abbreviation"),
                    "score": int(home_comp.get("score", 0)) if home_comp.get("score") else 0,
                    "record": home_comp.get("records", [{}])[0].get("summary", "") if home_comp.get("records") else "",
                    "logo": home_comp.get("team", {}).get("logo", ""),
                    "color": home_comp.get("team", {}).get("color", "000000"),
                    "winner": home_comp.get("winner", False)
                },
                "away": {
                    "id": away_comp.get("team", {}).get("id"),
                    "name": away_comp.get("team", {}).get("displayName"),
                    "shortName": away_comp.get("team", {}).get("shortDisplayName"),
                    "abbrev": away_comp.get("team", {}).get("abbreviation"),
                    "score": int(away_comp.get("score", 0)) if away_comp.get("score") else 0,
                    "record": away_comp.get("records", [{}])[0].get("summary", "") if away_comp.get("records") else "",
                    "logo": away_comp.get("team", {}).get("logo", ""),
                    "color": away_comp.get("team", {}).get("color", "000000"),
                    "winner": away_comp.get("winner", False)
                }
            }
            games.append(game)
        except Exception as err:
            logger.warning(f"Error parsing game {ev.get('id')}: {err}")

    return games


def get_game_boxscore(game_id: str) -> Dict[str, Any]:
    """
    Fetches full game summary including boxscore with individual stats for EVERY player.
    """
    url = f"{BASE_API}/summary?event={game_id}"
    data = _http_get(url)
    if not data:
        return {}

    boxscore = {"teams": []}
    players_data = data.get("boxscore", {}).get("players", [])

    for team_entry in players_data:
        team_info = team_entry.get("team", {})
        stats_sections = team_entry.get("statistics", [])
        if not stats_sections:
            continue

        sec = stats_sections[0]
        stat_names = sec.get("names", [])
        athletes = sec.get("athletes", [])

        team_players = []
        for ath in athletes:
            ath_info = ath.get("athlete", {})
            raw_stats = ath.get("stats", [])
            stats_dict = dict(zip(stat_names, raw_stats)) if len(stat_names) == len(raw_stats) else {}

            # Parse stats numbers safely
            def to_int(val: Any) -> int:
                try:
                    return int(val)
                except (ValueError, TypeError):
                    return 0

            pts = to_int(stats_dict.get("PTS", 0))
            reb = to_int(stats_dict.get("REB", 0))
            ast = to_int(stats_dict.get("AST", 0))
            stl = to_int(stats_dict.get("STL", 0))
            blk = to_int(stats_dict.get("BLK", 0))
            tov = to_int(stats_dict.get("TO", 0))

            # GameScore calculation (Hollinger formula for impact)
            # GameScore = PTS + 0.4*FG - 0.7*FGA - 0.4*(FTA-FT) + 0.7*ORB + 0.3*DRB + STL + 0.7*AST + 0.7*BLK - 0.4*PF - TO
            # Simplified proxy if shot splits are strings:
            game_score = pts + (reb * 1.2) + (ast * 1.5) + (stl * 2.0) + (blk * 2.0) - (tov * 1.5)

            player_item = {
                "id": ath_info.get("id"),
                "name": ath_info.get("displayName"),
                "shortName": ath_info.get("shortName"),
                "jersey": ath_info.get("jersey", ""),
                "position": ath_info.get("position", {}).get("abbreviation", ""),
                "starter": ath.get("starter", False),
                "minutes": stats_dict.get("MIN", "--"),
                "pts": pts,
                "reb": reb,
                "ast": ast,
                "stl": stl,
                "blk": blk,
                "tov": tov,
                "fg": stats_dict.get("FG", "-"),
                "three_pt": stats_dict.get("3PT", "-"),
                "ft": stats_dict.get("FT", "-"),
                "plus_minus": stats_dict.get("+/-", "-"),
                "game_score": round(game_score, 1),
                "did_not_play": ath.get("didNotPlay", False)
            }
            team_players.append(player_item)

        boxscore["teams"].append({
            "team_id": team_info.get("id"),
            "team_name": team_info.get("displayName"),
            "team_abbrev": team_info.get("abbreviation"),
            "players": team_players
        })

    return boxscore


def get_standings() -> Dict[str, Dict[str, Any]]:
    """
    Fetches standings for all 30 NBA teams, indexed by team abbreviation or name.
    """
    data = _http_get(STANDINGS_API)
    if not data or "children" not in data:
        return {}

    standings = {}
    for conf in data.get("children", []):
        conf_name = "Est" if "East" in conf.get("name", "") else "Ouest"
        entries = conf.get("standings", {}).get("entries", [])
        
        for rank, entry in enumerate(entries, start=1):
            team = entry.get("team", {})
            stats_list = entry.get("stats", [])
            stats_dict = {s.get("name"): s.get("displayValue", "") for s in stats_list}

            streak = stats_dict.get("streak", "-")
            l10 = stats_dict.get("L10", "-")
            diff = stats_dict.get("differential", "0")
            wins = stats_dict.get("wins", "0")
            losses = stats_dict.get("losses", "0")
            playoff_seed = stats_dict.get("playoffSeed", str(rank))

            team_record = {
                "team_name": team.get("displayName"),
                "team_abbrev": team.get("abbreviation"),
                "conference": conf_name,
                "rank": playoff_seed,
                "record": f"{wins}-{losses}",
                "wins": int(wins) if wins.isdigit() else 0,
                "losses": int(losses) if losses.isdigit() else 0,
                "streak": streak,
                "l10": l10,
                "differential": diff
            }

            if team.get("abbreviation"):
                standings[team.get("abbreviation").upper()] = team_record
            if team.get("displayName"):
                standings[team.get("displayName").lower()] = team_record

    return standings


def get_upcoming_games() -> List[Dict[str, Any]]:
    """
    Fetches games scheduled for tonight/tomorrow.
    """
    now_utc = datetime.now(timezone.utc)
    # Today's evening in US
    today_str = now_utc.strftime("%Y%m%d")
    games = get_scoreboard(today_str)
    
    # Keep only scheduled or live games
    upcoming = [g for g in games if not g.get("is_final")]
    return upcoming
