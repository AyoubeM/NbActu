"""
NBA Actu - Main Orchestrator
Fetches NBA games of the night, identifies broadcasters in France,
retrieves video highlights (FR or US fallback), computes team & player analytics,
generates the Web Dashboard, and dispatches Discord notifications with anti-spoiler mode.
"""

import sys
import logging
from datetime import datetime
from config import settings
from modules.nba_api import (
    get_target_date_str,
    get_scoreboard,
    get_game_boxscore,
    get_standings,
    get_upcoming_games
)
from modules.broadcaster import get_french_broadcaster
from modules.team_analysis import analyze_team_form
from modules.highlights import HighlightsFinder
from modules.player_analysis import analyze_all_players
from modules.web_generator import generate_web_assets
from modules.discord_notifier import build_discord_messages, send_discord_webhook

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("NbaActu")


def run_pipeline(date_str: str = ""):
    target_date = get_target_date_str(date_str or settings.OVERRIDE_DATE)
    logger.info(f"Starting NBA Actu pipeline for date: {target_date}")

    # 1. Fetch Scoreboard and Standings
    scoreboard_games = get_scoreboard(target_date)
    standings = get_standings()
    logger.info(f"Retrieved {len(scoreboard_games)} games from NBA/ESPN scoreboard.")

    # If no games for yesterday's US date (e.g., during off-season or test), try today's date
    if not scoreboard_games and not (date_str or settings.OVERRIDE_DATE):
        today_date = datetime.now().strftime("%Y%m%d")
        logger.info(f"No games on {target_date}, checking current date {today_date}...")
        scoreboard_games = get_scoreboard(today_date)
        if scoreboard_games:
            target_date = today_date

    # Preload highlight finder
    highlights_finder = HighlightsFinder()
    highlights_finder.preload_feeds()

    processed_games = []
    boxscores_list = []

    for game in scoreboard_games:
        game_id = game["id"]
        home = game["home"]
        away = game["away"]

        # Broadcaster
        broadcaster = get_french_broadcaster(game.get("broadcasts", []), game)

        # Team form
        home_form = analyze_team_form(home.get("abbrev", ""), home.get("name", ""), standings)
        away_form = analyze_team_form(away.get("abbrev", ""), away.get("name", ""), standings)

        # Highlights
        highlight = highlights_finder.find_highlight(away, home)

        # Full boxscore for all players
        boxscore = get_game_boxscore(game_id)
        if boxscore:
            boxscore["game_id"] = game_id
            boxscore["game_name"] = game.get("name", "")
            boxscores_list.append(boxscore)

        processed_game = {
            "id": game_id,
            "name": game.get("name"),
            "shortName": game.get("shortName"),
            "date": game.get("date"),
            "is_final": game.get("is_final"),
            "is_live": game.get("is_live"),
            "status_detail": game.get("status_detail"),
            "home": home,
            "away": away,
            "broadcaster": broadcaster,
            "home_form": home_form,
            "away_form": away_form,
            "highlight": highlight,
            "boxscore": boxscore
        }
        processed_games.append(processed_game)

    # 2. Player Analysis (Top performers & French players)
    players_analysis = analyze_all_players(boxscores_list)
    logger.info(
        f"Analyzed {players_analysis.get('total_players_tracked', 0)} players. "
        f"Found {len(players_analysis.get('french_players', []))} French player performances."
    )

    # 3. Upcoming Games
    upcoming = get_upcoming_games()
    for up in upcoming:
        up["broadcaster"] = get_french_broadcaster(up.get("broadcasts", []), up)

    # Format human date (French format)
    try:
        dt = datetime.strptime(target_date, "%Y%m%d")
        date_formatted = dt.strftime("%d/%m/%Y")
    except Exception:
        date_formatted = target_date

    # 4. Generate Web Assets
    payload = {
        "date": target_date,
        "date_formatted": date_formatted,
        "games": processed_games,
        "players_analysis": players_analysis,
        "standings": standings,
        "upcoming": upcoming,
        "generated_at": datetime.now().isoformat()
    }

    generate_web_assets(payload, settings.WEB_DIR, settings.DATA_DIR)

    # 5. Dispatch Discord Notifications
    if settings.DISCORD_WEBHOOK_URL:
        logger.info("Preparing Discord notifications...")
        messages = build_discord_messages(
            processed_games,
            upcoming,
            settings.SPOILER_MODE,
            settings.DASHBOARD_URL
        )
        for idx, msg in enumerate(messages, 1):
            success = send_discord_webhook(settings.DISCORD_WEBHOOK_URL, msg)
            if success:
                logger.info(f"Discord message part {idx}/{len(messages)} sent.")
            else:
                logger.error(f"Failed to send Discord message part {idx}/{len(messages)}.")
    else:
        logger.info("No DISCORD_WEBHOOK_URL configured. Discord notification skipped.")

    logger.info("Pipeline completed successfully!")
    return payload


if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else ""
    run_pipeline(date_arg)
