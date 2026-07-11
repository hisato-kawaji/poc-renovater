from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class Analysis(BaseModel):
    techStack: List[str] = Field(description="Detected technologies")
    runInstructions: str = Field(description="How to run the application locally")
    databaseType: Optional[str] = Field(description="Type of database detected")
    secretsDetected: bool = Field(description="Whether any hardcoded secrets were detected")
    hasTests: bool = Field(description="Whether automated tests are present")
    hasReadme: bool = Field(description="Whether a README file is present")
    cloudRunReady: bool = Field(description="Whether the app appears ready for Cloud Run")
    missingElements: List[str] = Field(description="Missing elements to address")

class CharterEvaluation(BaseModel):
    score: int = Field(description="Score from 0 to 100 indicating Cloud Run readiness based on Charter")
    reasons: List[str] = Field(description="Reasons for the score, including any critical failures")
    isPassed: bool = Field(description="Whether the score meets the minimum threshold to pass")

class RepoPlan(BaseModel):
    repositoryName: str = Field(description="Name of the repository to create, prefixed with poc-")
    repositoryDescription: str = Field(description="Short description for the repo")
    readmeContent: str = Field(description="Generated README.md content based on Analysis and Charter")

class IssueItem(BaseModel):
    title: str = Field(description="Issue title")
    body: str = Field(description="Issue description and acceptance criteria")
    type: str = Field(description="chore|docs|security|test|refactor|ci|ops|feat")
    priority: int = Field(description="1 is highest priority")

class IssuePlan(BaseModel):
    issues: List[IssueItem]

class AutoFixIssuePlan(BaseModel):
    critical_analysis: str = Field(description="Step-by-step critical analysis of the codebase, evaluating potential build errors, DB config typos, and setup bugs. Justify whether autofix is needed.")
    issues: List[IssueItem] = Field(description="The list of autofix issues. Empty if no issues found.")

class CodeChange(BaseModel):
    branchName: str = Field(description="Branch name for the PR")
    prTitle: str = Field(description="PR Title")
    prBody: str = Field(description="PR Body (including changes, risks, rollback)")
    fileChanges: Dict[str, str] = Field(description="Map of file paths to their new contents")

class ReviewResult(BaseModel):
    state: str = Field(description="approved | changes_requested")
    comments: List[str] = Field(description="List of specific comments on the PR")

class Deployment(BaseModel):
    service: str = Field(description="Cloud Run service name")
    url: str = Field(description="URL of the deployed service")
    status: str = Field(description="ready | failed")
