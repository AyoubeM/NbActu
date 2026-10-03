"""
French Broadcaster Identification Module
Identifies whether a game is broadcast on beIN SPORTS, Amazon Prime Video, or NBA League Pass.
"""

from typing import List, Dict, Any


def get_french_broadcaster(broadcast_names: List[str], game_info: Dict[str, Any] = None) -> str:
    """
    Returns the formatted string of French broadcasters for a given match.
    All NBA matches are available on the NBA League Pass.
    A subset is broadcast on beIN SPORTS or Amazon Prime Video.
    """
    clean_names = [b.lower() for b in broadcast_names] if broadcast_names else []
    
    is_prime = any("prime" in b or "amazon" in b for b in clean_names)
    is_bein = any("bein" in b for b in clean_names)

    # Some games in ESPN have national tags like TNT, ESPN, ABC, NBA TV
    # In France, beIN Sports picks up major national games
    has_major_us_coverage = any(b in clean_names for b in ["tnt", "abc", "espn", "nba tv"])

    if is_prime:
        return "📺 Amazon Prime Video • NBA League Pass"
    elif is_bein:
        return "📺 beIN SPORTS • NBA League Pass"
    elif has_major_us_coverage:
        # Most major national games are picked by beIN SPORTS in France
        return "📺 beIN SPORTS (ou différé) • NBA League Pass"
    else:
        return "📺 NBA League Pass (Exclusivité)"
