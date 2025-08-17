#!/bin/bash

# Variables
AWS_REGION="us-east-1"
VPC_ID="your-vpc-id"
SUBNET_ID="your-subnet-id"
KEY_NAME="your-key-name"
DB_INSTANCE_IDENTIFIER="fileboss-db"
DB_USER="fileboss"
DB_PASSWORD="your-db-password"
S3_BUCKET_NAME="your-fileboss-bucket-name"

# Create EC2 instance
aws ec2 run-instances \
    --region $AWS_REGION \
    --image-id ami-0c55b159cbfafe1f0 \
    --instance-type t3.medium \
    --key-name $KEY_NAME \
    --subnet-id $SUBNET_ID \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=fileboss-app}]'

# Create RDS instance
aws rds create-db-instance \
    --region $AWS_REGION \
    --db-instance-identifier $DB_INSTANCE_IDENTIFIER \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --master-username $DB_USER \
    --master-user-password $DB_PASSWORD \
    --allocated-storage 20 \
    --vpc-security-group-ids "your-security-group-id"

# Create S3 bucket
aws s3api create-bucket \
    --region $AWS_REGION \
    --bucket $S3_BUCKET_NAME \
    --create-bucket-configuration LocationConstraint=$AWS_REGION
