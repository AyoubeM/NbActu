"""
NBA Actu - Main Orchestrator
Fetches NBA games of the night, identifies broadcasters in France,
retrieves video highlights (French beIN Sports NBA Extra first, fallback to US official NBA),
computes team & player analytics, generates the Web Dashboard,
and dispatches Discord notifications with anti-spoiler mode.
"""

import sys
import logging
from datetime import datetime, timezone, timedelta
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
    logger.info(f"Targeting night games for US date: {target_date}")

    # 1. Fetch Scoreboard and Standings
    scoreboard_games = get_scoreboard(target_date)
    standings = get_standings()

    # Filter completed or live games vs upcoming unplayed games
    completed_games = [g for g in scoreboard_games if g.get("is_final") or g.get("is_live")]
    scheduled_games = [g for g in scoreboard_games if not g.get("is_final") and not g.get("is_live")]

    # If no games completed for target_date and no explicit override was set,
    # check yesterday to ensure we don't display unplayed 0-0 games
    if not completed_games and not (date_str or settings.OVERRIDE_DATE):
        prev_date = (datetime.strptime(target_date, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d")
        logger.info(f"No completed games on {target_date}. Checking previous night {prev_date}...")
        prev_games = get_scoreboard(prev_date)
        prev_completed = [g for g in prev_games if g.get("is_final") or g.get("is_live")]
        if prev_completed:
            completed_games = prev_completed
            target_date = prev_date
            logger.info(f"Found {len(completed_games)} completed games on {prev_date}.")

    logger.info(f"Processing {len(completed_games)} completed/live game(s) for morning recap.")

    # Preload highlight finder (beIN Sports NBA Extra FR + NBA US official)
    highlights_finder = HighlightsFinder()
    highlights_finder.preload_feeds()

    processed_games = []
    boxscores_list = []

    for game in completed_games:
        game_id = game["id"]
        home = game["home"]
        away = game["away"]

        # Broadcaster
        broadcaster = get_french_broadcaster(game.get("broadcasts", []), game)

        # Team form
        home_form = analyze_team_form(home.get("abbrev", ""), home.get("name", ""), standings)
        away_form = analyze_team_form(away.get("abbrev", ""), away.get("name", ""), standings)

        # Highlights (FR priority, then US fallback)
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

    # 3. Upcoming Games (Tonight's games)
    upcoming = scheduled_games if scheduled_games else get_upcoming_games()
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
