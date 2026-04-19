# HRM SaaS

Multi-tenant HR Management System with schema-based tenant isolation.

## Quick Deploy to AWS (Recommended)

**Easiest way to deploy - No Docker needed!**

📖 **Step-by-step guide:** [DEPLOY_AWS.md](DEPLOY_AWS.md)

**3 Steps:**
1. Launch EC2 instance on AWS
2. Upload project files
3. Run deployment script

**Total time:** 20 minutes | **Cost:** $0-15/month

## Quick Start (Local Development)

```bash
# Copy environment file
cp .env.example .env

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate_schemas --shared
python manage.py migrate_schemas

# Create superuser
python manage.py createsuperuser

# Run server
python manage.py runserver
```

Access: http://localhost:8000/api/v1/

## Documentation

- **[DEPLOY_AWS.md](DEPLOY_AWS.md)** - Deploy to AWS EC2 (beginner friendly!)
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Docker deployment guide
- **[.env.example](.env.example)** - Environment variables template

## Tech Stack

- Django 5.1.6
- Django REST Framework 3.15.2
- django-tenants 3.10.0
- PostgreSQL 15
- Gunicorn (production server)

## Project Structure

```
hrm_saas/
├── config/          # Main project configuration
├── tenants/         # Public schema (Organization/Domain models)
├── accounts/        # User management (tenant-isolated)
├── attendance/      # Attendance tracking (tenant-isolated)
├── invitations/     # Email invitations (tenant-isolated)
├── audit_logs/      # Audit logging (tenant-isolated)
└── deploy-aws.sh    # AWS deployment script
```

## Key Features

- **Multi-Tenancy**: Schema-based tenant isolation
- **Authentication**: JWT-based auth
- **User Management**: Role-based access control
- **Attendance**: Check-in/check-out with location support
- **Invitations**: Email-based user invitations
- **Audit Logs**: Comprehensive audit trail

## API Testing

A complete Postman collection is included: `HRM_SAAS_Complete_API.postman_collection.json`

Import this into Postman to test all endpoints. It includes:
- All API endpoints organized by module
- Pre-configured environment variables
- Authentication setup
- Test scripts for automatic token management
- Complete request/response examples

## Support

For deployment help, see [DEPLOY_AWS.md](DEPLOY_AWS.md)

## License

Proprietary software. All rights reserved.
