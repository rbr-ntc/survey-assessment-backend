"""
Quiz router - Universal test system API
Handles quiz content, attempts, and results.
"""
import json
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from app.auth.router import get_current_user
from app.db import db
from app.db_postgres import get_db
from app.models import (CategoryConfig, LevelConfig, Question,
                        QuizAttemptResponse, QuizContent, QuizResponse,
                        QuizSettings, StartQuizRequest, StartQuizResponse,
                        SubmitQuizRequest)
from app.models_postgres import QuizAttempt, User
from app.services import calculate_scores
from app.utils import CATEGORIES, get_level
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/quizzes", tags=["quizzes"])


@router.get("/{quiz_id}", response_model=QuizResponse)
async def get_quiz(quiz_id: str):
    """
    Get quiz configuration by ID.
    Quiz ID format: 'quiz:system-analyst-assessment' or just 'system-analyst-assessment'
    """
    # Normalize quiz_id (add 'quiz:' prefix if not present)
    if not quiz_id.startswith("quiz:"):
        quiz_id = f"quiz:{quiz_id}"

    quiz_doc = await db.quiz_content.find_one({"_id": quiz_id})
    if not quiz_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quiz '{quiz_id}' not found",
        )

    # Get question count
    question_ids = quiz_doc.get("question_ids", [])
    question_count = len(question_ids)

    # Convert to response model
    quiz_response = QuizResponse(
        id=quiz_doc["_id"],
        type=quiz_doc["type"],
        title=quiz_doc["title"],
        description=quiz_doc["description"],
        slug=quiz_doc["slug"],
        level=quiz_doc.get("level", "all"),
        duration_minutes=quiz_doc.get("duration_minutes"),
        passing_score=quiz_doc.get("passing_score", 50),
        categories={
            k: CategoryConfig(**v) for k, v in quiz_doc.get("categories", {}).items()
        },
        level_config={
            k: LevelConfig(**v) for k, v in quiz_doc.get("level_config", {}).items()
        },
        question_count=question_count,
        settings=QuizSettings(**quiz_doc.get("settings", {})),
    )

    return quiz_response


@router.get("/{quiz_id}/questions", response_model=List[Question])
async def get_quiz_questions(quiz_id: str):
    """
    Get questions for a quiz.
    """
    # Normalize quiz_id
    if not quiz_id.startswith("quiz:"):
        quiz_id = f"quiz:{quiz_id}"

    quiz_doc = await db.quiz_content.find_one({"_id": quiz_id})
    if not quiz_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quiz '{quiz_id}' not found",
        )

    question_ids = quiz_doc.get("question_ids", [])
    if not question_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No questions found for quiz '{quiz_id}'",
        )

    # Fetch questions from MongoDB
    questions = await db.questions.find(
        {"id": {"$in": question_ids}}, {"_id": 0}
    ).to_list(length=None)

    if len(questions) != len(question_ids):
        # Some questions are missing
        found_ids = {q["id"] for q in questions}
        missing_ids = set(question_ids) - found_ids
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Questions not found: {missing_ids}",
        )

    # Sort questions by question_ids order
    question_map = {q["id"]: q for q in questions}
    sorted_questions = [question_map[qid] for qid in question_ids if qid in question_map]

    return sorted_questions


