import json
import os
from datetime import datetime
from typing import Dict, List

from app.cache import get_cached_questions
from app.db import db
from app.deps import verify_api_key
from app.models import QuickTestRequest, Result, ResultWithId, SubmitRequest
from app.services import calculate_scores, generate_recommendations_content
from app.utils import CATEGORIES, get_level
from bson import ObjectId
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from openai import AsyncOpenAI, OpenAIError

router = APIRouter()

async def generate_and_save_recommendations(result_id, user, level, overallScore, strengths, weaknesses, question_details):
    try:
        print(f"Generating recommendations for result {result_id}")
        user_name = user.get('name', '')
        user_experience = user.get('experience', '')

        recommendations = await generate_recommendations_content(
            user_name,
            user_experience,
            level,
            overallScore,
            strengths,
            weaknesses,
            question_details
        )
        print(f"Recommendations generated successfully, length: {len(recommendations)}")
    except Exception as e:
        print(f"Error generating recommendations: {str(e)}")
        recommendations = f"Не удалось сгенерировать рекомендации: {str(e)}. Попробуйте позже."
    
    print(f"Saving recommendations to database for result {result_id}")
    await db.results.update_one({"_id": ObjectId(result_id)}, {"$set": {"recommendations": recommendations}})
    print(f"Recommendations saved successfully for result {result_id}")

@router.post("/results", response_model=ResultWithId, dependencies=[Depends(verify_api_key)])
async def submit_results(submit: SubmitRequest, background_tasks: BackgroundTasks):
    # Получаем вопросы (из кэша)
    questions = await get_cached_questions()
    answers = submit.answers
    user = submit.user.dict() if hasattr(submit.user, 'dict') else dict(submit.user)

    overallScore, level, categories, strengths, weaknesses, question_details = calculate_scores(questions, answers)

    result_doc = {
        "user": user,
        "answers": answers,
        "categories": categories,
        "overallScore": overallScore,
        "level": level,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "recommendations": None,
        "question_details": question_details,
        "created_at": datetime.utcnow()
    }
    insert_result = await db.results.insert_one(result_doc)
    result_id = str(insert_result.inserted_id)

    # Запускаем генерацию рекомендаций в фоне
    background_tasks.add_task(
        generate_and_save_recommendations,
        result_id,
        user,
        level,
        overallScore,
        strengths,
        weaknesses,
        question_details
    )

    return {
        "result_id": result_id,
        "overallScore": overallScore,
        "level": level,
        "categories": categories,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "recommendations": None,
        "question_details": question_details
    }

@router.get("/results/{result_id}", dependencies=[Depends(verify_api_key)])
async def get_result_by_id(result_id: str):
    try:
        obj_id = ObjectId(result_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid result id")
    result = await db.results.find_one({"_id": obj_id})
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    user = result.get("user", {})
    safe_user = {"name": user.get("name", ""), "experience": user.get("experience", "")}
    return {
        "user": safe_user,
        "overallScore": result.get("overallScore"),
        "level": result.get("level"),
        "categories": result.get("categories"),
        "strengths": result.get("strengths", []),
        "weaknesses": result.get("weaknesses", []),
        "recommendations": result.get("recommendations", None),
        "question_details": result.get("question_details", []),
        "created_at": result.get("created_at")
    }

@router.post("/quick-test")
async def quick_test(
    test_data: QuickTestRequest,
    background_tasks: BackgroundTasks
):
    # Проверяем, включены ли quick-test
    if not os.environ.get("ENABLE_QUICK_TEST", "false").lower() in ("true", "1", "yes"):
        raise HTTPException(
            status_code=404, 
            detail="Quick test functionality is disabled"
        )
    test_type = test_data.test_type
    """
    Быстрый тест с предзаполненными ответами
    test_type: "expert", "intermediate", "beginner", "random"
    """
    
    # Получаем все вопросы (из кэша)
    questions = await get_cached_questions()
    
    if not questions:
        raise HTTPException(status_code=404, detail="Questions not found")
    
    # Генерируем ответы в зависимости от типа теста
    answers = generate_quick_test_answers(questions, test_type)
    
    overallScore, level, categories, strengths, weaknesses, question_details = calculate_scores(questions, answers)

    # Создаем полный результат теста
    test_result = {
        "user": {"name": f"Quick Test - {test_type.title()}", "experience": "N/A"},
        "answers": answers,
        "categories": categories,
        "overallScore": overallScore,
        "level": level,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "recommendations": None,
        "question_details": question_details,
        "created_at": datetime.utcnow()
    }
    
    # Сохраняем в базу
    insert_result = await db.results.insert_one(test_result)
    result_id = str(insert_result.inserted_id)
    
    # Запускаем генерацию рекомендаций в фоне
    background_tasks.add_task(
        generate_and_save_recommendations,
        result_id,
        test_result["user"],
        level,
        overallScore,
        strengths,
        weaknesses,
        question_details
    )
    
    return {
        "test_id": result_id,
        "message": f"Quick test completed with {test_type} level answers",
        "answers_count": len(answers)
    }

def generate_quick_test_answers(questions: List[Dict], test_type: str) -> Dict[str, str]:
    """Генерирует предзаполненные ответы для быстрого тестирования"""
    import random
    
    answers = {}
    
    for question in questions:
        if test_type == "expert":
            # Эксперт: в основном правильные ответы (a, b, c)
            if random.random() < 0.8:
                answer = random.choice(["a", "b", "c"])
            else:
                answer = random.choice(["d", "e", "f", "g", "h", "i"])
        elif test_type == "intermediate":
            # Средний уровень: смешанные ответы
            if random.random() < 0.6:
                answer = random.choice(["a", "b", "c"])
            else:
                answer = random.choice(["d", "e", "f", "g", "h", "i"])
        elif test_type == "beginner":
            # Начинающий: в основном неправильные ответы
            if random.random() < 0.3:
                answer = random.choice(["a", "b", "c"])
            else:
                answer = random.choice(["d", "e", "f", "g", "h", "i"])
        elif test_type == "random":
            # Случайные ответы
            answer = random.choice(["a", "b", "c", "d", "e", "f", "g", "h", "i"])
        else:
            # По умолчанию - случайные
            answer = random.choice(["a", "b", "c", "d", "e", "f", "g", "h", "i"])
        
        answers[question["id"]] = answer
    
    return answers

@router.get("/quick-test/{test_id}")
async def get_quick_test_result(test_id: str):
    # Проверяем, включены ли quick-test
    if not os.environ.get("ENABLE_QUICK_TEST", "false").lower() in ("true", "1", "yes"):
        raise HTTPException(
            status_code=404, 
            detail="Quick test functionality is disabled"
        )
    """Получить результат быстрого теста"""
    try:
        obj_id = ObjectId(test_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid test id")
    
    result = await db.results.find_one({"_id": obj_id})
    
    if not result:
        raise HTTPException(status_code=404, detail="Test result not found")
    
    # Получаем полный результат через существующий endpoint
    return await get_result_by_id(test_id)
