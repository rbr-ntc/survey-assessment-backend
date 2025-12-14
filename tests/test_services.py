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

        # Since only these two categories have max_score > 0, they contribute to the overall score.
        # But wait, the logic iterates over ALL categories in `CATEGORIES`.
        # If `category_max_scores[cat]` is 0, score is 0.
        # `weighted_sum` sums `categories[cat]["score"] * CATEGORIES[cat]['weight']`.
        # `total_weight` sums `CATEGORIES[cat]['weight']` for ALL categories.
        # So if we only answer questions for 2 categories, the others will have 0 score, pulling down the average.

        # Let's verify this behavior.
        # database weight 1.1, api weight 1.1.
        # score 100 for both.
        # weighted_sum = 100 * 1.1 + 100 * 1.1 = 220.
        # total_weight = sum of all weights.
        # There are 9 categories. Weights:
        # doc: 1, modeling: 1.2, api: 1.1, db: 1.1, messaging: 1, sys_design: 1.3, sec: 1, analyt: 1.2, comm: 1
        # Total weight = 1+1.2+1.1+1.1+1+1.3+1+1.2+1 = 9.9
        # overall = 220 / 9.9 = 22.22

        assert overallScore < 30
