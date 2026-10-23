"""
Highlights Finder Module
Locates game highlight videos from YouTube.
PRIORITY 1: Official French highlights (beIN SPORTS NBA Extra - UCcMGbm0EYWh1SZZ8MsM75tw)
PRIORITY 2: Official NBA US 10-minute HD highlights (UCWJ2lWNubArHWmf3FIHbfcQ)
FALLBACK: Direct YouTube search link in French
"""

import logging
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# Channels
BEIN_NBA_EXTRA_CHANNEL_ID = "UCcMGbm0EYWh1SZZ8MsM75tw"
BEIN_FR_MAIN_CHANNEL_ID = "UCfj4kQ6_mYO5r4hzX5KloVw"
NBA_US_CHANNEL_ID = "UCWJ2lWNubArHWmf3FIHbfcQ"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

TEAM_ALIASES = {
    "cavaliers": ["cavaliers", "cavs", "cleveland"],
    "76ers": ["76ers", "sixers", "philadelphia", "philly"],
    "nuggets": ["nuggets", "denver"],
    "thunder": ["thunder", "okc", "oklahoma"],
    "celtics": ["celtics", "boston"],
    "knicks": ["knicks", "new york", "ny"],
    "bucks": ["bucks", "milwaukee"],
    "bulls": ["bulls", "chicago"],
    "heat": ["heat", "miami"],
    "lakers": ["lakers", "los angeles", "lal"],
    "clippers": ["clippers", "lac"],
    "warriors": ["warriors", "golden state", "gsw"],
    "suns": ["suns", "phoenix"],
    "mavericks": ["mavericks", "mavs", "dallas"],
    "timberwolves": ["timberwolves", "wolves", "minnesota"],
    "spurs": ["spurs", "san antonio"],
    "pacers": ["pacers", "indiana"],
    "magic": ["magic", "orlando"],
    "hawks": ["hawks", "atlanta"],
    "hornets": ["hornets", "charlotte"],
    "nets": ["nets", "brooklyn"],
    "raptors": ["raptors", "toronto"],
    "wizards": ["wizards", "washington"],
    "pistons": ["pistons", "detroit"],
    "rockets": ["rockets", "houston"],
    "grizzlies": ["grizzlies", "memphis"],
    "pelicans": ["pelicans", "pels", "new orleans"],
    "kings": ["kings", "sacramento"],
    "trail blazers": ["blazers", "trail blazers", "portland"],
    "jazz": ["jazz", "utah"]
}


def _fetch_channel_rss(channel_id: str) -> List[Dict[str, str]]:
    """Fetches the latest videos from a YouTube channel via public RSS feed."""
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=8) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            ns = {
                "atom": "http://www.w3.org/2005/Atom",
                "yt": "http://www.youtube.com/xml/schemas/2015",
                "media": "http://search.yahoo.com/mrss/"
            }
            videos = []
            for entry in root.findall("atom:entry", ns):
                title_elem = entry.find("atom:title", ns)
                link_elem = entry.find("atom:link", ns)
                video_id_elem = entry.find("yt:videoId", ns)
                media_group = entry.find("media:group", ns)
                thumb_elem = media_group.find("media:thumbnail", ns) if media_group is not None else None

                title = title_elem.text if title_elem is not None else ""
                link = link_elem.attrib.get("href", "") if link_elem is not None else ""
                vid_id = video_id_elem.text if video_id_elem is not None else ""
                thumb = thumb_elem.attrib.get("url", "") if thumb_elem is not None else f"https://img.youtube.com/vi/{vid_id}/hqdefault.jpg"

                videos.append({
                    "title": title,
                    "url": link,
                    "video_id": vid_id,
                    "thumbnail": thumb
                })
            return videos
    except Exception as e:
        logger.warning(f"Error fetching YouTube RSS for channel {channel_id}: {e}")
        return []


