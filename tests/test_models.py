import pytest
from app.models import QuestionDetail, Result, SubmitRequest, UserInfo
from pydantic import ValidationError


class TestQuestionDetail:
    """Тесты для модели QuestionDetail"""
    
    def test_valid_question_detail(self):
        """Тест создания валидного QuestionDetail"""
        data = {
            "question_id": "test1",
            "question_text": "Test question?",
            "user_answer_value": "a",
            "user_answer_text": "Test answer A",
            "correct_answer_value": "b",
            "correct_answer_text": "Test answer B",
            "user_score": 3,
            "max_score": 5,
            "explanation": "User chose A but B is correct",
            "difficulty": "medium",
            "learning_tip": "Study this topic more"
        }
        
        question_detail = QuestionDetail(**data)
        assert question_detail.question_id == "test1"
        assert question_detail.user_score == 3
        assert question_detail.max_score == 5
    
    def test_invalid_question_detail_missing_fields(self):
        """Тест валидации при отсутствии обязательных полей"""
        with pytest.raises(ValidationError):
            QuestionDetail(
                question_id="test1",
                question_text="Test question?"
                # Отсутствуют другие обязательные поля
            )

class TestResult:
    """Тесты для модели Result"""
    
    def test_valid_result(self):
        """Тест создания валидного Result"""
        data = {
            "overallScore": 75,
            "level": {"level": "Middle", "description": "Test level"},
            "categories": {"test": {"score": 75, "weight": 1.0, "name": "Test"}},
            "strengths": [{"name": "Test", "score": 80}],
            "weaknesses": [{"name": "Test", "score": 60}],
            "question_details": []
        }
        
        result = Result(**data)
        assert result.overallScore == 75
        assert result.level["level"] == "Middle"
        assert len(result.categories) == 1
    
    def test_result_without_question_details(self):
        """Тест создания Result без question_details"""
        data = {
            "overallScore": 75,
            "level": {"level": "Middle", "description": "Test level"},
            "categories": {"test": {"score": 75, "weight": 1.0, "name": "Test"}},
            "strengths": [{"name": "Test", "score": 80}],
            "weaknesses": [{"name": "Test", "score": 60}]
        }
        
        result = Result(**data)
        assert result.question_details is None

class TestUserInfo:
    """Тесты для модели UserInfo"""
    
    def test_valid_user_info(self):
        """Тест создания валидного UserInfo"""
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "experience": "3 years"
        }
        
        user_info = UserInfo(**data)
        assert user_info.name == "John Doe"
        assert user_info.email == "john@example.com"
        assert user_info.experience == "3 years"
    
    def test_user_info_empty_fields(self):
        """Тест валидации при пустых полях"""
        with pytest.raises(ValidationError):
            UserInfo(
                name="",
                email="",
                experience=""
            )

class TestSubmitRequest:
    """Тесты для модели SubmitRequest"""
    
    def test_valid_submit_request(self):
        """Тест создания валидного SubmitRequest"""
        data = {
            "user": {
                "name": "John Doe",
                "email": "john@example.com",
                "experience": "3 years"
            },
            "answers": {
                "q1": "a",
                "q2": "b"
            }
        }
        
        submit_request = SubmitRequest(**data)
        assert submit_request.user.name == "John Doe"
        assert len(submit_request.answers) == 2
        assert submit_request.answers["q1"] == "a"