@router.post("/{quiz_id}/start", response_model=StartQuizResponse)
async def start_quiz(
    quiz_id: str,
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db),
):
    """
    Start a new quiz attempt.
    Creates a quiz_attempt record in PostgreSQL.
    """
    # Normalize quiz_id
    if not quiz_id.startswith("quiz:"):
        quiz_id = f"quiz:{quiz_id}"

    # Verify quiz exists
    quiz_doc = await db.quiz_content.find_one({"_id": quiz_id})
    if not quiz_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quiz '{quiz_id}' not found",
        )

    # Check max attempts if configured
    max_attempts = quiz_doc.get("settings", {}).get("max_attempts")
    if max_attempts:
        result = await db_session.execute(
            select(QuizAttempt)
            .where(
                QuizAttempt.user_id == current_user.id,
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.deleted_at.is_(None),
            )
        )
        existing_attempts = result.scalars().all()
        if len(existing_attempts) >= max_attempts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum attempts ({max_attempts}) reached for this quiz",
            )

    # Create quiz attempt in PostgreSQL
    attempt = QuizAttempt(
        user_id=current_user.id,
        quiz_id=quiz_id,
        status="in_progress",
        started_at=datetime.now(timezone.utc),
    )
    db_session.add(attempt)
    await db_session.flush()  # Get attempt.id

    # Get questions
    question_ids = quiz_doc.get("question_ids", [])
    questions = await db.questions.find(
        {"id": {"$in": question_ids}}, {"_id": 0}
    ).to_list(length=None)

    # Sort questions by question_ids order
    question_map = {q["id"]: q for q in questions}
    sorted_questions = [question_map[qid] for qid in question_ids if qid in question_map]

    # Build quiz response
    quiz_response = QuizResponse(
        id=quiz_doc["_id"],
        type=quiz_doc["type"],
        title=quiz_doc["title"],
        description=quiz_doc["description"],
        slug=quiz_doc["slug"],
        level=quiz_doc.get("level", "all"),
        duration_minutes=quiz_doc.get("duration_minutes"),
        passing_score=quiz_doc.get("passing_score", 50),
        categories={
            k: CategoryConfig(**v) for k, v in quiz_doc.get("categories", {}).items()
        },
        level_config={
            k: LevelConfig(**v) for k, v in quiz_doc.get("level_config", {}).items()
        },
        question_count=len(sorted_questions),
        settings=QuizSettings(**quiz_doc.get("settings", {})),
    )

    await db_session.commit()

    return StartQuizResponse(
        attempt_id=str(attempt.id),
        quiz=quiz_response,
        questions=sorted_questions,
    )


@router.post("/{quiz_id}/attempts/{attempt_id}/submit", response_model=QuizAttemptResponse)
async def submit_quiz(
    quiz_id: str,
    attempt_id: str,
    request: SubmitQuizRequest,
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db),
):
    """
    Submit quiz answers and calculate results.
    Updates quiz_attempt in PostgreSQL and optionally saves detailed results to MongoDB.
    """
    # Normalize quiz_id
    if not quiz_id.startswith("quiz:"):
        quiz_id = f"quiz:{quiz_id}"

    # Get quiz attempt
    try:
        attempt_uuid = UUID(attempt_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid attempt_id format",
        )

    result = await db_session.execute(
        select(QuizAttempt).where(
            QuizAttempt.id == attempt_uuid,
            QuizAttempt.user_id == current_user.id,
            QuizAttempt.quiz_id == quiz_id,
            QuizAttempt.deleted_at.is_(None),
        )
    )
    attempt = result.scalar_one_or_none()

    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz attempt not found",
        )

    if attempt.status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Quiz attempt is already {attempt.status}",
        )

    # Get quiz configuration
    quiz_doc = await db.quiz_content.find_one({"_id": quiz_id})
    if not quiz_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quiz '{quiz_id}' not found",
        )

    # Get questions
    question_ids = quiz_doc.get("question_ids", [])
    questions = await db.questions.find(
        {"id": {"$in": question_ids}}, {"_id": 0}
    ).to_list(length=None)

    # Calculate scores using existing service
    # Note: This uses CATEGORIES from utils, but we should use quiz categories
    # For now, we'll use the quiz's categories if available, otherwise fallback to utils
    overall_score, level_dict, categories_dict, strengths, weaknesses, question_details = (
        calculate_scores(questions, request.answers)
    )

    # Determine level from quiz config or fallback
    level_config = quiz_doc.get("level_config", {})
    level_name = None
    if level_config:
        # Find level from config
        for level_key, level_cfg in level_config.items():
            if overall_score >= level_cfg.get("min_score", 0):
                level_name = level_key
        # Get the highest matching level
        if level_name:
            # Reverse iterate to get highest level
            for level_key in reversed(list(level_config.keys())):
                if overall_score >= level_config[level_key].get("min_score", 0):
                    level_name = level_key
                    break
    else:
        # Fallback to utils
        level_name = level_dict.get("level", "Junior").lower()

    # Check if passed
    passing_score = quiz_doc.get("passing_score", 50)
    passed = overall_score >= passing_score

    # Calculate time spent
    time_spent = None
    if attempt.started_at:
        time_spent = int((datetime.now(timezone.utc) - attempt.started_at).total_seconds())

    # Update attempt in PostgreSQL
    attempt.status = "completed"
    attempt.score = overall_score
    attempt.level = level_name
    attempt.passed = passed
    attempt.completed_at = datetime.now(timezone.utc)
    attempt.time_spent_seconds = time_spent
    attempt.category_scores = json.dumps(
        {k: v["score"] for k, v in categories_dict.items()}
    )
    attempt.strengths = json.dumps(strengths)
    attempt.weaknesses = json.dumps(weaknesses)

    # Optionally save detailed results to MongoDB (for backward compatibility)
    # This allows existing result viewing pages to work
    result_doc = {
        "user": {
            "name": current_user.name,
            "email": current_user.email,
            "experience": "",  # Could add to user profile later
        },
        "answers": request.answers,
        "categories": categories_dict,
        "overallScore": overall_score,
        "level": level_dict,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "recommendations": None,  # Will be generated in background
        "question_details": [qd.dict() if hasattr(qd, "dict") else qd for qd in question_details],
        "created_at": datetime.utcnow(),
    }
    insert_result = await db.results.insert_one(result_doc)
    attempt.result_content_id = str(insert_result.inserted_id)

    await db_session.commit()

    # TODO: Generate recommendations in background (similar to existing system)

    return QuizAttemptResponse(
        attempt_id=str(attempt.id),
        quiz_id=quiz_id,
        status=attempt.status,
        score=attempt.score,
        level=attempt.level,
        passed=attempt.passed,
        started_at=attempt.started_at.isoformat(),
        completed_at=attempt.completed_at.isoformat() if attempt.completed_at else None,
        time_spent_seconds=attempt.time_spent_seconds,
        category_scores=json.loads(attempt.category_scores) if attempt.category_scores else None,
        strengths=json.loads(attempt.strengths) if attempt.strengths else None,
        weaknesses=json.loads(attempt.weaknesses) if attempt.weaknesses else None,
        recommendations=None,  # Will be populated when generated
        question_details=question_details,
    )


