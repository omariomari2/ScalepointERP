#!/bin/bash
# Script to build and deploy the ERP system to Google Cloud Run

# Set variables
PROJECT_ID="773057744195"  # Your GCP project ID from the URL
IMAGE_NAME="erp-system"
VERSION="v8"  # Incrementing from v7 based on your Docker Desktop screenshot
REGION="us-central1"  # Region from your existing deployment
SERVICE_NAME="erp-system"

# Build the Docker image
echo "Building Docker image: $IMAGE_NAME:$VERSION"
docker build -t $IMAGE_NAME:$VERSION .

# Tag the image for Google Container Registry
echo "Tagging image for Google Container Registry"
docker tag $IMAGE_NAME:$VERSION gcr.io/$PROJECT_ID/$IMAGE_NAME:$VERSION

# Push the image to Google Container Registry
echo "Pushing image to Google Container Registry"
docker push gcr.io/$PROJECT_ID/$IMAGE_NAME:$VERSION

# Deploy to Cloud Run
echo "Deploying to Cloud Run"
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$IMAGE_NAME:$VERSION \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --port 8080 \
  --set-env-vars="FLASK_CONFIG=production,SECRET_KEY=your-secret-key-here"

echo "Deployment complete! Your application should be available at:"
echo "https://$SERVICE_NAME-$PROJECT_ID.$REGION.run.app"
