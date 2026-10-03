"""
Web Data Generator Module
Serializes daily NBA recap, stats, and player analysis into JSON for the web dashboard.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


def generate_web_assets(data: Dict[str, Any], web_dir: Path, data_dir: Path) -> bool:
    """
    Saves the processed NBA payload into web/data.json and data/recap.json.
    """
    try:
        web_dir.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)

        json_content = json.dumps(data, indent=2, ensure_ascii=False)

        # Write to web/data.json
        web_data_file = web_dir / "data.json"
        web_data_file.write_text(json_content, encoding="utf-8")

        # Write backup to data/recap.json
        recap_file = data_dir / "recap.json"
        recap_file.write_text(json_content, encoding="utf-8")

        logger.info(f"Web assets successfully generated at {web_data_file}")
        return True
    except Exception as e:
        logger.error(f"Error generating web assets: {e}")
        return False
