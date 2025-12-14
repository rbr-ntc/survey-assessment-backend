import pytest
from app.services import calculate_scores
from app.utils import CATEGORIES

# Mock categories for testing
# Assuming the categories in app.utils are constant, we can use them directly.
# Or we can verify the behavior based on them.

class TestCalculateScores:
    """Tests for calculate_scores function"""

    def test_calculate_scores_basic(self):
        """Test basic score calculation"""
        # Define a mock question
        questions = [
            {
                "id": "q1",
                "category": "database",
                "type": "single_choice",
                "question": "What is SQL?",
                "options": [
                    {"value": "a", "text": "Structured Query Language"},
                    {"value": "b", "text": "Simple Query Language"}
                ],
                "weights": {"a": 5, "b": 0}
            }
        ]

        answers = {"q1": "a"}

        overallScore, level, categories, strengths, weaknesses, question_details = calculate_scores(questions, answers)

        # Check database category score
        # The calculation depends on other categories being 0, so the overall score might be low due to weights.
        # Let's check the specific category score.
        assert categories["database"]["score"] == 100

        # Check question details
        assert len(question_details) == 1
        assert question_details[0]["user_score"] == 5
        assert question_details[0]["max_score"] == 5
        assert question_details[0]["user_answer_value"] == "a"

    def test_calculate_scores_wrong_answer(self):
        """Test score calculation with wrong answer"""
        questions = [
            {
                "id": "q1",
                "category": "database",
                "type": "single_choice",
                "question": "What is SQL?",
                "options": [
                    {"value": "a", "text": "Structured Query Language"},
                    {"value": "b", "text": "Simple Query Language"}
                ],
                "weights": {"a": 5, "b": 0}
            }
        ]

        answers = {"q1": "b"}

        overallScore, level, categories, strengths, weaknesses, question_details = calculate_scores(questions, answers)

        assert categories["database"]["score"] == 0
        assert question_details[0]["user_score"] == 0

    def test_calculate_scores_mixed(self):
        """Test with multiple questions and categories"""
        questions = [
            {
                "id": "q1",
                "category": "database",
                "weights": {"a": 5},
                "options": [{"value": "a", "text": "A"}, {"value": "b", "text": "B"}],
                "question": "Q1"
            },
            {
                "id": "q2",
                "category": "api",
                "weights": {"a": 5},
                "options": [{"value": "a", "text": "A"}, {"value": "b", "text": "B"}],
                "question": "Q2"
            }
        ]

        answers = {"q1": "a", "q2": "a"}

        overallScore, level, categories, strengths, weaknesses, question_details = calculate_scores(questions, answers)

        assert categories["database"]["score"] == 100
        assert categories["api"]["score"] == 100

        assert overallScore < 30

from unittest.mock import MagicMock, AsyncMock, patch
from app.services import generate_recommendations_content

class TestGenerateRecommendations:
    """Tests for generate_recommendations_content"""

    @pytest.mark.asyncio
    @patch("app.services.AsyncOpenAI")
    async def test_generate_recommendations(self, mock_openai_cls):
        """Test generating recommendations with mocked OpenAI"""
        mock_client = AsyncMock()
        mock_openai_cls.return_value = mock_client

        # Mock responses.create for new model
        mock_response = MagicMock()
        mock_response.output_text = "Test recommendations"
        mock_client.responses.create.return_value = mock_response

        recommendations = await generate_recommendations_content(
            user_name="User",
            user_experience="Junior",
            level={"level": "Junior"},
            overallScore=50,
            strengths=[],
            weaknesses=[],
            question_details=[]
        )

        assert recommendations == "Test recommendations"
        mock_client.responses.create.assert_called_once()