def get_team_keywords(team_info: Dict[str, Any]) -> List[str]:
    """Extracts all relevant alias keywords for a team."""
    name = (team_info.get("name") or "").lower()
    short_name = (team_info.get("shortName") or "").lower()
    abbrev = (team_info.get("abbrev") or "").lower()

    keywords = set([w for w in name.split() if len(w) > 2])
    if short_name:
        keywords.update([w for w in short_name.split() if len(w) > 2])
    if abbrev and len(abbrev) >= 2:
        keywords.add(abbrev)

    # Check against known aliases dictionary
    for k, aliases in TEAM_ALIASES.items():
        if k in name or k in short_name or any(a in name for a in aliases):
            keywords.update(aliases)

    return list(keywords)


def match_game_video(videos: List[Dict[str, str]], away_keywords: List[str], home_keywords: List[str], require_highlight_keyword: bool = True) -> Optional[Dict[str, str]]:
    """Checks if any video title contains keywords from BOTH teams."""
    for v in videos:
        t = v["title"].lower()
        has_away = any(k in t for k in away_keywords)
        has_home = any(k in t for k in home_keywords)
        
        if require_highlight_keyword:
            is_highlight = any(h in t for h in ["résumé", "resume", "highlights", "highlight", "replay", "extra"])
            if has_away and has_home and is_highlight:
                return v
        else:
            if has_away and has_home:
                return v

    return None


class HighlightsFinder:
    def __init__(self):
        self._nba_extra_videos: Optional[List[Dict[str, str]]] = None
        self._bein_main_videos: Optional[List[Dict[str, str]]] = None
        self._nba_us_videos: Optional[List[Dict[str, str]]] = None

    def preload_feeds(self):
        self._nba_extra_videos = _fetch_channel_rss(BEIN_NBA_EXTRA_CHANNEL_ID)
        self._bein_main_videos = _fetch_channel_rss(BEIN_FR_MAIN_CHANNEL_ID)
        self._nba_us_videos = _fetch_channel_rss(NBA_US_CHANNEL_ID)

    def find_highlight(self, away_team: Dict[str, Any], home_team: Dict[str, Any]) -> Dict[str, str]:
        """
        PRIORITY 1: French highlights from beIN SPORTS NBA Extra.
        PRIORITY 2: Official NBA US 10-min HD highlights.
        FALLBACK: Direct YouTube search query in French.
        """
        if self._nba_extra_videos is None:
            self.preload_feeds()

        away_kw = get_team_keywords(away_team)
        home_kw = get_team_keywords(home_team)

        # 1. Search in French NBA Extra channel (Highest Priority)
        if self._nba_extra_videos:
            match_extra = match_game_video(self._nba_extra_videos, away_kw, home_kw)
            if match_extra:
                return {
                    "title": match_extra["title"],
                    "url": match_extra["url"],
                    "thumbnail": match_extra["thumbnail"],
                    "language": "FR 🇫🇷",
                    "source": "beIN SPORTS (NBA Extra)"
                }

        # 2. Search in main beIN France channel
        if self._bein_main_videos:
            match_bein = match_game_video(self._bein_main_videos, away_kw, home_kw)
            if match_bein:
                return {
                    "title": match_bein["title"],
                    "url": match_bein["url"],
                    "thumbnail": match_bein["thumbnail"],
                    "language": "FR 🇫🇷",
                    "source": "beIN SPORTS France"
                }

        # 3. Fallback to Official NBA US 10-minute HD Highlights
        if self._nba_us_videos:
            match_us = match_game_video(self._nba_us_videos, away_kw, home_kw)
            if match_us:
                return {
                    "title": match_us["title"],
                    "url": match_us["url"],
                    "thumbnail": match_us["thumbnail"],
                    "language": "VO (US) 🇺🇸",
                    "source": "NBA Officiel (10 min HD)"
                }

        # 4. Direct French YouTube Search Link Fallback
        away_name = away_team.get("shortName") or away_team.get("name", "")
        home_name = home_team.get("shortName") or home_team.get("name", "")
        query = f"resume {away_name} {home_name} NBA beIN"
        search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}"

        return {
            "title": f"Recherche Résumé FR : {away_name} vs {home_name}",
            "url": search_url,
            "thumbnail": home_team.get("logo", ""),
            "language": "FR 🇫🇷 (Recherche)",
            "source": "YouTube FR"
        }
