"""
Discord Notifier Module
Formats and delivers beautiful Discord Rich Embeds with anti-spoiler protection,
video highlight links, broadcaster information, and a link to the web dashboard.
"""

import json
import logging
import urllib.request
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def send_discord_webhook(webhook_url: str, payload: Dict[str, Any]) -> bool:
    """Posts payload JSON to Discord Webhook."""
    if not webhook_url:
        logger.warning("No DISCORD_WEBHOOK_URL set. Notification skipped.")
        return False

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "NbaActu-Bot/1.0"
            }
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status in (200, 204):
                logger.info("Discord notification sent successfully.")
                return True
            else:
                logger.warning(f"Discord responded with status {response.status}")
                return False
    except Exception as e:
        logger.error(f"Failed to send Discord webhook: {e}")
        return False


def build_discord_messages(
    games_data: List[Dict[str, Any]],
    upcoming_games: List[Dict[str, Any]],
    spoiler_mode: bool,
    dashboard_url: str
) -> List[Dict[str, Any]]:
    """
    Constructs well-structured Discord payloads (chunked if necessary to obey Discord's 10-embed limit).
    """
    now_str = datetime.now().strftime("%d/%m/%Y")
    total_games = len(games_data)

    # 1. Header embed
    header_embed = {
        "title": f"🏀 NBA Morning Recap • {now_str}",
        "description": (
            f"**{total_games} match(s) disputé(s) cette nuit.**\n\n"
            + ("🛡️ *Mode Anti-Spoiler actif : cliquez sur les balises sombres pour révéler les scores.* \n\n" if spoiler_mode else "")
            + f"📊 **[Consulter les stats complètes des joueurs sur le web]({dashboard_url})**"
        ),
        "color": 0x1D428A,  # NBA Blue
        "footer": {
            "text": "NbaActu • Résumés & Stats",
            "icon_url": "https://cdn.nba.com/logos/leagues/L/logo-nba.svg"
        }
    }

    embeds = [header_embed]

    # 2. Individual game embeds (or grouped)
    for g in games_data:
        home = g["home"]
        away = g["away"]
        broadcaster = g.get("broadcaster", "📺 NBA League Pass")
        highlight = g.get("highlight", {})
        home_form = g.get("home_form", {})
        away_form = g.get("away_form", {})

        # Spoiler formatting
        if spoiler_mode:
            score_text = f"|| 🏆 **{away['shortName']}** {away['score']} - {home['score']} **{home['shortName']}** ||"
        else:
            winner_icon_away = "🏆 " if away.get("winner") else ""
            winner_icon_home = "🏆 " if home.get("winner") else ""
            score_text = f"{winner_icon_away}**{away['shortName']}** {away['score']} - {home['score']} **{home['shortName']}**{winner_icon_home}"

        # Match description
        desc_lines = [
            f"**Score :** {score_text}",
            f"**Diffusion :** {broadcaster}",
            f"**Dynamique :** {away_form.get('streak_formatted', '-')} ({away['record']}) vs {home_form.get('streak_formatted', '-')} ({home['record']})",
            f"**Résumé :** 🎬 [{highlight.get('source', 'Vidéo')} ({highlight.get('language', 'VO')})]({highlight.get('url')})"
        ]

        embed = {
            "title": f"⚡ {away['name']} @ {home['name']}",
            "description": "\n".join(desc_lines),
            "color": 0xC8102E if away.get("winner") or home.get("winner") else 0x333333,
            "thumbnail": {
                "url": home.get("logo") or away.get("logo") or ""
            }
        }
        embeds.append(embed)

    # 3. Upcoming games embed (if any)
    if upcoming_games:
        upcoming_lines = []
        for up in upcoming_games[:6]:
            up_home = up["home"]["shortName"]
            up_away = up["away"]["shortName"]
            up_broadcast = up.get("broadcaster", "NBA League Pass")
            upcoming_lines.append(f"• **{up_away} vs {up_home}** ({up_broadcast})")

        upcoming_embed = {
            "title": "🌙 Au programme la nuit prochaine",
            "description": "\n".join(upcoming_lines),
            "color": 0xFDB927  # Gold
        }
        embeds.append(upcoming_embed)

    # Discord allows max 10 embeds per message. Chunk if > 10.
    messages = []
    chunk_size = 9
    for i in range(0, len(embeds), chunk_size):
        messages.append({"embeds": embeds[i:i + chunk_size]})

    return messages
