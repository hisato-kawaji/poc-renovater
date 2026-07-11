#!/bin/bash
set -e

PROJECT_ID="YOUR_PROJECT_ID"
REGION="asia-northeast1"
REPO_NAME="poc-renovater"
REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}"

# Authenticate Docker to GCP Artifact Registry
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

# 1. Build & Push API
echo "Building API..."
docker build --platform linux/amd64 -t ${REGISTRY}/api:latest -f apps/api/Dockerfile .
docker push ${REGISTRY}/api:latest

# 2. Deploy API to Cloud Run
echo "Deploying API to Cloud Run..."
gcloud run deploy poc-renovater-api \
  --image ${REGISTRY}/api:latest \
  --region ${REGION} \
  --project ${PROJECT_ID} \
  --set-secrets="/secrets/env/.env=poc-renovater-api-env:latest" \
  --quiet

API_URL=$(gcloud run services describe poc-renovater-api --region ${REGION} --project ${PROJECT_ID} --format="value(status.url)")
echo "API deployed to: $API_URL"

# 3. Build & Push Web
echo "Building Web with API_URL=${API_URL}..."
cd apps/web
# Next.js standalone requires configuration in next.config.ts: output: 'standalone'
grep -q "standalone" next.config.ts || echo "Make sure to add output: 'standalone' to next.config.ts"
docker build --platform linux/amd64 --build-arg API_URL=${API_URL} -t ${REGISTRY}/web:latest .
docker push ${REGISTRY}/web:latest
cd ../../

# 4. Deploy Web to Cloud Run
echo "Deploying Web to Cloud Run..."
gcloud run deploy poc-renovater-web \
  --image ${REGISTRY}/web:latest \
  --region ${REGION} \
  --project ${PROJECT_ID} \
  --set-env-vars API_URL=${API_URL} \
  --quiet

