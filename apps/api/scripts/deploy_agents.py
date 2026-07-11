#!/usr/bin/env python3
import os
import subprocess

agents = [
    ("packages.agents.ingest:build_ingest_agent", "ingest-agent"),
    ("packages.agents.charter:build_charter_agent", "charter-agent"),
    ("packages.agents.repo:build_repo_agent", "repo-agent"),
    ("packages.agents.issue_planner:build_issue_planner_agent", "issue-planner-agent"),
    ("packages.agents.coding.engine:build_coding_agent", "coding-agent"),
    ("packages.agents.review:build_review_agent", "review-agent"),
    ("packages.agents.self_improve:build_self_improve_agent", "self-improve-agent"),
]

def main():
    project = os.getenv("GOOGLE_CLOUD_PROJECT", "YOUR_PROJECT_ID")
    region = os.getenv("GOOGLE_CLOUD_REGION", "asia-northeast1")
    
    for agent_path, agent_name in agents:
        print(f"Deploying {agent_name}...")
        cmd = [
            "uv", "run", "adk", "deploy", "agent_engine",
            "--agent", agent_path,
            "--name", agent_name,
            "--project", project,
            "--location", region
        ]
        print(" ".join(cmd))
        # Note: In a real environment, you run this.
        # subprocess.run(cmd, check=True)

if __name__ == "__main__":
    main()
