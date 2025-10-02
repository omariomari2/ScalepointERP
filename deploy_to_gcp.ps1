# PowerShell script to build and deploy the ERP system to Google Cloud Run

# Set variables
$PROJECT_ID = "erp-system-445701"  # Correct project ID (project number is 773057744195)
$IMAGE_NAME = "erp-system"
$VERSION = "v20"  # Incrementing from v19 to v20 with attendance detail page feature
$REGION = "us-central1"  # Region from your existing deployment
$SERVICE_NAME = "erp-system"  # Updated to match the service name for the desired URL

# Cloud SQL connection details - Update these with your actual Cloud SQL settings
$CLOUD_SQL_INSTANCE = "erp-database"  # Updated to correct Cloud SQL instance name
$DB_NAME = "erpsystem"
$DB_USER = "erpuser"  # Your database username
$DB_PASS = "ERPuser2025!"  # Your database password

# Build the Docker image
Write-Host "Building Docker image: $IMAGE_NAME`:$VERSION with attendance detail page feature"
docker build -t $IMAGE_NAME`:$VERSION .

# Tag the image for Google Container Registry
Write-Host "Tagging image for Google Container Registry"
docker tag $IMAGE_NAME`:$VERSION gcr.io/$PROJECT_ID/$IMAGE_NAME`:$VERSION

# Push the image to Google Container Registry
Write-Host "Pushing image to Google Container Registry"
docker push gcr.io/$PROJECT_ID/$IMAGE_NAME`:$VERSION

# Create DATABASE_URL for Cloud SQL PostgreSQL connection
$DATABASE_URL = "postgresql://${DB_USER}:${DB_PASS}@/erpsystem?host=/cloudsql/${PROJECT_ID}:${REGION}:${CLOUD_SQL_INSTANCE}"

# Run database migration script to fix sales report issues
Write-Host "Running database migration to fix sales report issues..."

# Create a temporary container to run the migration
Write-Host "Creating temporary container to run migration..."
docker run --rm -v ${PWD}/migrations:/app/migrations -e DATABASE_URL="${DATABASE_URL}" gcr.io/$PROJECT_ID/$IMAGE_NAME`:$VERSION python /app/migrations/fix_sales_report.py

Write-Host "Database migration completed."

# Deploy to Cloud Run with Cloud SQL connection
Write-Host "Deploying to Cloud Run with attendance detail page feature"
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

Write-Host "Deployment complete! Your application should be available at:"
Write-Host "https://$SERVICE_NAME-773057744195.$REGION.run.app"
Write-Host ""
Write-Host "Key improvements in this deployment:"
Write-Host "1. Added detailed employee attendance profile page"
Write-Host "2. Enhanced attendance tracking with visual calendar view"
Write-Host "3. Added attendance analytics with check-in/out time distributions"
Write-Host "4. Implemented attendance metrics (attendance rate, on-time percentage)"
Write-Host "5. Added links from main attendance page to employee detail views"
Write-Host "- Updated expected departure time to 19:00 (7:00 PM)"
Write-Host "- Improved attendance data visualization with charts"
Write-Host "- Enhanced employee attendance monitoring capabilities"