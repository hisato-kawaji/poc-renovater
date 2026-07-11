import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
import json
import base64
from app.main import app

# For pubsub tests we might need to patch deps because events route initializes Deps internally.
# Looking at events.py:
# settings = get_settings()
# deps = Deps(settings, tenant_id)
# usecase = AgentUseCase(...)
# This means we should patch AgentUseCase directly or Deps.

@pytest.fixture
def mock_agent_repo(mocker):
    repo = AsyncMock()
    # Mock Deps completely
    mock_deps = mocker.patch("app.interface.http.routers.events.Deps")
    mock_deps_instance = mock_deps.return_value
    mock_deps_instance.agent_repo = repo
    mock_deps_instance.storage = AsyncMock()
    mock_deps_instance.scm = AsyncMock()
    mock_deps_instance.settings = MagicMock()
    mock_deps_instance.event_publisher = AsyncMock()
    return repo

@pytest.fixture
def mock_usecase_analyze(mocker):
    return mocker.patch("app.application.usecases.agent_usecase.AgentUseCase.analyze", new_callable=AsyncMock)

def test_pubsub_event_success(mock_agent_repo, mock_usecase_analyze, mocker):
    client = TestClient(app)
    
    payload = {"upload_id": "agent-1", "tenant_id": "tenant-1"}
    data_b64 = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")
    
    req_body = {
        "message": {
            "data": data_b64,
            "attributes": {"event_type": "analyze"},
            "messageId": "msg-123"
        },
        "subscription": "sub"
    }
    
    res = client.post("/api/events/pubsub", json=req_body)
    assert res.status_code == 200
    
    # check that job was created and updated
    mock_agent_repo.save_job.assert_called_once()
    mock_usecase_analyze.assert_called_once_with("agent-1")
    mock_agent_repo.update_job.assert_called_with("agent-1", "job-analyze", {"status": "COMPLETED"})

def test_pubsub_event_error_handling(mock_agent_repo, mock_usecase_analyze, mocker):
    client = TestClient(app)
    mock_usecase_analyze.side_effect = Exception("Vertex AI Timeout")
    
    payload = {"upload_id": "agent-1", "tenant_id": "tenant-1"}
    data_b64 = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")
    
    req_body = {
        "message": {
            "data": data_b64,
            "attributes": {"event_type": "analyze"},
            "messageId": "msg-123"
        },
        "subscription": "sub"
    }
    
    res = client.post("/api/events/pubsub", json=req_body)
    assert res.status_code == 200 # pubsub endpoint returns 200 to ack the message even on task failure
    
    # Check error recording
    mock_agent_repo.update_job.assert_called_with(
        "agent-1", "job-analyze", 
        {"status": "FAILED", "error_details": mocker.ANY}
    )
    mock_agent_repo.update.assert_called_with("agent-1", {"status": "ERROR"})
