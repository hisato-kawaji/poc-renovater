#!/bin/bash
set -e

PROJECT_ID="YOUR_PROJECT_ID"
REPO="YOUR_GITHUB_ACCOUNT/poc-foundry-agy"
SA_NAME="github-actions"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
POOL_NAME="github-pool"
PROVIDER_NAME="github-provider"

echo "Creating Service Account..."
gcloud iam service-accounts create $SA_NAME --project $PROJECT_ID --display-name "GitHub Actions Deploy" || echo "SA already exists"

echo "Granting roles..."
for ROLE in roles/run.admin roles/cloudbuild.builds.builder roles/storage.admin roles/iam.serviceAccountUser roles/artifactregistry.writer roles/secretmanager.secretAccessor; do
  gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:${SA_EMAIL}" --role="$ROLE" > /dev/null
done

echo "Creating Workload Identity Pool..."
gcloud iam workload-identity-pools create $POOL_NAME --project=$PROJECT_ID --location="global" --display-name="GitHub Actions Pool" || echo "Pool already exists"

echo "Creating Workload Identity Provider..."
gcloud iam workload-identity-pools providers create-oidc $PROVIDER_NAME \
  --project=$PROJECT_ID --location="global" --workload-identity-pool=$POOL_NAME \
  --display-name="GitHub Actions Provider" --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com" || echo "Provider error"

echo "Binding Repo to SA..."
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
gcloud iam service-accounts add-iam-policy-binding $SA_EMAIL \
  --project=$PROJECT_ID \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_NAME}/attribute.repository/${REPO}" > /dev/null

echo "Setup complete!"
echo "WIF_PROVIDER=projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_NAME}/providers/${PROVIDER_NAME}"
echo "SA_EMAIL=${SA_EMAIL}"
