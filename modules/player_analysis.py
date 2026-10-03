"""
Player Analysis Module
Computes player impact (Game Score), extracts top performers of the night,
detects double/triple-doubles, and tracks French NBA players.
"""

from typing import List, Dict, Any

# Roster of prominent French players in the NBA (active 2024-2026)
FRENCH_PLAYERS = {
    "victor wembanyama": "Victor Wembanyama",
    "wembanyama": "Victor Wembanyama",
    "zaccharie risacher": "Zaccharie Risacher",
    "risacher": "Zaccharie Risacher",
    "alexandre sarr": "Alexandre Sarr",
    "alex sarr": "Alexandre Sarr",
    "bilal coulibaly": "Bilal Coulibaly",
    "coulibaly": "Bilal Coulibaly",
    "rudy gobert": "Rudy Gobert",
    "gobert": "Rudy Gobert",
    "tidjane salaun": "Tidjane Salaün",
    "tidjane salaün": "Tidjane Salaün",
    "guerschon yabusele": "Guerschon Yabusele",
    "yabusele": "Guerschon Yabusele",
    "pacome dadiet": "Pacôme Dadiet",
    "pacôme dadiet": "Pacôme Dadiet",
    "nicolas batum": "Nicolas Batum",
    "batum": "Nicolas Batum",
    "ousmane dieng": "Ousmane Dieng",
    "rayan rupert": "Rayan Rupert",
    "moussa diabate": "Moussa Diabaté",
    "moussa diabaté": "Moussa Diabaté",
    "killian hayes": "Killian Hayes",
    "armel traore": "Armel Traoré",
    "melvin ajinca": "Melvin Ajinça"
}


def is_french_player(name: str) -> bool:
    if not name:
        return False
    clean = name.lower().strip()
    return clean in FRENCH_PLAYERS or any(fr in clean for fr in FRENCH_PLAYERS.keys())


def detect_milestones(player: Dict[str, Any]) -> List[str]:
    """Detects triple-doubles, double-doubles, or high-scoring marks."""
    pts = player.get("pts", 0)
    reb = player.get("reb", 0)
    ast = player.get("ast", 0)
    stl = player.get("stl", 0)
    blk = player.get("blk", 0)

    cats = [pts, reb, ast, stl, blk]
    double_digits = sum(1 for c in cats if c >= 10)

    milestones = []
    if double_digits >= 3:
        milestones.append("⭐ Triple-Double")
    elif double_digits == 2:
        milestones.append("Double-Double")

    if pts >= 50:
        milestones.append("🔥 50+ Points!")
    elif pts >= 40:
        milestones.append("🔥 40+ Points!")
    elif pts >= 30:
        milestones.append("30+ Points")

    return milestones


def analyze_all_players(boxscores: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Scans every player across all game boxscores and compiles:
    - Top 5 performers of the night (MVP race)
    - French players recap 🇫🇷
    - All players list sorted by impact
    """
    all_players = []

    for box in boxscores:
        game_id = box.get("game_id", "")
        game_name = box.get("game_name", "")
        for team in box.get("teams", []):
            team_name = team.get("team_name", "")
            team_abbrev = team.get("team_abbrev", "")
            for p in team.get("players", []):
                if p.get("did_not_play"):
                    continue
                # Add context
                p_copy = dict(p)
                p_copy["game_id"] = game_id
                p_copy["game_name"] = game_name
                p_copy["team_name"] = team_name
                p_copy["team_abbrev"] = team_abbrev
                p_copy["is_french"] = is_french_player(p.get("name", ""))
                p_copy["milestones"] = detect_milestones(p)
                all_players.append(p_copy)

    # Sort players by game_score descending
    all_players.sort(key=lambda x: x.get("game_score", 0), reverse=True)

    # Top performers
    top_performers = all_players[:5]

    # French players
    french_players = [p for p in all_players if p.get("is_french")]

    return {
        "top_performers": top_performers,
        "french_players": french_players,
        "all_players": all_players,
        "total_players_tracked": len(all_players)
    }
