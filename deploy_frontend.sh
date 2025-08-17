#!/bin/bash

# Variables
S3_BUCKET_NAME="your-fileboss-bucket-name"

# Install dependencies
npm install

# Build the frontend
npm run build

# Deploy to S3
aws s3 sync build/ s3://$S3_BUCKET_NAME
