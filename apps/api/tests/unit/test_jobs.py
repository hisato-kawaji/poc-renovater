import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.deps import get_deps, Deps
from app.domain.models import NotFoundError, ConflictError

@pytest.fixture
def mock_deps():
    deps = MagicMock(spec=Deps)
    deps.agent_repo = AsyncMock()
    deps.storage = AsyncMock()
    deps.scm = AsyncMock()
    deps.settings = MagicMock()
    deps.settings.pubsub_topic_tasks = "test-topic"
    deps.event_publisher = AsyncMock()
    deps.tenant_id = "test-tenant"
    return deps

@pytest.fixture
def client(mock_deps):
    app.dependency_overrides[get_deps] = lambda: mock_deps
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_get_jobs_success(client, mock_deps):
    mock_deps.agent_repo.get.return_value = {"id": "test-agent"}
    mock_deps.agent_repo.get_jobs.return_value = [{"id": "job-1", "status": "COMPLETED"}]
    
    res = client.get("/api/agents/test-agent/jobs")
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["id"] == "job-1"

def test_get_jobs_not_found(client, mock_deps):
    mock_deps.agent_repo.get.return_value = None
    
    res = client.get("/api/agents/test-agent/jobs")
    assert res.status_code == 404

def test_retry_job_success(client, mock_deps):
    mock_deps.agent_repo.get.return_value = {"id": "test-agent"}
    mock_deps.agent_repo.get_job.return_value = {"id": "job-1", "type": "analyze", "status": "FAILED"}
    
    res = client.post("/api/agents/test-agent/jobs/job-1/retry")
    assert res.status_code == 202
    assert res.json()["jobId"] == "job-1"
    
    mock_deps.agent_repo.update_job.assert_called_with("test-agent", "job-1", {"status": "PENDING", "error_details": None})
    mock_deps.event_publisher.publish.assert_called_once()

def test_retry_job_not_failed(client, mock_deps):
    mock_deps.agent_repo.get.return_value = {"id": "test-agent"}
    mock_deps.agent_repo.get_job.return_value = {"id": "job-1", "type": "analyze", "status": "COMPLETED"}
    
    res = client.post("/api/agents/test-agent/jobs/job-1/retry")
    assert res.status_code == 409

def test_retry_job_publish_error(client, mock_deps):
    mock_deps.agent_repo.get.return_value = {"id": "test-agent"}
    mock_deps.agent_repo.get_job.return_value = {"id": "job-1", "type": "analyze", "status": "FAILED"}
    mock_deps.event_publisher.publish.side_effect = Exception("PubSub Error")
    
    res = client.post("/api/agents/test-agent/jobs/job-1/retry")
    assert res.status_code == 500
    
    # Verify job was marked as failed again
    mock_deps.agent_repo.update_job.assert_any_call("test-agent", "job-1", {"status": "FAILED", "error_details": {"error": "PubSub Error"}})
