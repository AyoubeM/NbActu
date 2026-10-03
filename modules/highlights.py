"""
Highlights Finder Module
Locates game highlight videos from YouTube (beIN Sports France first, then official NBA US channel as fallback).
"""

import logging
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

NBA_CHANNEL_ID = "UCWJ2lWNubArHWmf3FIHbfcQ"
BEIN_FR_CHANNEL_ID = "UCfj4kQ6_mYO5r4hzX5KloVw"
LEQUIPE_CHANNEL_ID = "UC_j_8n68a7Q1m7Hw457G2sQ"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
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


def match_game_video(videos: List[Dict[str, str]], away_name: str, home_name: str) -> Optional[Dict[str, str]]:
    """Checks if any video title in the list matches both team identifiers."""
    away_terms = [w.lower() for w in away_name.split() if len(w) > 3]
    home_terms = [w.lower() for w in home_name.split() if len(w) > 3]

    for v in videos:
        t = v["title"].lower()
        has_away = any(term in t for term in away_terms)
        has_home = any(term in t for term in home_terms)
        is_highlight = any(h in t for h in ["highlight", "résumé", "resume", "recap"])
        
        if (has_away and has_home) or (is_highlight and (has_away or has_home)):
            return v
    return None


class HighlightsFinder:
    def __init__(self):
        # Cache feeds to avoid fetching 15 times for 15 games
        self._nba_videos: Optional[List[Dict[str, str]]] = None
        self._bein_videos: Optional[List[Dict[str, str]]] = None

    def preload_feeds(self):
        self._bein_videos = _fetch_channel_rss(BEIN_FR_CHANNEL_ID)
        self._nba_videos = _fetch_channel_rss(NBA_CHANNEL_ID)

    def find_highlight(self, away_team: Dict[str, Any], home_team: Dict[str, Any]) -> Dict[str, str]:
        """
        Attempts to find a French highlight first.
        If unavailable, falls back to the official NBA US 10-minute game highlights.
        If not yet in RSS, generates direct YouTube search query link.
        """
        if self._bein_videos is None or self._nba_videos is None:
            self.preload_feeds()

        away_name = away_team.get("name") or away_team.get("shortName", "")
        home_name = home_team.get("name") or home_team.get("shortName", "")

        # 1. Search in French feed (beIN Sports)
        if self._bein_videos:
            match_fr = match_game_video(self._bein_videos, away_name, home_name)
            if match_fr:
                return {
                    "title": match_fr["title"],
                    "url": match_fr["url"],
                    "thumbnail": match_fr["thumbnail"],
                    "language": "FR 🇫🇷",
                    "source": "beIN SPORTS France"
                }

        # 2. Search in Official NBA US feed
        if self._nba_videos:
            match_us = match_game_video(self._nba_videos, away_name, home_name)
            if match_us:
                return {
                    "title": match_us["title"],
                    "url": match_us["url"],
                    "thumbnail": match_us["thumbnail"],
                    "language": "VO (US) 🇺🇸",
                    "source": "NBA Officiel (10 min HD)"
                }

        # 3. Direct Search Link Fallback
        query = f"{away_name} at {home_name} NBA full game highlights"
        search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}"
        
        return {
            "title": f"Résumé {away_name} vs {home_name}",
            "url": search_url,
            "thumbnail": home_team.get("logo", ""),
            "language": "VO (US) 🇺🇸",
            "source": "YouTube (Recherche directe)"
        }
