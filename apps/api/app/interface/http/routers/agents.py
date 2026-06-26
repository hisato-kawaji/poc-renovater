from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict
from app.deps import get_deps, Deps
from app.application.agents.ingest import IngestAgentClient
from app.application.agents.charter import CharterAgentClient
from google.cloud import firestore

router = APIRouter()

import zipfile
import io

class AnalyzeRequest(BaseModel):
    uploadId: str

@router.post("/agents:analyze")
async def analyze_agent(req: AnalyzeRequest, deps: Deps = Depends(get_deps)):
    # Download zip
    zip_bytes = deps.storage.download_zip(req.uploadId)
    
    # Extract source_tree and file_contents
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
                    pass # ignore binary files
    
    source_tree_str = "\\n".join(source_tree)
    
    client = IngestAgentClient(deps)
    analysis = await client.analyze(source_tree_str, file_contents)
    
    charter_client = CharterAgentClient(deps)
    charter_eval = await charter_client.evaluate(analysis, source_tree_str, file_contents)
    
    status = "REJECTED"
    if charter_eval.isPassed and charter_eval.score >= deps.settings.charter_score_threshold:
        status = "PASSED"
        
    import asyncio
    db = firestore.Client(project=deps.settings.google_cloud_project)
    
    def _save():
        doc_ref = db.collection("agents").document(req.uploadId)
        doc_ref.set({
            "id": req.uploadId,
            "status": status,
            "analysis": analysis.model_dump(),
            "charter": charter_eval.model_dump()
        })
    await asyncio.to_thread(_save)
    
    return {
        "agentId": req.uploadId, 
        "status": status,
        "analysis": analysis.model_dump(),
        "charter": charter_eval.model_dump()
    }

from fastapi import HTTPException
from app.application.agents.repo import RepoAgentClient
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../../packages")))
from shared.python.schemas import Analysis, CharterEvaluation

@router.post("/agents/{upload_id}:register")
async def register_agent(upload_id: str, deps: Deps = Depends(get_deps)):
    import asyncio
    db = firestore.Client(project=deps.settings.google_cloud_project)
    
    doc_ref = db.collection("agents").document(upload_id)
    doc = await asyncio.to_thread(doc_ref.get)
    if not doc.exists:
        raise HTTPException(status_code=404, detail="not found")
        
    data = doc.to_dict()
    if data.get("status") != "PASSED":
        raise HTTPException(status_code=409, detail="Agent has not passed the Charter Gate")
        
    analysis = Analysis.model_validate(data["analysis"])
    charter = CharterEvaluation.model_validate(data["charter"])
    
    zip_bytes = deps.storage.download_zip(upload_id)
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
    source_tree_str = "\\n".join(source_tree)
    
    client = RepoAgentClient(deps)
    plan = await client.plan(upload_id, analysis, charter)
    repo_url, repo_name = await client.execute(plan, source_tree_str, file_contents)
    
    def _update():
        doc_ref.update({
            "status": "REGISTERED",
            "repo": {
                "provider": "github",
                "fullName": f"{deps.settings.github_org}/{repo_name}",
                "url": repo_url
            }
        })
    await asyncio.to_thread(_update)
    
    return {"repoUrl": repo_url}

from app.application.agents.issue_planner import IssuePlannerClient

@router.post("/agents/{upload_id}/issues:plan")
async def plan_issues(upload_id: str, deps: Deps = Depends(get_deps)):
    import asyncio
    db = firestore.Client(project=deps.settings.google_cloud_project)
    
    doc_ref = db.collection("agents").document(upload_id)
    doc = await asyncio.to_thread(doc_ref.get)
    if not doc.exists:
        raise HTTPException(status_code=404, detail="not found")
        
    data = doc.to_dict()
    if data.get("status") not in ["REGISTERED", "MERGED", "IDLE"]:
        raise HTTPException(status_code=409, detail="Agent is not ready for issue planning")
        
    analysis = Analysis.model_validate(data["analysis"])
    charter = CharterEvaluation.model_validate(data["charter"])
    repo_name = data["repo"]["fullName"].split("/")[-1]
    
    client = IssuePlannerClient(deps)
    plan = await client.plan(analysis, charter)
    created_issues = await client.execute(repo_name, plan)
    
    def _update():
        doc_ref.update({
            "status": "PLANNING"
        })
        for i, issue in enumerate(plan.issues):
            doc_ref.collection("issues").add({
                "title": issue.title,
                "type": issue.type,
                "body": issue.body,
                "status": "open",
                "priority": issue.priority,
                "url": created_issues[i]["url"]
            })
    await asyncio.to_thread(_update)
    
    return {"issues": created_issues}

from app.application.agents.coding import CodingAgentClient