@router.get("/{quiz_id}/attempts/{attempt_id}", response_model=QuizAttemptResponse)
async def get_quiz_attempt(
    quiz_id: str,
    attempt_id: str,
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db),
):
    """
    Get quiz attempt result.
    """
    # Normalize quiz_id
    if not quiz_id.startswith("quiz:"):
        quiz_id = f"quiz:{quiz_id}"

    try:
        attempt_uuid = UUID(attempt_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid attempt_id format",
        )

    result = await db_session.execute(
        select(QuizAttempt).where(
            QuizAttempt.id == attempt_uuid,
            QuizAttempt.user_id == current_user.id,
            QuizAttempt.quiz_id == quiz_id,
            QuizAttempt.deleted_at.is_(None),
        )
    )
    attempt = result.scalar_one_or_none()

    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz attempt not found",
        )

    # Get detailed results from MongoDB if available
    question_details = None
    recommendations = None
    if attempt.result_content_id:
        try:
            result_doc = await db.results.find_one({"_id": ObjectId(attempt.result_content_id)})
            if result_doc:
                question_details = result_doc.get("question_details", [])
                recommendations = result_doc.get("recommendations")
        except Exception:
            pass  # If MongoDB result not found, continue without details

    return QuizAttemptResponse(
        attempt_id=str(attempt.id),
        quiz_id=attempt.quiz_id,
        status=attempt.status,
        score=attempt.score,
        level=attempt.level,
        passed=attempt.passed,
        started_at=attempt.started_at.isoformat(),
        completed_at=attempt.completed_at.isoformat() if attempt.completed_at else None,
        time_spent_seconds=attempt.time_spent_seconds,
        category_scores=json.loads(attempt.category_scores) if attempt.category_scores else None,
        strengths=json.loads(attempt.strengths) if attempt.strengths else None,
        weaknesses=json.loads(attempt.weaknesses) if attempt.weaknesses else None,
        recommendations=recommendations,
        question_details=question_details,
    )

