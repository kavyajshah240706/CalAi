# deploy.ps1
# Robust deployment script for CalAi Backend using Google Cloud Run Source Deployments

Write-Host "Deploying CalAi Backend to Google Cloud Run..." -ForegroundColor Cyan

# Use gcloud run deploy with --source to bypass local Docker/Artifact Registry IAM issues.
# This pushes the source code securely to GCP, builds it remotely using Cloud Build, 
# and automatically deploys the resulting image to the Cloud Run service.

gcloud run deploy calai-backend `
    --source . `
    --region asia-south1 `
    --platform managed `
    --allow-unauthenticated `
    --min-instances 1 `
    --max-instances 5 `
    --memory 1Gi `
    --cpu 1 `
    --timeout 300 `
    --add-cloudsql-instances "gemini-project-2-500616:asia-south1:calai-db" `
    --set-env-vars "DATABASE_URL=postgresql://postgres:calai2026secure@34.93.198.130:5432/calai_db,INSTANCE_CONNECTION_NAME=gemini-project-2-500616:asia-south1:calai-db"

if ($LASTEXITCODE -eq 0) {
    Write-Host "Deployment Successful! 🚀" -ForegroundColor Green
    Write-Host "Live URL: https://calai-backend-1041961183692.asia-south1.run.app" -ForegroundColor Yellow
} else {
    Write-Host "Deployment Failed. Check the error logs above." -ForegroundColor Red
}
