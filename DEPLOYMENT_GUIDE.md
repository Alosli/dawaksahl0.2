# DawakSahl Backend Deployment Guide

This guide provides step-by-step instructions for deploying the DawakSahl backend API to various platforms.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Local Development](#local-development)
4. [Deploy to Render](#deploy-to-render)
5. [Deploy with Docker](#deploy-with-docker)
6. [GitHub Actions CI/CD](#github-actions-cicd)
7. [Database Setup](#database-setup)
8. [Environment Variables](#environment-variables)
9. [Monitoring and Logging](#monitoring-and-logging)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

- Python 3.11+
- Git
- PostgreSQL (for production)
- SendGrid account
- Render account (for cloud deployment)

## Environment Setup

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd dawaksahl-backend
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Variables

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your configuration (see [Environment Variables](#environment-variables) section).

## Local Development

### 1. Initialize Database

```bash
export FLASK_APP=src/main.py
flask db upgrade
```

### 2. Run the Application

```bash
python src/main.py
```

The API will be available at `http://localhost:5000`

### 3. Test the API

```bash
curl http://localhost:5000/health
```

Expected response:
```json
{
  "status": "healthy",
  "message": "DawakSahl API is running",
  "version": "1.0.0"
}
```

## Deploy to Render

### Method 1: Using render.yaml (Recommended)

1. **Fork the repository** to your GitHub account

2. **Create a new Web Service** on Render:
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Render will automatically detect the `render.yaml` file

3. **Configure Environment Variables**:
   - The `render.yaml` file includes most configurations
   - Add sensitive variables manually in Render dashboard:
     - `SENDGRID_API_KEY`
     - Any other sensitive keys

4. **Deploy**:
   - Click "Create Web Service"
   - Render will automatically build and deploy your application

### Method 2: Manual Configuration

1. **Create Web Service**:
   - Environment: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn --bind 0.0.0.0:$PORT --workers 4 src.main:app`

2. **Add Environment Variables** (see [Environment Variables](#environment-variables))

3. **Create PostgreSQL Database**:
   - Go to Render Dashboard
   - Click "New" → "PostgreSQL"
   - Copy the database URL to your web service environment variables

4. **Deploy**:
   - Push to your main branch
   - Render will automatically deploy

### Post-Deployment Steps

1. **Run Database Migrations**:
   ```bash
   # This is automatically done in the start command
   flask db upgrade
   ```

2. **Verify Deployment**:
   ```bash
   curl https://your-app.onrender.com/health
   ```

## Deploy with Docker

### 1. Build Docker Image

```bash
docker build -t dawaksahl-backend .
```

### 2. Run Container Locally

```bash
docker run -p 5000:5000 --env-file .env dawaksahl-backend
```

### 3. Deploy to Container Platform

#### Docker Hub
```bash
# Tag and push to Docker Hub
docker tag dawaksahl-backend your-username/dawaksahl-backend
docker push your-username/dawaksahl-backend
```

#### Deploy to Cloud Run (Google Cloud)
```bash
# Build and deploy to Cloud Run
gcloud run deploy dawaksahl-backend \
  --image gcr.io/your-project/dawaksahl-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## GitHub Actions CI/CD

The repository includes a GitHub Actions workflow (`.github/workflows/deploy.yml`) that:

1. **Runs tests** on every push/PR
2. **Performs security checks**
3. **Automatically deploys** to Render on main branch

### Setup GitHub Actions

1. **Add Secrets** to your GitHub repository:
   - Go to Settings → Secrets and variables → Actions
   - Add the following secrets:
     - `RENDER_SERVICE_ID`: Your Render service ID
     - `RENDER_API_KEY`: Your Render API key

2. **Push to main branch** to trigger deployment

### Workflow Features

- **Testing**: Runs pytest with coverage
- **Linting**: Black, isort, flake8
- **Security**: Bandit, Safety checks
- **Deployment**: Automatic deployment to Render
- **Notifications**: Deployment status notifications

## Database Setup

### Development (SQLite)

SQLite is used by default for development. No additional setup required.

### Production (PostgreSQL)

#### Render PostgreSQL

1. **Create Database**:
   - Go to Render Dashboard
   - Click "New" → "PostgreSQL"
   - Choose your plan
   - Note the connection details

2. **Configure Connection**:
   - Copy the "External Database URL"
   - Add it to your web service as `DATABASE_URL`

#### External PostgreSQL

```bash
# Example connection string
DATABASE_URL=postgresql://username:password@hostname:5432/database_name
```

### Database Migrations

```bash
# Create new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Downgrade (if needed)
flask db downgrade
```

## Environment Variables

### Required Variables

```env
# Flask Configuration
SECRET_KEY=your-super-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# Database
DATABASE_URL=postgresql://username:password@hostname:5432/database_name

# SendGrid (Email)
SENDGRID_API_KEY=your-sendgrid-api-key
SENDGRID_FROM_EMAIL=noreply@dawaksahl.com
SENDGRID_FROM_NAME=DawakSahl

# Application
FRONTEND_URL=https://your-frontend-domain.com
CORS_ORIGINS=https://your-frontend-domain.com,https://www.your-frontend-domain.com
```

### Optional Variables

```env
# Environment
FLASK_ENV=production

# File Uploads
UPLOAD_FOLDER=/opt/render/project/src/uploads
MAX_CONTENT_LENGTH=16777216

# Logging
LOG_LEVEL=WARNING

# API Configuration
API_PREFIX=/api/v1

# Security
SESSION_COOKIE_SECURE=true

# Rate Limiting (Redis URL for production)
REDIS_URL=redis://localhost:6379/0
```

### Generating Secret Keys

```python
# Generate secure secret keys
import secrets
print(secrets.token_urlsafe(32))
```

## Monitoring and Logging

### Application Logs

Logs are written to:
- **Development**: Console output
- **Production**: `logs/app.log` file

### Health Monitoring

- **Health endpoint**: `/health`
- **API info endpoint**: `/api/v1/`

### Render Monitoring

Render provides built-in monitoring:
- **Metrics**: CPU, Memory, Response time
- **Logs**: Real-time log streaming
- **Alerts**: Configure alerts for downtime

### External Monitoring (Optional)

Consider integrating with:
- **Sentry**: Error tracking
- **New Relic**: Application performance monitoring
- **DataDog**: Infrastructure monitoring

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors

```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solutions**:
- Verify `DATABASE_URL` is correct
- Check database server is running
- Ensure firewall allows connections

#### 2. Migration Errors

```
alembic.util.exc.CommandError: Can't locate revision identified by 'xyz'
```

**Solutions**:
- Reset migrations: `rm -rf migrations/` and `flask db init`
- Check for conflicting migrations
- Manually resolve migration conflicts

#### 3. SendGrid Email Errors

```
HTTP Error 401: Unauthorized
```

**Solutions**:
- Verify `SENDGRID_API_KEY` is correct
- Check SendGrid account status
- Verify sender email is verified in SendGrid

#### 4. CORS Errors

```
Access to fetch at 'api-url' from origin 'frontend-url' has been blocked by CORS policy
```

**Solutions**:
- Add frontend URL to `CORS_ORIGINS`
- Check CORS configuration in `src/app.py`
- Verify environment variables are loaded

#### 5. File Upload Errors

```
413 Request Entity Too Large
```

**Solutions**:
- Check `MAX_CONTENT_LENGTH` setting
- Verify file size limits
- Check server/proxy upload limits

### Debug Mode

Enable debug mode for development:

```env
FLASK_ENV=development
```

**Warning**: Never enable debug mode in production!

### Log Analysis

```bash
# View recent logs
tail -f logs/app.log

# Search for errors
grep "ERROR" logs/app.log

# Monitor in real-time (Render)
render logs -f your-service-name
```

### Performance Issues

1. **Database Performance**:
   - Add database indexes
   - Optimize queries
   - Use connection pooling

2. **Memory Issues**:
   - Monitor memory usage
   - Optimize image processing
   - Use pagination for large datasets

3. **Response Time**:
   - Enable caching
   - Optimize database queries
   - Use CDN for static files

## Security Checklist

- [ ] Use HTTPS in production
- [ ] Set secure environment variables
- [ ] Enable rate limiting
- [ ] Validate all inputs
- [ ] Use secure headers
- [ ] Regular security updates
- [ ] Monitor for vulnerabilities

## Backup and Recovery

### Database Backups

```bash
# Create backup
pg_dump $DATABASE_URL > backup.sql

# Restore backup
psql $DATABASE_URL < backup.sql
```

### File Backups

- Upload folder: `/uploads/`
- Configuration files: `.env`, `render.yaml`
- Application code: Git repository

## Scaling

### Horizontal Scaling

- Use multiple Render instances
- Implement load balancing
- Use Redis for session storage

### Vertical Scaling

- Upgrade Render plan
- Increase database resources
- Optimize application performance

## Support

For deployment support:
- **Documentation**: This guide
- **Issues**: GitHub repository issues
- **Email**: support@dawaksahl.com

---

*Last updated: January 2024*

