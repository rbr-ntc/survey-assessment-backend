import os

from app.deps import verify_api_key
from app.models import RecommendationRequest
from app.services import generate_recommendations_content
from fastapi import APIRouter, Depends, HTTPException, Response
from openai import OpenAIError

router = APIRouter()

@router.post("/recommendations", response_class=Response, dependencies=[Depends(verify_api_key)])
async def get_recommendations(req: RecommendationRequest):
    user = req.user
    level = req.level
    strengths = req.strengths
    weaknesses = req.weaknesses
    overallScore = req.overallScore
    question_details = req.question_details if hasattr(req, 'question_details') else []

    try:
        user_name = user.name
        user_experience = user.experience

        content = await generate_recommendations_content(
            user_name,
            user_experience,
            level,
            overallScore,
            strengths,
            weaknesses,
            question_details
        )
    except OpenAIError as e:
        print(f"OpenAI error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OpenAI error: {str(e)}")
    except Exception as e:
        print(f"General error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

    return Response(content, media_type="text/markdown")