@router.post("/agents/{upload_id}/issues/{issue_id}:implement")
async def implement_issue(upload_id: str, issue_id: str, deps: Deps = Depends(get_deps)):
    import asyncio
    db = firestore.Client(project=deps.settings.google_cloud_project)
    
    doc_ref = db.collection("agents").document(upload_id)
    doc = await asyncio.to_thread(doc_ref.get)
    if not doc.exists:
        raise HTTPException(status_code=404, detail="agent not found")
    
    data = doc.to_dict()
    charter = CharterEvaluation.model_validate(data["charter"])
    repo_name = data["repo"]["fullName"].split("/")[-1]
    
    issues = await asyncio.to_thread(lambda: list(doc_ref.collection("issues").get()))
    issue_doc = next((i for i in issues if i.id == issue_id), None)
    if not issue_doc:
        raise HTTPException(status_code=404, detail="issue not found")
        
    issue_data = issue_doc.to_dict()
    
    client = CodingAgentClient(deps)
    code_change = await client.implement(issue_data, charter, repo_name)
    url, branch = await client.execute(repo_name, code_change)
    
    def _update():
        doc_ref.update({
            "status": "PR_OPEN"
        })
        issue_doc.reference.update({
            "status": "in_progress",
            "prUrl": url
        })
        doc_ref.collection("pulls").add({
            "issueId": issue_id,
            "branch": branch,
            "status": "open",
            "reviewState": "pending",
            "url": url
        })
    await asyncio.to_thread(_update)
    
    return {"prUrl": url, "branch": branch}

from app.application.agents.review import ReviewAgentClient

@router.post("/agents/{upload_id}/pulls/{pr_number}:review")
async def review_pull(upload_id: str, pr_number: int, deps: Deps = Depends(get_deps)):
    import asyncio
    db = firestore.Client(project=deps.settings.google_cloud_project)
    
    doc_ref = db.collection("agents").document(upload_id)
    doc = await asyncio.to_thread(doc_ref.get)
    if not doc.exists:
        raise HTTPException(status_code=404, detail="agent not found")
        
    data = doc.to_dict()
    charter = CharterEvaluation.model_validate(data["charter"])
    repo_name = data["repo"]["fullName"].split("/")[-1]
    
    pulls = await asyncio.to_thread(lambda: list(doc_ref.collection("pulls").get()))
    pull_doc = next((p for p in pulls if str(pr_number) in p.to_dict().get("url", "")), None)
    
    issue_data = {}
    if pull_doc:
        issue_id = pull_doc.to_dict().get("issueId")
        if issue_id:
            issues = await asyncio.to_thread(lambda: list(doc_ref.collection("issues").get()))
            issue_d = next((i for i in issues if i.id == issue_id), None)
            if issue_d:
                issue_data = issue_d.to_dict()
                
    diff = deps.scm.get_pr_diff(repo_name, pr_number)
    
    client = ReviewAgentClient(deps)
    review_result = await client.review(diff, charter, issue_data)
    await client.execute(repo_name, pr_number, review_result)
    
    def _update():
        doc_ref.update({
            "status": "PREVIEW_READY" if review_result.state == "approved" else "CHANGES_REQUESTED"
        })
        if pull_doc:
            pull_doc.reference.update({
                "reviewState": review_result.state
            })
    await asyncio.to_thread(_update)
    
    return {"state": review_result.state, "comments": review_result.comments}

@router.post("/agents/{upload_id}/pulls/{pr_number}:deploy-preview")
async def deploy_preview(upload_id: str, pr_number: int, deps: Deps = Depends(get_deps)):
    import asyncio
    db = firestore.Client(project=deps.settings.google_cloud_project)
    doc_ref = db.collection("agents").document(upload_id)
    
    # Mock deploy for MVP
    service_name = f"poc-{upload_id[:8]}-pr{pr_number}"
    url = f"https://{service_name}-preview.run.app"
    
    def _update():
        doc_ref.collection("deployments").add({
            "prNumber": pr_number,
            "service": service_name,
            "url": url,
            "status": "ready"
        })
    await asyncio.to_thread(_update)
    return {"deployId": service_name, "url": url}

@router.post("/agents/{upload_id}/pulls/{pr_number}:approve")
async def approve_pull(upload_id: str, pr_number: int, deps: Deps = Depends(get_deps)):
    import asyncio
    db = firestore.Client(project=deps.settings.google_cloud_project)
    doc_ref = db.collection("agents").document(upload_id)
    doc = await asyncio.to_thread(doc_ref.get)
    repo_name = doc.to_dict()["repo"]["fullName"].split("/")[-1]
    
    # Merge PR
    deps.scm.review_pr(repo_name, pr_number, "approved", "Approved by human")
    # In a real app we'd call pr.merge(), let's just update DB for MVP
    
    def _update():
        doc_ref.update({"status": "MERGED"})
    await asyncio.to_thread(_update)
    return {"merged": True}

@router.post("/agents/{upload_id}:stop")
async def stop_agent(upload_id: str, deps: Deps = Depends(get_deps)):
    import asyncio
    db = firestore.Client(project=deps.settings.google_cloud_project)
    doc_ref = db.collection("agents").document(upload_id)
    def _update():
        doc_ref.update({"status": "IDLE"})
    await asyncio.to_thread(_update)
    return {"status": "stopped"}
