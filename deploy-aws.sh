#!/bin/bash
# AWS EC2 Deployment Script for HRM SAAS
# This script automates the entire deployment process

set -e  # Exit on error

echo "=========================================="
echo "HRM SAAS - AWS EC2 Deployment"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (sudo)${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Starting deployment...${NC}"

# Update system
echo -e "${YELLOW}→ Updating system packages...${NC}"
apt-get update -y
apt-get upgrade -y

# Install Python and pip
echo -e "${YELLOW}→ Installing Python 3 and pip...${NC}"
apt-get install -y python3 python3-pip python3-venv

# Install PostgreSQL
echo -e "${YELLOW}→ Installing PostgreSQL...${NC}"
apt-get install -y postgresql postgresql-contrib

# Install dependencies
echo -e "${YELLOW}→ Installing system dependencies...${NC}"
apt-get install -y python3-dev libpq-dev build-essential

# Install Nginx
echo -e "${YELLOW}→ Installing Nginx...${NC}"
apt-get install -y nginx

# Create app directory
APP_DIR="/opt/hrm_saas"
echo -e "${YELLOW}→ Creating app directory: $APP_DIR${NC}"
mkdir -p $APP_DIR
cd $APP_DIR

# Setup virtual environment
echo -e "${YELLOW}→ Creating virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}→ Upgrading pip...${NC}"
pip install --upgrade pip

# Copy your application files here
echo -e "${YELLOW}→ NOTE: Copy your application files to $APP_DIR${NC}"
echo -e "${YELLOW}→ Run: scp -r -i your-key.pem ./* ec2-user@your-ec2-ip:$APP_DIR${NC}"

# Install Python dependencies
if [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}→ Installing Python dependencies...${NC}"
    pip install -r requirements.txt
    pip install gunicorn
else
    echo -e "${RED}ERROR: requirements.txt not found!${NC}"
    echo -e "${YELLOW}→ Please copy your application files first${NC}"
    exit 1
fi

# Setup database
echo -e "${YELLOW}→ Setting up PostgreSQL database...${NC}"
sudo -u postgres psql <<EOF
CREATE DATABASE hrm_saas;
CREATE USER hrm_saas WITH PASSWORD 'hrm_saas_password';
GRANT ALL PRIVILEGES ON DATABASE hrm_saas TO hrm_saas;
\q
EOF

# Create .env file
echo -e "${YELLOW}→ Creating .env file...${NC}"
cat > .env <<EOF
DJANGO_SECRET_KEY=$(openssl rand -base64 50)
DEBUG=False
ALLOWED_HOSTS=your-ec2-public-ip, your-domain.com

DB_NAME=hrm_saas
DB_USER=hrm_saas
DB_PASSWORD=hrm_saas_password
DB_HOST=localhost
DB_PORT=5432

CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com
CORS_ALLOW_ALL_ORIGINS=False

PUBLIC_SIGNUP_ENABLED=False

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=noreply@hrmsaas.com
FRONTEND_URL=https://your-frontend-domain.com
EOF

# Run migrations
echo -e "${YELLOW}→ Running database migrations...${NC}"
python manage.py migrate_schemas --shared
python manage.py migrate_schemas

# Collect static files
echo -e "${YELLOW}→ Collecting static files...${NC}"
python manage.py collectstatic --noinput

# Create superuser (optional - uncomment if needed)
# echo -e "${YELLOW}→ Creating superuser...${NC}"
# echo "from accounts.models import User; User.objects.create_superuser('admin@hrmsaas.com', 'Admin123!')" | python manage.py shell

# Setup Gunicorn systemd service
echo -e "${YELLOW}→ Setting up Gunicorn service...${NC}"
cat > /etc/systemd/system/hrm_saas.service <<EOF
[Unit]
Description=HRM SAAS Django Application
After=network.target

[Service]
User=root
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:$APP_DIR/hrm_saas.sock \
          config.wsgi:application

[Install]
WantedBy=multi-user.target
EOF

# Start and enable Gunicorn
systemctl start hrm_saas
systemctl enable hrm_saas

# Setup Nginx
echo -e "${YELLOW}→ Configuring Nginx...${NC}"
cat > /etc/nginx/sites-available/hrm_saas <<EOF
server {
    listen 80;
    server_name your-ec2-public-ip your-domain.com;

    location / {
        proxy_pass http://unix:$APP_DIR/hrm_saas.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static/ {
        alias $APP_DIR/staticfiles/;
    }

    location /media/ {
        alias $APP_DIR/media/;
    }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/hrm_saas /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test and restart Nginx
nginx -t
systemctl restart nginx

# Configure firewall
echo -e "${YELLOW}→ Configuring firewall...${NC}"
ufw allow 'Nginx Full'
ufw allow OpenSSH
ufw --force enable

echo -e "${GREEN}=========================================="
echo "✓ Deployment Complete!"
echo "==========================================${NC}"
echo ""
echo -e "${YELLOW}IMPORTANT: Update these values in $APP_DIR/.env:${NC}"
echo "  - ALLOWED_HOSTS (add your EC2 IP or domain)"
echo "  - CORS_ALLOWED_ORIGINS (add your frontend URL)"
echo "  - FRONTEND_URL (add your frontend URL)"
echo ""
echo -e "${YELLOW}Then restart services:${NC}"
echo "  sudo systemctl restart hrm_saas"
echo "  sudo systemctl restart nginx"
echo ""
echo -e "${GREEN}Your app should be accessible at:${NC}"
echo "  http://your-ec2-public-ip"
echo ""
echo -e "${YELLOW}To check logs:${NC}"
echo "  sudo journalctl -u hrm_saas -f"
echo "  sudo tail -f /var/log/nginx/error.log"
echo ""
