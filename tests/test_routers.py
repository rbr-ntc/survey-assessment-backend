import pytest
from app.routers.results import router
from app.models import SubmitRequest, UserInfo
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import MagicMock, AsyncMock, patch
from app.deps import verify_api_key

# Mock the database
mock_db = MagicMock()
mock_db.questions.find.return_value.to_list = AsyncMock(return_value=[
    {
        "id": "q1",
        "category": "database",
        "type": "single_choice",
        "question": "Q1",
        "options": [
            {"value": "a", "text": "A"},
            {"value": "b", "text": "B"}
        ],
        "weights": {"a": 5, "b": 0}
    }
])
# Mock insert_one as AsyncMock
mock_db.results.insert_one = AsyncMock()
mock_db.results.insert_one.return_value.inserted_id = "test_id"
mock_db.results.update_one = AsyncMock()

# Mock settings
from app.config import settings
settings.API_KEY = "test_key"

# Create a FastAPI app for testing
app = FastAPI()
app.include_router(router)

# Override dependency verification
async def override_verify_api_key():
    return True

app.dependency_overrides[verify_api_key] = override_verify_api_key

client = TestClient(app)

@patch("app.cache.db", mock_db)
@patch("app.routers.results.db", mock_db)
@patch("app.routers.results.generate_and_save_recommendations")
def test_submit_results(mock_bg_task):
    """Test submitting results"""
    data = {
        "user": {
            "name": "Test User",
            "email": "test@example.com",
            "experience": "Junior"
        },
        "answers": {
            "q1": "a"
        }
    }

    response = client.post("/results", json=data)

    assert response.status_code == 200
    assert response.json()["overallScore"] >= 0
    assert response.json()["result_id"] == "test_id"

@patch("app.routers.results.db", mock_db)
def test_get_result_by_id():
    """Test getting a result by ID"""
    # Setup mock return value for find_one
    mock_db.results.find_one = AsyncMock(return_value={
        "_id": "test_id",
        "user": {"name": "Test User", "experience": "Junior"},
        "overallScore": 80,
        "level": {"level": "Middle"},
        "categories": {},
        "created_at": "2024-01-01"
    })

    # We need to mock ObjectId as well because the router converts string to ObjectId
    with patch("app.routers.results.ObjectId") as mock_object_id:
        mock_object_id.return_value = "test_id_obj"

        response = client.get("/results/test_id")

        assert response.status_code == 200
        assert response.json()["user"]["name"] == "Test User"
