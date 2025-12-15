import os
from typing import Dict, List, Optional, Tuple

from openai import AsyncOpenAI, OpenAIError

from app.config import settings
from app.models import QuestionDetail
from app.utils import CATEGORIES, get_level


def calculate_scores(questions: List[Dict], answers: Dict[str, str]) -> Tuple[int, Dict, Dict, List, List, List[QuestionDetail]]:
    """
    Calculates scores based on questions and user answers.
    Returns:
        overallScore (int): The weighted average score.
        level (Dict): The calculated level object.
        categories (Dict): Detailed scores per category.
        strengths (List): List of strong categories.
        weaknesses (List): List of weak categories.
        question_details (List[QuestionDetail]): Detailed analysis of each question.
    """
    category_scores = {cat: 0 for cat in CATEGORIES}
    category_max_scores = {cat: 0 for cat in CATEGORIES}
    question_details = []

    for q in questions:
        qid = q['id']
        cat = q['category']

        weights = q.get('weights', {})
        if weights:
            # Optimization: Find max score and correct answer value in one pass
            best_answer_item = max(weights.items(), key=lambda x: x[1])
            correct_answer_value = best_answer_item[0]
            max_score = best_answer_item[1]
        else:
            max_score = 5
            correct_answer_value = ""

        category_max_scores[cat] += max_score
        answer = answers.get(qid)

        if answer:
            score = weights.get(answer, 0)
            category_scores[cat] += score

            # Optimization: Avoid iterating options multiple times
            user_answer_text = ""
            correct_answer_text = ""

            # Linear scan once to find both texts
            for opt in q['options']:
                val = opt['value']
                if val == answer:
                    user_answer_text = opt['text']
                if val == correct_answer_value:
                    correct_answer_text = opt['text']
                if user_answer_text and correct_answer_text:
                    break

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
                "difficulty": "medium",  # Could add logic for difficulty
                "learning_tip": f"Для улучшения в категории '{CATEGORIES[cat]['name']}' изучите: {q['question']}"
            }
            question_details.append(question_detail)

    # Category percentages + weights
    categories = {}
    for cat in CATEGORIES:
        percent = round((category_scores[cat] / category_max_scores[cat]) * 100) if category_max_scores[cat] > 0 else 0
        categories[cat] = {
            "score": percent,
            "weight": CATEGORIES[cat]["weight"],
            "name": CATEGORIES[cat]["name"]
        }

    # Weighted overall score
    weighted_sum = sum(categories[cat]["score"] * CATEGORIES[cat]['weight'] for cat in CATEGORIES)
    total_weight = sum(CATEGORIES[cat]['weight'] for cat in CATEGORIES)
    overallScore = round(weighted_sum / total_weight)

    level = get_level(overallScore)
    level = dict(level)  # copy to avoid modifying global LEVELS
    level["nextLevelScore"] = str(level["nextLevelScore"])
    level["minScore"] = str(level["minScore"])

    # Strengths (score >= 70)
    strengths = [
        {"name": categories[cat]["name"], "score": categories[cat]["score"]}
        for cat in categories if categories[cat]["score"] >= 70
    ]
    # Weaknesses (score < 60)
    weaknesses = [
        {"name": categories[cat]["name"], "score": categories[cat]["score"]}
        for cat in categories if categories[cat]["score"] < 60
    ]

    return overallScore, level, categories, strengths, weaknesses, question_details


