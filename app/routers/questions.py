from typing import List

from app.db import db
from app.deps import verify_api_key
from app.models import Question
from fastapi import APIRouter, Depends

router = APIRouter()

@router.get("/questions", response_model=List[Question], dependencies=[Depends(verify_api_key)])
async def get_questions():
    cursor = db.questions.find({}, {"_id": 0, "id": 1, "category": 1, "type": 1, "question": 1, "options": 1})
    return [q async for q in cursor]
