import json
import os
from datetime import datetime
from typing import Dict, List

from app.db import db
from app.deps import verify_api_key
from app.models import QuickTestRequest, Result, ResultWithId, SubmitRequest
from app.utils import CATEGORIES, get_level
from bson import ObjectId
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from openai import AsyncOpenAI, OpenAIError

router = APIRouter()

async def generate_and_save_recommendations(result_id, user, level, overallScore, strengths, weaknesses, question_details):
    strong_str = ', '.join(f'{s["name"]} ({s["score"]}%)' for s in strengths) or 'Требуют развития'
    weak_str = ', '.join(f'{w["name"]} ({w["score"]}%)' for w in weaknesses) or 'Нет явных'
    
    # Анализируем детали вопросов для персонализации
    incorrect_answers = [qd for qd in question_details if qd["user_score"] < qd["max_score"]]
    correct_answers = [qd for qd in question_details if qd["user_score"] == qd["max_score"]]
    
    # Группируем ошибки по категориям
    errors_by_category = {}
    for qd in incorrect_answers:
        # Извлекаем категорию из learning_tip
        learning_tip = qd["learning_tip"]
        cat_name = "Общие"
        
        # Ищем категорию в learning_tip
        for cat in CATEGORIES.values():
            if cat["name"] in learning_tip:
                cat_name = cat["name"]
                break
        
        if cat_name not in errors_by_category:
            errors_by_category[cat_name] = []
        errors_by_category[cat_name].append(qd)
    
    # Создаем детальный анализ ошибок
    errors_analysis = ""
    for cat, errors in errors_by_category.items():
        if errors:
            errors_analysis += f"\n**{cat}** - {len(errors)} ошибок:\n"
            for error in errors[:3]:  # Показываем первые 3 ошибки
                errors_analysis += f"- Вопрос: {error['question_text'][:100]}...\n"
                errors_analysis += f"  Ваш ответ: {error['user_answer_text']}\n"
                errors_analysis += f"  Правильный: {error['correct_answer_text']}\n"
                errors_analysis += f"  Балл: {error['user_score']}/{error['max_score']}\n"
    
    system_prompt = """
Ты — заботливый, мотивирующий и экспертный ментор по развитию системных аналитиков. 
Твоя задача — проанализировать конкретные ответы пользователя на вопросы и дать персонализированные рекомендации.
Пиши живо, с примерами, избегай шаблонов. Опирайся на реальные вопросы и ответы пользователя.
"""
    
    prompt = f"""
Ты — опытный, вдохновляющий и заботливый ментор по развитию системных аналитиков. 
Твоя задача — проанализировать конкретные ответы пользователя и дать персональные советы.

## ИНФОРМАЦИЯ О КАНДИДАТЕ:
Кандидат: {user['name']}
Опыт: {user['experience']}
Текущий уровень: {level['level']} ({overallScore}%)
Сильные стороны: {strong_str}
Зоны развития: {weak_str}

## ДЕТАЛЬНЫЙ АНАЛИЗ ОТВЕТОВ:
Всего вопросов: {len(question_details)}
Правильных ответов: {len(correct_answers)}
Ошибок: {len(incorrect_answers)}

### АНАЛИЗ ОШИБОК ПО КАТЕГОРИЯМ:
{errors_analysis}

### ПРИМЕРЫ ВОПРОСОВ, ГДЕ БЫЛИ ОШИБКИ:
{chr(10).join([f"- {qd['question_text'][:80]}... (Ваш ответ: {qd['user_answer_text']}, Правильный: {qd['correct_answer_text']})" for qd in incorrect_answers[:5]])}

## ТВОЯ ЗАДАЧА:
1. **Проанализируй конкретные ошибки** - посмотри на вопросы, где были ошибки, и объясни, почему это важно
2. **Дай персональные советы** - основываясь на реальных ответах пользователя, а не на общих категориях
3. **Составь план развития** - учитывая конкретные слабые места, которые ты видишь в ответах
4. **Подбери ресурсы** - для тех тем, где были ошибки
5. **Мотивируй** - покажи, что ошибки - это нормально и как их превратить в опыт

## ФОРМАТ ОТВЕТА:
# Персональный план развития для {user['name']}

## Анализ ваших ответов
Проанализировав ваши ответы на {len(question_details)} вопросов, я вижу следующие паттерны:
- **Правильно отвечали на вопросы про:** [конкретные темы]
- **Сложности возникли с:** [конкретные темы на основе ошибок]

## Конкретные области для развития
[На основе реальных ошибок, которые вы делали]

## План на 3 месяца
[Персонализированный план, учитывающий ваши ошибки]

## Лучшие ресурсы
[Для конкретных тем, где были ошибки]

**Помните: каждый неправильный ответ - это шаг к пониманию!**
"""
    try:
        print(f"Generating recommendations for result {result_id}")
        client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        response = await client.chat.completions.create(
            model="gpt-5.2",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        recommendations = response.choices[0].message.content
        print(f"Recommendations generated successfully, length: {len(recommendations)}")
    except Exception as e:
        print(f"Error generating recommendations: {str(e)}")
        recommendations = f"Не удалось сгенерировать рекомендации: {str(e)}. Попробуйте позже."
    
    print(f"Saving recommendations to database for result {result_id}")
    await db.results.update_one({"_id": ObjectId(result_id)}, {"$set": {"recommendations": recommendations}})
    print(f"Recommendations saved successfully for result {result_id}")

@router.post("/results", response_model=ResultWithId, dependencies=[Depends(verify_api_key)])
async def submit_results(submit: SubmitRequest, background_tasks: BackgroundTasks):
    # Получаем вопросы из MongoDB
    questions = await db.questions.find({}, {"_id": 0}).to_list(length=None)
    answers = submit.answers
    user = submit.user.dict() if hasattr(submit.user, 'dict') else dict(submit.user)

    # Подсчёт баллов по категориям и сбор деталей по вопросам
    category_scores = {cat: 0 for cat in CATEGORIES}
    category_max_scores = {cat: 0 for cat in CATEGORIES}
    question_details = []

    for q in questions:
        qid = q['id']
        cat = q['category']
        max_score = max(q.get('weights', {}).values()) if 'weights' in q else 5
        category_max_scores[cat] += max_score
        answer = answers.get(qid)
        
        if answer:
            score = q.get('weights', {}).get(answer, 0) if 'weights' in q else 0
            category_scores[cat] += score
            
            # Собираем детали по каждому вопросу
            user_answer_text = next((opt['text'] for opt in q['options'] if opt['value'] == answer), "")
            correct_answer_value = max(q.get('weights', {}).items(), key=lambda x: x[1])[0] if q.get('weights') else ""
            correct_answer_text = next((opt['text'] for opt in q['options'] if opt['value'] == correct_answer_value), "")
            
            question_detail = {
                "question_id": qid,
                "question_text": q['question'],
                "user_answer_value": answer,
                "user_answer_text": user_answer_text,
                "correct_answer_value": correct_answer_value,
                "correct_answer_text": correct_answer_text,
                "user_score": score,
                "max_score": max_score,
                "explanation": f"Пользователь выбрал '{user_answer_text}' (балл: {score}/{max_score})",
                "difficulty": "medium",  # Можно добавить логику определения сложности
                "learning_tip": f"Для улучшения в категории '{CATEGORIES[cat]['name']}' изучите: {q['question']}"
            }
            question_details.append(question_detail)

    # Проценты по категориям + веса
    categories = {}
    for cat in CATEGORIES:
        percent = round((category_scores[cat] / category_max_scores[cat]) * 100) if category_max_scores[cat] > 0 else 0
        categories[cat] = {
            "score": percent,
            "weight": CATEGORIES[cat]["weight"],
            "name": CATEGORIES[cat]["name"]
        }

    # Взвешенный общий балл
    weighted_sum = sum(categories[cat]["score"] * CATEGORIES[cat]['weight'] for cat in CATEGORIES)
    total_weight = sum(CATEGORIES[cat]['weight'] for cat in CATEGORIES)
    overallScore = round(weighted_sum / total_weight)

    level = get_level(overallScore)
    level = dict(level)  # копия, чтобы не менять глобальный LEVELS
    level["nextLevelScore"] = str(level["nextLevelScore"])
    level["minScore"] = str(level["minScore"])

    # Сильные стороны (score >= 70)
    strengths = [
        {"name": categories[cat]["name"], "score": categories[cat]["score"]}
        for cat in categories if categories[cat]["score"] >= 70
    ]
    # Зоны развития (score < 60)
    weaknesses = [
        {"name": categories[cat]["name"], "score": categories[cat]["score"]}
        for cat in categories if categories[cat]["score"] < 60
    ]

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
    
    # Получаем все вопросы
    questions = await db.questions.find({}, {"_id": 0}).to_list(length=None)
    
    if not questions:
        raise HTTPException(status_code=404, detail="Questions not found")
    
    # Генерируем ответы в зависимости от типа теста
    answers = generate_quick_test_answers(questions, test_type)
    
    # Рассчитываем результаты теста
    category_scores = {cat: 0 for cat in CATEGORIES}
    category_max_scores = {cat: 0 for cat in CATEGORIES}
    question_details = []

    for q in questions:
        qid = q['id']
        cat = q['category']
        max_score = max(q.get('weights', {}).values()) if 'weights' in q else 5
        category_max_scores[cat] += max_score
        answer = answers.get(qid)
        
        if answer:
            score = q.get('weights', {}).get(answer, 0) if 'weights' in q else 0
            category_scores[cat] += score
            
            # Собираем детали по каждому вопросу
            user_answer_text = next((opt['text'] for opt in q['options'] if opt['value'] == answer), "")
            correct_answer_value = max(q.get('weights', {}).items(), key=lambda x: x[1])[0] if q.get('weights') else ""
            correct_answer_text = next((opt['text'] for opt in q['options'] if opt['value'] == correct_answer_value), "")
            
            question_detail = {
                "question_id": qid,
                "question_text": q['question'],
                "user_answer_value": answer,
                "user_answer_text": user_answer_text,
                "correct_answer_value": correct_answer_value,
                "correct_answer_text": correct_answer_text,
                "user_score": score,
                "max_score": max_score,
                "explanation": f"Пользователь выбрал '{user_answer_text}' (балл: {score}/{max_score})",
                "difficulty": "medium",
                "learning_tip": f"Для улучшения в категории '{CATEGORIES[cat]['name']}' изучите: {q['question']}"
            }
            question_details.append(question_detail)

    # Проценты по категориям + веса
    categories = {}
    for cat in CATEGORIES:
        percent = round((category_scores[cat] / category_max_scores[cat]) * 100) if category_max_scores[cat] > 0 else 0
        categories[cat] = {
            "score": percent,
            "weight": CATEGORIES[cat]["weight"],
            "name": CATEGORIES[cat]["name"]
        }

    # Взвешенный общий балл
    weighted_sum = sum(categories[cat]["score"] * CATEGORIES[cat]['weight'] for cat in CATEGORIES)
    total_weight = sum(CATEGORIES[cat]['weight'] for cat in CATEGORIES)
    overallScore = round(weighted_sum / total_weight)

    level = get_level(overallScore)
    level = dict(level)  # копия, чтобы не менять глобальный LEVELS
    level["nextLevelScore"] = str(level["nextLevelScore"])
    level["minScore"] = str(level["minScore"])

    # Сильные стороны (score >= 70)
    strengths = [
        {"name": categories[cat]["name"], "score": categories[cat]["score"]}
        for cat in categories if categories[cat]["score"] >= 70
    ]
    # Зоны развития (score < 60)
    weaknesses = [
        {"name": categories[cat]["name"], "score": categories[cat]["score"]}
        for cat in categories if categories[cat]["score"] < 60
    ]

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
