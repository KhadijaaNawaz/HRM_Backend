#!/bin/bash
# Quick setup script for HRM SAAS development environment

echo "HRM SAAS - Development Setup"
echo "=============================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "✓ Created .env file"
    echo "  Please edit .env with your configuration"
else
    echo "✓ .env file already exists"
fi

# Generate secret key if using default
if grep -q "django-insecure-change-this-in-production" .env; then
    echo ""
    echo "⚠ WARNING: Using default secret key!"
    echo "Generate a secure key with: python scripts/generate_secret_key.py"
fi

# Check if docker-compose is available
if command -v docker-compose &> /dev/null; then
    echo ""
    echo "✓ Docker Compose is available"
    echo ""
    echo "To start the development environment:"
    echo "  docker-compose up -d"
    echo ""
    echo "To run migrations:"
    echo "  docker-compose exec web python manage.py migrate_schemas --shared"
    echo "  docker-compose exec web python manage.py migrate_schemas"
    echo ""
    echo "To create a superuser:"
    echo "  docker-compose exec web python manage.py createsuperuser"
elif command -v docker &> /dev/null; then
    echo ""
    echo "✓ Docker is available (using docker compose plugin)"
    echo ""
    echo "To start the development environment:"
    echo "  docker compose up -d"
else
    echo ""
    echo "⚠ Docker not found. Please install Docker for easy setup."
    echo ""
    echo "Manual setup:"
    echo "  1. Create virtual environment: python -m venv venv"
    echo "  2. Activate: source venv/bin/activate"
    echo "  3. Install dependencies: pip install -r requirements.txt"
    echo "  4. Setup PostgreSQL database"
    echo "  5. Run migrations: python manage.py migrate_schemas --shared"
    echo "  6. Run migrations: python manage.py migrate_schemas"
    echo "  7. Create superuser: python manage.py createsuperuser"
    echo "  8. Run server: python manage.py runserver"
fi

echo ""
echo "For detailed deployment instructions, see DEPLOYMENT.md"