async def generate_recommendations_content(
    user_name: str,
    user_experience: str,
    level: Dict,
    overallScore: int,
    strengths: List[Dict],
    weaknesses: List[Dict],
    question_details: List[Dict]
) -> str:
    """
    Generates recommendation content using OpenAI.
    """
    strong_str = ', '.join(f'{s["name"]} ({s["score"]}%)' for s in strengths) or 'Требуют развития'
    weak_str = ', '.join(f'{w["name"]} ({w["score"]}%)' for w in weaknesses) or 'Нет явных'

    # Analyze question details for personalization
    # Ensure question_details are dicts
    q_details = []
    for qd in question_details:
        if hasattr(qd, 'dict'):
            q_details.append(qd.dict())
        else:
            q_details.append(qd)

    incorrect_answers = [qd for qd in q_details if qd.get("user_score", 0) < qd.get("max_score", 5)]
    correct_answers = [qd for qd in q_details if qd.get("user_score", 0) == qd.get("max_score", 5)]

    # Group errors by category
    errors_by_category = {}
    for qd in incorrect_answers:
        learning_tip = qd.get("learning_tip", "")
        cat_name = "Общие"

        # Look for category in learning_tip
        for cat in CATEGORIES.values():
            if cat["name"] in learning_tip:
                cat_name = cat["name"]
                break

        if cat_name not in errors_by_category:
            errors_by_category[cat_name] = []
        errors_by_category[cat_name].append(qd)

    # Create detailed error analysis
    errors_analysis = ""
    for cat, errors in errors_by_category.items():
        if errors:
            errors_analysis += f"\n**{cat}** - {len(errors)} ошибок:\n"
            for error in errors[:3]:  # Show first 3 errors
                errors_analysis += f"- Вопрос: {error.get('question_text', '')[:100]}...\n"
                errors_analysis += f"  Ваш ответ: {error.get('user_answer_text', '')}\n"
                errors_analysis += f"  Правильный: {error.get('correct_answer_text', '')}\n"
                errors_analysis += f"  Балл: {error.get('user_score', 0)}/{error.get('max_score', 5)}\n"

    system_prompt = """
Ты — заботливый, мотивирующий и экспертный ментор по развитию системных аналитиков.
Твоя задача — проанализировать конкретные ответы пользователя на вопросы и дать персонализированные рекомендации.
Пиши живо, с примерами, избегай шаблонов. Опирайся на реальные вопросы и ответы пользователя.
"""

    prompt = f"""
Ты — опытный, вдохновляющий и заботливый ментор по развитию системных аналитиков.
Твоя задача — проанализировать конкретные ответы пользователя и дать персональные советы.

## ИНФОРМАЦИЯ О КАНДИДАТЕ:
Кандидат: {user_name}
Опыт: {user_experience}
Текущий уровень: {level['level']} ({overallScore}%)
Сильные стороны: {strong_str}
Зоны развития: {weak_str}

## ДЕТАЛЬНЫЙ АНАЛИЗ ОТВЕТОВ:
Всего вопросов: {len(q_details)}
Правильных ответов: {len(correct_answers)}
Ошибок: {len(incorrect_answers)}

### АНАЛИЗ ОШИБОК ПО КАТЕГОРИЯМ:
{errors_analysis}

### ПРИМЕРЫ ВОПРОСОВ, ГДЕ БЫЛИ ОШИБКИ:
{chr(10).join([f"- {qd.get('question_text', '')[:80]}... (Ваш ответ: {qd.get('user_answer_text', '')}, Правильный: {qd.get('correct_answer_text', '')})" for qd in incorrect_answers[:5]])}

## ТВОЯ ЗАДАЧА:
1. **Проанализируй конкретные ошибки** - посмотри на вопросы, где были ошибки, и объясни, почему это важно
2. **Дай персональные советы** - основываясь на реальных ответах пользователя, а не на общих категориях
3. **Составь план развития** - учитывая конкретные слабые места, которые ты видишь в ответах
4. **Подбери ресурсы** - для тех тем, где были ошибки
5. **Мотивируй** - покажи, что ошибки - это нормально и как их превратить в опыт

## ФОРМАТ ОТВЕТА:
# Персональный план развития для {user_name}

## Анализ ваших ответов
Проанализировав ваши ответы на {len(q_details)} вопросов, я вижу следующие паттерны:
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
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    # Using Responses API with GPT-5 family models (gpt-5.1, gpt-5-mini, gpt-5-nano)
    # Format: instructions (system prompt) + input (user prompt as string)
    response = await client.responses.create(
        model=settings.OPENAI_MODEL,
        instructions=system_prompt,
        input=prompt,
        reasoning={"effort": settings.OPENAI_REASONING_EFFORT},
        max_output_tokens=settings.OPENAI_MAX_TOKENS
    )

    return response.output_text
