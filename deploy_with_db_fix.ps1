# PowerShell script to build and deploy the ERP system to Google Cloud Run with database fix

# Set variables
$PROJECT_ID = "erp-system-445701"  # Project ID from your existing deployment
$IMAGE_NAME = "erp-system"
$VERSION = "v18"  # Increment version for the database fix deployment
$REGION = "us-central1"  # Region from your existing deployment
$SERVICE_NAME = "erp-system"  # Your existing service name

# Cloud SQL connection details
$CLOUD_SQL_INSTANCE = "erp-database"  # Your Cloud SQL instance name
$DB_NAME = "erpsystem"
$DB_USER = "erpuser"  # Your database username
$DB_PASS = "ERPuser2025!"  # Your database password

# Build the Docker image
Write-Host "Building Docker image: $IMAGE_NAME`:$VERSION with discount feature fix"
docker build -t $IMAGE_NAME`:$VERSION .

# Tag the image for Google Container Registry
Write-Host "Tagging image for Google Container Registry"
docker tag $IMAGE_NAME`:$VERSION gcr.io/$PROJECT_ID/$IMAGE_NAME`:$VERSION

# Push the image to Google Container Registry
Write-Host "Pushing image to Google Container Registry"
docker push gcr.io/$PROJECT_ID/$IMAGE_NAME`:$VERSION

# Create DATABASE_URL for Cloud SQL PostgreSQL connection
$DATABASE_URL = "postgresql://${DB_USER}:${DB_PASS}@/erpsystem?host=/cloudsql/${PROJECT_ID}:${REGION}:${CLOUD_SQL_INSTANCE}"

# Deploy to Cloud Run with Cloud SQL connection
Write-Host "Deploying to Cloud Run with discount feature fix"
gcloud run deploy $SERVICE_NAME `
  --image gcr.io/$PROJECT_ID/$IMAGE_NAME`:$VERSION `
  --platform managed `
  --region $REGION `
  --allow-unauthenticated `
  --memory 512Mi `
  --cpu 1 `
  --port 8080 `
  --add-cloudsql-instances "${PROJECT_ID}:${REGION}:${CLOUD_SQL_INSTANCE}" `
  --set-env-vars="FLASK_CONFIG=production,SECRET_KEY=your-secret-key-here,DATABASE_URL=${DATABASE_URL}"

# Ensure traffic is routed to the latest revision
Write-Host "Ensuring traffic is routed to the latest revision..."
gcloud run services update-traffic $SERVICE_NAME --region $REGION --to-latest

# Connect to Cloud SQL to run the database fix
Write-Host "Running database fix for discount feature..."
# Package and upload the database fix script to the deployed cloud run service
gcloud beta run jobs create fix-database-one-time `
  --image gcr.io/$PROJECT_ID/$IMAGE_NAME`:$VERSION `
  --tasks 1 `
  --region $REGION `
  --set-cloudsql-instances "${PROJECT_ID}:${REGION}:${CLOUD_SQL_INSTANCE}" `
  --set-env-vars="DB_USER=${DB_USER},DB_PASS=${DB_PASS},DB_NAME=${DB_NAME},DB_HOST=/cloudsql/${PROJECT_ID}:${REGION}:${CLOUD_SQL_INSTANCE}" `
  --command "python" `
  --args "cloud_db_fix.py"

# Run the fix database job
Write-Host "Executing database fix job..."
gcloud beta run jobs execute fix-database-one-time --region $REGION

Write-Host "Deployment complete! Your application should be available at:"
Write-Host "https://$SERVICE_NAME-773057744195.$REGION.run.app"
Write-Host ""
Write-Host "Key improvements in this deployment:"
Write-Host "- Fixed database schema for discount feature"
Write-Host "- Added proper handling of discount_amount in cloud database"
Write-Host "- Fixed payment processing with discounts" 