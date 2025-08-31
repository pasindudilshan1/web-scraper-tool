#!/bin/bash

# AWS Lambda Web Scraper Deployment Script
# This script packages and deploys the Lambda function

echo "🚀 Starting AWS Lambda Web Scraper Deployment..."

# Create deployment directory
mkdir -p deployment
cd deployment

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r ../requirements.txt

# Create deployment package
echo "📦 Creating deployment package..."
mkdir -p package
cd package

# Copy source code


cp -r ../venv/lib/python*/site-packages/* .

# Create deployment zip
echo "🗜️ Creating deployment zip..."
zip -r9 ../web-scraper-lambda.zip .

# Clean up
cd ..
rm -rf package venv

echo "✅ Deployment package created: web-scraper-lambda.zip"
echo "📋 Package size: $(du -h web-scraper-lambda.zip | cut -f1)"

# Instructions for deployment
echo ""
echo "🎯 To deploy to AWS Lambda:"
echo "1. Create a new Lambda function in AWS Console"
echo "2. Upload the web-scraper-lambda.zip file"
echo "3. Set handler to: lambda_function.lambda_handler"
echo "4. Set runtime to: Python 3.11"
echo "5. Set timeout to: 30 seconds"
echo "6. Set memory to: 512 MB"
echo "7. Create API Gateway trigger"
echo ""
echo "🔐 Required IAM permissions:"
echo "- lambda:CreateFunction"
echo "- lambda:UpdateFunctionCode"
echo "- lambda:AddPermission"
echo "- apigateway:*"
echo "- logs:CreateLogGroup"
echo "- logs:CreateLogStream"
echo "- logs:PutLogEvents"