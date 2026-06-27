import zipfile
import io
import sys
import os
import logging
from typing import Dict, Any, Tuple
from app.deps import Deps
from app.application.agents.ingest import IngestAgentClient
from app.application.agents.charter import CharterAgentClient
from app.application.agents.repo import RepoAgentClient
from app.application.agents.issue_planner import IssuePlannerClient
from app.application.agents.coding import CodingAgentClient
from app.application.agents.review import ReviewAgentClient
from app.domain.repositories.agent_repository import AgentRepository
from app.ports.storage import StoragePort
from app.ports.scm import ScmPort
from app.settings import Settings
from app.domain.models import AgentStatus, NotFoundError, ConflictError

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../../packages")))
from shared.python.schemas import Analysis, CharterEvaluation

logger = logging.getLogger(__name__)

class AgentUseCase:
    def __init__(
        self,
        agent_repo: AgentRepository,
        storage: StoragePort,
        scm: ScmPort,
        settings: Settings,
        deps_for_clients: Deps # Still needed for AgentClients temporarily
    ):
        self.repo = agent_repo
        self.storage = storage
        self.scm = scm
        self.settings = settings
        self.deps = deps_for_clients

    def _extract_zip(self, zip_bytes: bytes) -> Tuple[str, Dict[str, str]]:
        source_tree = []
        file_contents = {}
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            for info in z.infolist():
                source_tree.append(info.filename)
                if not info.is_dir():
                    try:
                        content = z.read(info.filename).decode('utf-8')
                        file_contents[info.filename] = content
                    except UnicodeDecodeError:
                        pass
        return "\n".join(source_tree), file_contents

    async def mark_as_failed(self, upload_id: str, error_msg: str):
        try:
            await self.repo.update(upload_id, {"status": AgentStatus.ERROR.value, "error": error_msg})
        except Exception as e:
            logger.error(f"Failed to mark agent {upload_id} as failed: {e}", exc_info=True)

    async def analyze(self, upload_id: str) -> Dict[str, Any]:
        zip_bytes = self.storage.download_zip(upload_id)
        source_tree_str, file_contents = self._extract_zip(zip_bytes)

        client = IngestAgentClient(self.deps)
        analysis = await client.analyze(source_tree_str, file_contents)

        charter_client = CharterAgentClient(self.deps)
        charter_eval = await charter_client.evaluate(analysis, source_tree_str, file_contents)

        status = AgentStatus.REJECTED
        if charter_eval.isPassed and charter_eval.score >= self.settings.charter_score_threshold:
            status = AgentStatus.PASSED

        await self.repo.save(upload_id, {
            "id": upload_id,
            "status": status.value,
            "analysis": analysis.model_dump(),
            "charter": charter_eval.model_dump()
        })

        return {
            "uploadId": upload_id,
            "status": status.value,
            "analysis": analysis.model_dump(),
            "charter": charter_eval.model_dump()
        }

    async def ensure_can_register(self, upload_id: str):
        doc = await self.repo.get(upload_id)
        if not doc:
            raise NotFoundError(f"Agent {upload_id} not found")
        if doc.get("status") != AgentStatus.PASSED.value:
            raise ConflictError("Agent has not passed the Charter Gate")

    async def register(self, upload_id: str) -> Dict[str, Any]:
        doc = await self.repo.get(upload_id)
        if not doc:
            raise NotFoundError(f"Agent {upload_id} not found")

        analysis = Analysis.model_validate(doc["analysis"])
        charter = CharterEvaluation.model_validate(doc["charter"])

        zip_bytes = self.storage.download_zip(upload_id)
        source_tree_str, file_contents = self._extract_zip(zip_bytes)

        client = RepoAgentClient(self.deps)
        plan = await client.plan(upload_id, analysis, charter)
        repo_url, repo_name = await client.execute(plan, source_tree_str, file_contents)

        await self.repo.update(upload_id, {
            "status": AgentStatus.REGISTERED.value,
            "repo": {
                "provider": "github",
                "fullName": f"{self.settings.github_org}/{repo_name}",
                "url": repo_url
            }
        })
        return {"repoUrl": repo_url}

    async def ensure_can_plan_issues(self, upload_id: str):
        doc = await self.repo.get(upload_id)
        if not doc:
            raise NotFoundError(f"Agent {upload_id} not found")
        if doc.get("status") not in [AgentStatus.REGISTERED.value, AgentStatus.MERGED.value, AgentStatus.IDLE.value]:
            raise ConflictError("Agent is not ready for issue planning")

    async def plan_issues(self, upload_id: str) -> Dict[str, Any]:
        doc = await self.repo.get(upload_id)
        if not doc:
            raise NotFoundError(f"Agent {upload_id} not found")

        analysis = Analysis.model_validate(doc["analysis"])
        charter = CharterEvaluation.model_validate(doc["charter"])
        repo_name = doc["repo"]["fullName"].split("/")[-1]

        client = IssuePlannerClient(self.deps)
        plan = await client.plan(analysis, charter)
        created_issues = await client.execute(repo_name, plan)

        await self.repo.update(upload_id, {"status": AgentStatus.PLANNING.value})
        for i, issue in enumerate(plan.issues):
            issue_id = str(i+1)
            await self.repo.save_issue(upload_id, issue_id, {
                "title": issue.title,
                "type": issue.type,
                "body": issue.body,
                "status": "open",
                "priority": issue.priority,
                "url": created_issues[i]["url"]
            })

        return {"issues": created_issues}

    async def ensure_can_implement_issue(self, upload_id: str, issue_id: str):
        doc = await self.repo.get(upload_id)
        if not doc:
            raise NotFoundError(f"Agent {upload_id} not found")
        issues = await self.repo.get_issues(upload_id)
        if not any(i["id"] == issue_id for i in issues):
            raise NotFoundError(f"Issue {issue_id} not found")

    async def implement_issue(self, upload_id: str, issue_id: str) -> Dict[str, Any]:
        doc = await self.repo.get(upload_id)
        if not doc:
            raise NotFoundError(f"Agent {upload_id} not found")

        charter = CharterEvaluation.model_validate(doc["charter"])
        repo_name = doc["repo"]["fullName"].split("/")[-1]

        issues = await self.repo.get_issues(upload_id)
        issue_doc = next((i for i in issues if i["id"] == issue_id), None)
        if not issue_doc:
            raise NotFoundError(f"Issue {issue_id} not found")

        client = CodingAgentClient(self.deps)
        code_change = await client.implement(issue_doc, charter, repo_name)
        url, branch = await client.execute(repo_name, code_change)

        await self.repo.update(upload_id, {"status": AgentStatus.PR_OPEN.value})
        await self.repo.update_issue(upload_id, issue_id, {
            "status": "in_progress",
            "prUrl": url
        })
        await self.repo.save_pull(upload_id, {
            "issueId": issue_id,
            "branch": branch,
            "status": "open",
            "reviewState": "pending",
            "url": url
        })

        return {"prUrl": url, "branch": branch}

    async def ensure_can_review_pull(self, upload_id: str):
        doc = await self.repo.get(upload_id)
        if not doc:
            raise NotFoundError(f"Agent {upload_id} not found")

    async def review_pull(self, upload_id: str, pr_number: int) -> Dict[str, Any]:
        doc = await self.repo.get(upload_id)
        if not doc:
            raise NotFoundError(f"Agent {upload_id} not found")

        charter = CharterEvaluation.model_validate(doc["charter"])
        repo_name = doc["repo"]["fullName"].split("/")[-1]

        pulls = await self.repo.get_pulls(upload_id)
        pull_doc = next((p for p in pulls if str(pr_number) in p.get("url", "")), None)

        issue_data = {}
        if pull_doc:
            issue_id = pull_doc.get("issueId")
            if issue_id:
                issues = await self.repo.get_issues(upload_id)
                issue_d = next((i for i in issues if i["id"] == issue_id), None)
                if issue_d:
                    issue_data = issue_d

        diff = self.scm.get_pr_diff(repo_name, pr_number)

        client = ReviewAgentClient(self.deps)
        review_result = await client.review(diff, charter, issue_data)
        await client.execute(repo_name, pr_number, review_result)

        new_status = AgentStatus.PREVIEW_READY.value if review_result.state == "approved" else AgentStatus.CHANGES_REQUESTED.value
        await self.repo.update(upload_id, {"status": new_status})
        
        if pull_doc:
            await self.repo.update_pull(upload_id, pr_number, {
                "reviewState": review_result.state
            })

        return {"state": review_result.state, "comments": review_result.comments}

    async def get_charter_messages(self, upload_id: str) -> List[Dict[str, Any]]:
        doc = await self.repo.get(upload_id)
        if not doc:
            raise NotFoundError(f"Agent {upload_id} not found")
        return await self.repo.get_messages(upload_id)

    async def send_charter_message(self, upload_id: str, message: str) -> Dict[str, Any]:
        doc = await self.repo.get(upload_id)
        if not doc:
            raise NotFoundError(f"Agent {upload_id} not found")
        
        import datetime
        now = datetime.datetime.utcnow().isoformat() + "Z"
        
        # Save user message
        user_msg = {
            "role": "user",
            "content": message,
            "timestamp": now
        }
        await self.repo.save_message(upload_id, user_msg)
        
        # Get history
        messages = await self.repo.get_messages(upload_id)
        
        analysis_data = doc.get("analysis", {})
        charter_data = doc.get("charter", {})
        
        client = CharterAgentClient(self.deps)
        ai_response_text = await client.chat(analysis_data, charter_data, messages)
        
        now = datetime.datetime.utcnow().isoformat() + "Z"
        ai_msg = {
            "role": "assistant",
            "content": ai_response_text,
            "timestamp": now
        }
        await self.repo.save_message(upload_id, ai_msg)
        
        return ai_msg

    async def deploy_preview(self, upload_id: str, pr_number: int) -> Dict[str, Any]:
        service_name = f"poc-{upload_id[:8]}-pr{pr_number}"
        url = f"https://{service_name}-preview.run.app"
        await self.repo.save_deployment(upload_id, {
            "prNumber": pr_number,
            "service": service_name,
            "url": url,
            "status": "ready"
        })
        return {"deployId": service_name, "url": url}

    async def approve_pull(self, upload_id: str, pr_number: int) -> Dict[str, Any]:
        doc = await self.repo.get(upload_id)
        if not doc:
            raise NotFoundError(f"Agent {upload_id} not found")
            
        repo_name = doc["repo"]["fullName"].split("/")[-1]
        self.scm.review_pr(repo_name, pr_number, "approved", "Approved by human")
        await self.repo.update(upload_id, {"status": AgentStatus.MERGED.value})
        return {"merged": True}

    async def stop_agent(self, upload_id: str) -> Dict[str, Any]:
        await self.repo.update(upload_id, {"status": AgentStatus.IDLE.value})
        return {"status": "stopped"}
