from typing import List

from app.cache import get_cached_questions
from app.deps import verify_api_key
from app.models import Question
from fastapi import APIRouter, Depends

router = APIRouter()

@router.get("/questions", response_model=List[Question], dependencies=[Depends(verify_api_key)])
async def get_questions():
    questions = await get_cached_questions()
    # Ensure fields match what was requested originally if strict filtering is needed,
    # but Pydantic response_model will handle extra fields.
    return questions
