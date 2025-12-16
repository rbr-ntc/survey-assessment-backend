import time
from typing import List, Dict, Optional
from app.db import db

# Simple in-memory cache
_questions_cache: Optional[List[Dict]] = None
_last_cache_update: float = 0
CACHE_TTL = 300  # 5 minutes

async def get_cached_questions() -> List[Dict]:
    """
    Returns a list of questions, cached for CACHE_TTL seconds.
    """
    global _questions_cache, _last_cache_update

    current_time = time.time()

    if _questions_cache is None or (current_time - _last_cache_update > CACHE_TTL):
        # Cache miss or expired
        # Fetch all questions from DB, excluding _id to be safe for JSON serialization if needed,
        # but keep it if used elsewhere. The original code used {"_id": 0} in some places.
        # app/routers/results.py used {"_id": 0}
        # app/routers/questions.py used {"_id": 0, ...}

        # We fetch everything except _id for now, as _id is usually not needed for calculations
        # and can cause serialization issues if not handled.
        cursor = db.questions.find({}, {"_id": 0})
        _questions_cache = await cursor.to_list(length=None)
        _last_cache_update = current_time

    return _questions_cache
