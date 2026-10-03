"""
Team Analysis Module
Computes team momentum, standings, win/loss streaks, and recent 10-game form (L10).
"""

from typing import Dict, Any, Optional


def format_streak(streak_str: str) -> str:
    """Formats streak with visual indicator."""
    if not streak_str or streak_str == "-":
        return "-"
    
    streak_upper = streak_str.upper()
    if streak_upper.startswith("W"):
        count = streak_upper.replace("W", "").strip()
        return f"🔥 {count}V d'affilée" if int(count) >= 3 else f"🟢 {count}V"
    elif streak_upper.startswith("L"):
        count = streak_upper.replace("L", "").strip()
        return f"❄️ {count}D de suite" if int(count) >= 3 else f"🔴 {count}D"
    return streak_str


def analyze_team_form(team_abbrev: str, team_name: str, standings: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extracts and computes form metrics for a team from the standings.
    """
    record_data = standings.get(team_abbrev.upper()) or standings.get(team_name.lower()) or {}
    
    rank = record_data.get("rank", "-")
    conference = record_data.get("conference", "")
    record = record_data.get("record", "")
    raw_streak = record_data.get("streak", "-")
    l10 = record_data.get("l10", "-")
    differential = record_data.get("differential", "0")

    formatted_streak = format_streak(raw_streak)

    # Momentum summary
    status_tag = ""
    if raw_streak.startswith("W") and len(raw_streak) > 1 and int(raw_streak[1:]) >= 3:
        status_tag = "En grande forme"
    elif raw_streak.startswith("L") and len(raw_streak) > 1 and int(raw_streak[1:]) >= 3:
        status_tag = "En difficulté"
    else:
        status_tag = "Stable"

    return {
        "team_name": team_name,
        "team_abbrev": team_abbrev,
        "rank": rank,
        "conference": conference,
        "record": record,
        "streak_raw": raw_streak,
        "streak_formatted": formatted_streak,
        "l10": l10,
        "differential": differential,
        "status_tag": status_tag,
        "summary": f"{rank}e {conference} ({record}) • Série: {formatted_streak} • L10: {l10}"
    }


def compare_matchup_form(home_form: Dict[str, Any], away_form: Dict[str, Any]) -> str:
    """
    Produces a 1-line narrative summary of the matchup dynamics.
    """
    away_desc = f"{away_form.get('team_name')} ({away_form.get('streak_formatted')}, {away_form.get('rank')}e {away_form.get('conference')})"
    home_desc = f"{home_form.get('team_name')} ({home_form.get('streak_formatted')}, {home_form.get('rank')}e {home_form.get('conference')})"
    return f"{away_desc} vs {home_desc}"
