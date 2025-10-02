# PowerShell script to deploy the ERP system to Google Cloud Run and run migrations

# First run the regular deployment script
Write-Host "Running main deployment script..."
.\deploy_to_gcp.ps1

# Check if deployment was successful
if ($LASTEXITCODE -ne 0) {
    Write-Host "Deployment failed. Please check the logs." -ForegroundColor Red
    exit $LASTEXITCODE
}

# Get the Cloud SQL connection string from the environment
$PROJECT_ID = "erp-system-445701"
$REGION = "us-central1"
$CLOUD_SQL_INSTANCE = "erp-database"
$DB_USER = "erpuser"
$DB_PASS = "ERPuser2025!"
$DB_NAME = "erpsystem"

# Create the PostgreSQL connection string
$DB_URL = "postgresql://${DB_USER}:${DB_PASS}@localhost/${DB_NAME}"

Write-Host "Connecting to Cloud SQL instance to run migrations..."
Write-Host "This will create a Cloud SQL Auth proxy connection and run the attendance migrations"

# Run the Cloud SQL Auth proxy in the background
Write-Host "Starting Cloud SQL Auth proxy..."
$proxy_process = Start-Process -FilePath "cloud_sql_proxy" -ArgumentList "-instances=${PROJECT_ID}:${REGION}:${CLOUD_SQL_INSTANCE}=tcp:5432" -PassThru -NoNewWindow

# Wait for the proxy to start
Start-Sleep -Seconds 5

# Run the migration script
Write-Host "Running attendance migrations..."
python migrations/attendance_migration.py --db-url $DB_URL

# Check if migration was successful
if ($LASTEXITCODE -ne 0) {
    Write-Host "Migration failed. Please check the logs." -ForegroundColor Red
    # Stop the proxy
    Stop-Process -Id $proxy_process.Id
    exit $LASTEXITCODE
}

# Stop the proxy
Write-Host "Stopping Cloud SQL Auth proxy..."
Stop-Process -Id $proxy_process.Id

Write-Host "Deployment and migration completed successfully!" -ForegroundColor Green
Write-Host "Your application should be available at: https://erp-system-773057744195.us-central1.run.app"
