import os

from app.deps import verify_api_key
from app.models import RecommendationRequest
from fastapi import APIRouter, Depends, HTTPException, Response
from openai import AsyncOpenAI, OpenAIError

router = APIRouter()

@router.post("/recommendations", response_class=Response, dependencies=[Depends(verify_api_key)])
async def get_recommendations(req: RecommendationRequest):
    user = req.user
    level = req.level
    strengths = req.strengths
    weaknesses = req.weaknesses
    overallScore = req.overallScore
    question_details = req.question_details if hasattr(req, 'question_details') else []

    strong_str = ', '.join(f'{s["name"]} ({s["score"]}%)' for s in strengths) or 'Требуют развития'
    weak_str = ', '.join(f'{w["name"]} ({w["score"]}%)' for w in weaknesses) or 'Нет явных'

    # Анализируем детали вопросов для персонализации
    incorrect_answers = [qd for qd in question_details if qd.get("user_score", 0) < qd.get("max_score", 5)]
    correct_answers = [qd for qd in question_details if qd.get("user_score", 0) == qd.get("max_score", 5)]
    
    # Создаем детальный анализ ошибок
    errors_analysis = ""
    if question_details:
        errors_by_category = {}
        for qd in incorrect_answers:
            cat_name = next((cat["name"] for cat in [{"name": "API Design"}, {"name": "Базы данных"}, {"name": "Документирование"}, {"name": "Асинхронные взаимодействия"}, {"name": "Проектирование систем"}, {"name": "Безопасность"}, {"name": "Аналитическое мышление"}, {"name": "Коммуникации"}] if cat["name"] in qd.get("learning_tip", "")), "Общие")
            if cat_name not in errors_by_category:
                errors_by_category[cat_name] = []
            errors_by_category[cat_name].append(qd)
        
        for cat, errors in errors_by_category.items():
            if errors:
                errors_analysis += f"\n**{cat}** - {len(errors)} ошибок:\n"
                for error in errors[:3]:
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
Кандидат: {user.name}
Опыт: {user.experience}
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
{chr(10).join([f"- {qd.get('question_text', '')[:80]}... (Ваш ответ: {qd.get('user_answer_text', '')}, Правильный: {qd.get('correct_answer_text', '')})" for qd in incorrect_answers[:5]]) if incorrect_answers else "Нет данных о конкретных вопросах"}

## ТВОЯ ЗАДАЧА:
1. **Проанализируй конкретные ошибки** - посмотри на вопросы, где были ошибки, и объясни, почему это важно
2. **Дай персональные советы** - основываясь на реальных ответах пользователя, а не на общих категориях
3. **Составь план развития** - учитывая конкретные слабые места, которые ты видишь в ответах
4. **Подбери ресурсы** - для тех тем, где были ошибки
5. **Мотивируй** - покажи, что ошибки - это нормально и как их превратить в опыт

## ФОРМАТ ОТВЕТА:
# Персональный план развития для {user.name}

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
        client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        response = await client.responses.create(
            model="gpt-5.2-mini",
            reasoning={"effort": "medium"},
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_output_tokens=4000
        )
        content = response.output_text
    except OpenAIError as e:
        print(f"OpenAI error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OpenAI error: {str(e)}")
    except Exception as e:
        print(f"General error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

    return Response(content, media_type="text/markdown")
