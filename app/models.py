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


# Quiz models for universal test system
class CategoryConfig(BaseModel):
    """Category configuration for a quiz"""
    name: str
    icon: str
    weight: float
    description: Optional[str] = None


class LevelConfig(BaseModel):
    """Level configuration for a quiz"""
    min_score: int
    icon: str
    description: str
    next_level: str
    min_years: Optional[str] = None


class QuizSettings(BaseModel):
    """Quiz settings"""
    shuffle_questions: bool = False
    shuffle_options: bool = False
    show_correct_answers: bool = True
    allow_skip: bool = False
    time_limit: Optional[int] = None  # minutes
    max_attempts: Optional[int] = None


class QuizContent(BaseModel):
    """Quiz content model (stored in MongoDB)"""
    id: str = Field(..., alias="_id", description="Quiz ID (e.g., 'quiz:system-analyst-assessment')")
    type: str = Field(..., description="Type: assessment | quiz | practice")
    title: str
    description: str
    slug: str
    level: str = Field(default="all", description="beginner | intermediate | advanced | all")
    duration_minutes: Optional[int] = None
    passing_score: int = Field(default=50, ge=0, le=100)
    categories: Dict[str, CategoryConfig]
    level_config: Dict[str, LevelConfig]
    question_ids: List[str] = Field(default_factory=list, description="List of question IDs")
    settings: QuizSettings = Field(default_factory=QuizSettings)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        populate_by_name = True
        validate_by_name = True


class QuizResponse(BaseModel):
    """Quiz response (for API)"""
    id: str
    type: str
    title: str
    description: str
    slug: str
    level: str
    duration_minutes: Optional[int]
    passing_score: int
    categories: Dict[str, CategoryConfig]
    level_config: Dict[str, LevelConfig]
    question_count: int
    settings: QuizSettings


class StartQuizRequest(BaseModel):
    """Request to start a quiz attempt"""
    pass  # No additional data needed, user_id comes from token


class StartQuizResponse(BaseModel):
    """Response when starting a quiz"""
    attempt_id: str
    quiz: QuizResponse
    questions: List[Question]


class SubmitQuizRequest(BaseModel):
    """Request to submit quiz answers"""
    answers: Dict[str, str]  # {question_id: selected_value}


class QuizAttemptResponse(BaseModel):
    """Quiz attempt result"""
    attempt_id: str
    quiz_id: str
    status: str  # in_progress | completed | abandoned
    score: Optional[int] = None
    level: Optional[str] = None
    passed: Optional[bool] = None
    started_at: str
    completed_at: Optional[str] = None
    time_spent_seconds: Optional[int] = None
    category_scores: Optional[Dict[str, int]] = None
    strengths: Optional[List[Dict]] = None
    weaknesses: Optional[List[Dict]] = None
    recommendations: Optional[str] = None
    question_details: Optional[List[QuestionDetail]] = None
