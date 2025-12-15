"""
Script to migrate existing test to quiz_content format in MongoDB.
Run this once to create the quiz_content document for the system analyst assessment.

Usage:
    python scripts/migrate_quiz_content.py
"""
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.db import db
from app.utils import CATEGORIES, LEVELS


async def migrate_quiz_content():
    """
    Create quiz_content document for system analyst assessment.
    """
    quiz_id = "quiz:system-analyst-assessment"

    # Check if already exists
    existing = await db.quiz_content.find_one({"_id": quiz_id})
    if existing:
        print(f"Quiz '{quiz_id}' already exists. Skipping migration.")
        return

    # Get all question IDs from questions collection
    questions = await db.questions.find({}, {"id": 1}).to_list(length=None)
    question_ids = [q["id"] for q in questions]

    # Build categories config from utils
    categories_config = {}
    for cat_key, cat_data in CATEGORIES.items():
        categories_config[cat_key] = {
            "name": cat_data["name"],
            "icon": cat_data["icon"],
            "weight": cat_data["weight"],
            "description": f"Категория {cat_data['name']}",
        }

    # Build level config from utils
    level_icons = {
        "Senior": "🏆",
        "Middle+": "📈",
        "Middle": "📊",
        "Junior+": "📝",
        "Junior": "🌱",
    }
    level_config = {}
    for level in LEVELS:
        level_key = level["level"].lower().replace("+", "_plus").replace("/", "_")
        next_level_key = level["nextLevel"].lower().replace("+", "_plus").replace("/", "_")
        level_config[level_key] = {
            "min_score": level["minScore"],
            "icon": level_icons.get(level["level"], "📊"),
            "description": level["description"],
            "next_level": next_level_key,
            "min_years": level.get("minYears"),
        }

    # Create quiz_content document
    quiz_doc = {
        "_id": quiz_id,
        "type": "assessment",
        "title": "Оценка навыков системного аналитика",
        "description": "Комплексная оценка компетенций системного аналитика по различным категориям: документирование, моделирование процессов, API Design, базы данных, безопасность, аналитическое мышление и коммуникации.",
        "slug": "system-analyst-assessment",
        "level": "all",
        "duration_minutes": 60,
        "passing_score": 50,
        "categories": categories_config,
        "level_config": level_config,
        "question_ids": question_ids,
        "settings": {
            "shuffle_questions": False,
            "shuffle_options": False,
            "show_correct_answers": True,
            "allow_skip": False,
            "time_limit": None,
            "max_attempts": None,
        },
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    # Insert into MongoDB
    await db.quiz_content.insert_one(quiz_doc)
    print(f"✅ Successfully created quiz '{quiz_id}' with {len(question_ids)} questions")
    print(f"   Categories: {len(categories_config)}")
    print(f"   Levels: {len(level_config)}")
    print(f"\n📋 Quiz configuration:")
    print(f"   - Title: {quiz_doc['title']}")
    print(f"   - Slug: {quiz_doc['slug']}")
    print(f"   - Passing score: {quiz_doc['passing_score']}%")
    print(f"   - Duration: {quiz_doc.get('duration_minutes', 'unlimited')} minutes")


if __name__ == "__main__":
    asyncio.run(migrate_quiz_content())

