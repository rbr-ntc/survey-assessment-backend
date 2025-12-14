from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Option(BaseModel):
    value: str
    text: str

class Question(BaseModel):
    id: str
    category: str
    type: str
    question: str
    options: List[Option]

class UserInfo(BaseModel):
    name: str = Field(..., min_length=1, description="Имя пользователя")
    email: str = Field(..., min_length=1, description="Email пользователя")
    experience: str = Field(..., min_length=1, description="Опыт пользователя")

class SubmitRequest(BaseModel):
    user: UserInfo
    answers: Dict[str, str]  # {question_id: selected_value}

class QuestionDetail(BaseModel):
    question_id: str
    question_text: str
    user_answer_value: str
    user_answer_text: str
    correct_answer_value: str
    correct_answer_text: str
    user_score: int
    max_score: int
    explanation: str
    difficulty: str
    learning_tip: str

class Result(BaseModel):
    overallScore: int
    level: dict
    categories: dict
    strengths: list
    weaknesses: list
    recommendations: Optional[str] = None
    question_details: Optional[List[QuestionDetail]] = None

class RecommendationRequest(BaseModel):
    user: UserInfo
    overallScore: int
    level: dict
    strengths: list
    weaknesses: list
    question_details: Optional[List[QuestionDetail]] = None

class RecommendationResponse(BaseModel):
    recommendations: str

class QuickTestRequest(BaseModel):
    test_type: str = Field(..., description="Тип теста: expert, intermediate, beginner, random")

class ResultWithId(Result):
    result_id: str
