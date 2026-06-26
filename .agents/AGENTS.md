# PoC Foundry (Antigravity Rules)

## Overview
This file defines rules and constraints for Antigravity agents working on this project.
The project architecture strictly follows Hexagonal Architecture principles.

## Tech Stack
- Frontend: Next.js 15 App Router, TailwindCSS, TypeScript, pnpm
- Backend: Python 3.12, FastAPI, uv, Google ADK
- Infrastructure: GCP (Cloud Run, Firestore, GCS, Secret Manager), Terraform

## Rules
- **Backend Architecture**: All backend code must reside in `apps/api` and follow hexagonal architecture: `domain/`, `ports/`, `adapters/`, `application/`, `interface/`.
- **Domain Layer**: The `domain/` directory must have ZERO external dependencies. Only standard library and Pydantic are allowed.
- **Dependency Injection**: Use `deps.py` to inject `adapters` into `ports`. Do not import `adapters` directly from `application`.
- **Error Handling**: Use custom exceptions inherited from `FoundryError`. Do not raise `HTTPException` directly from use case or domain layers.
- **Firestore Transactions**: Must wrap updates and event appending in a single transaction. `agents/{id}.next_event_seq` must be atomically incremented.
- **Frontend State**: Initial load via server-side fetch from backend API. Live updates via `onSnapshot` in Client Components.

## Subagents
If you need to execute complex or long-running tasks (e.g. running multiple tests, debugging complex CI issues, or building a feature branch), invoke a subagent so it doesn't block the main conversation flow.
