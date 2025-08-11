#!/bin/bash

# Production Deployment Script for The Commons
set -e

echo "🚀 Starting production deployment..."

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo "❌ Error: .env.production file not found!"
    echo "Please create .env.production with the following variables:"
    echo "SECRET_KEY=your-secret-key"
    echo "ALGORITHM=HS256"
    echo "ACCESS_TOKEN_EXPIRE_MINUTES=30"
    exit 1
fi

# Load production environment variables
export $(cat .env.production | grep -v '^#' | xargs)

# Validate required environment variables
if [ -z "$SECRET_KEY" ]; then
    echo "❌ Error: SECRET_KEY not set in .env.production"
    exit 1
fi

echo "✅ Environment variables loaded"

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker compose -f docker-compose.prod.yml down

# Build production image
echo "🔨 Building production image..."
docker build -f Dockerfile.prod -t the-commons-backend:prod .

# Start production services
echo "🚀 Starting production services..."
docker compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Check service health
echo "🏥 Checking service health..."
if docker compose -f docker-compose.prod.yml ps | grep -q "unhealthy"; then
    echo "❌ Some services are unhealthy. Check logs:"
    docker compose -f docker-compose.prod.yml logs
    exit 1
fi

echo "✅ All services are healthy!"

# Run database migrations
echo "🗄️ Running database migrations..."
docker compose -f docker-compose.prod.yml exec -T web alembic upgrade head

# Test the API
echo "🧪 Testing API health..."
if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "✅ API is responding correctly"
else
    echo "❌ API health check failed"
    exit 1
fi

echo "🎉 Production deployment completed successfully!"
echo "📊 API is available at: http://localhost:8000"
echo "📚 API documentation at: http://localhost:8000/docs"
