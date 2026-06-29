# Todo App (Cloud Run Ready)

This is a stateless Next.js application that perfectly complies with the Cloud Run Charter.

## Architecture & Charter Compliance
- **Stateless:** All application state is stored in an external database (Firestore). The application itself is completely stateless.
- **Containerized:** A complete `Dockerfile` is provided for containerizing the application.
- **Environment Variables:** All configuration (like Firestore credentials) is done via environment variables (`.env`).
- **No Hardcoded Secrets:** There are absolutely no hardcoded secrets in the source code.

## Getting Started

1. Set up `.env` based on `.env.example`.
2. Run `npm install`
3. Run `npm run dev`
