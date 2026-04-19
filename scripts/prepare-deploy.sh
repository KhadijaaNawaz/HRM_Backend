#!/bin/bash
# Prepare files for AWS EC2 deployment

echo "Preparing files for AWS EC2 deployment..."

# Create a deployment package
echo "Creating deployment package..."

# Exclude unnecessary files
rsync -av \
  --exclude 'venv/' \
  --exclude '.git/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '.env' \
  --exclude 'db.sqlite3' \
  --exclude 'media/' \
  --exclude 'staticfiles/' \
  --exclude 'test/' \
  --exclude 'test_*.py' \
  --exclude 'docs/' \
  --exclude '*.md' \
  --exclude '.gitignore' \
  --exclude 'deploy-aws.sh' \
  --exclude 'scripts/' \
  . ../hrm_saas-deploy/

echo "✓ Deployment package created in ../hrm_saas-deploy/"
echo ""
echo "To upload to AWS EC2:"
echo "  scp -i your-key.pem -r ../hrm_saas-deploy/* ubuntu@YOUR-EC2-IP:/home/ubuntu/hrm_saas/"
