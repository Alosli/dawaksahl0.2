# DawakSahl Backend API

A comprehensive Flask-based backend API for the DawakSahl pharmacy platform with full multilingual support (Arabic/English).

## Features

- 🔐 **Authentication & Authorization**: JWT-based auth with role-based access control
- 🌐 **Multilingual Support**: Full Arabic and English support throughout the API
- 📧 **Email System**: SendGrid integration for verification and notifications
- 🏥 **Pharmacy Management**: Complete pharmacy profiles and inventory management
- 💊 **Medication Database**: Comprehensive medication catalog with categories
- 📋 **Prescription System**: Upload, verify, and manage prescriptions
- 🛒 **Order Management**: Full order lifecycle with real-time tracking
- 💬 **Chat System**: Real-time messaging between users and pharmacies
- 🔔 **Notifications**: Multi-channel notification system
- ⭐ **Reviews & Ratings**: User feedback system for pharmacies and medications
- 🔍 **Advanced Search**: Powerful search and filtering capabilities
- 📱 **File Uploads**: Secure file handling for prescriptions and documents
- 🛡️ **Security**: Comprehensive security measures and input validation

## Tech Stack

- **Framework**: Flask 3.1.1
- **Database**: PostgreSQL (SQLite for development)
- **Authentication**: Flask-JWT-Extended
- **Email**: SendGrid
- **File Storage**: Local filesystem (configurable for cloud storage)
- **Validation**: Marshmallow
- **Security**: bcrypt, rate limiting, CORS
- **Deployment**: Docker, Render, GitHub Actions

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL (for production)
- SendGrid account
- Git

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd dawaksahl-backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   flask db upgrade
   ```

6. **Run the application**
   ```bash
   python src/main.py
   ```

The API will be available at `http://localhost:5000`

## Environment Variables

Create a `.env` file with the following variables:

```env
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-super-secret-key
JWT_SECRET_KEY=your-jwt-secret-key

# Database
DATABASE_URL=postgresql://username:password@localhost:5432/dawaksahl

# SendGrid
SENDGRID_API_KEY=your-sendgrid-api-key
SENDGRID_FROM_EMAIL=noreply@dawaksahl.com
SENDGRID_FROM_NAME=DawakSahl

# Application
FRONTEND_URL=http://localhost:3000
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# File Uploads
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216

# Security
SESSION_COOKIE_SECURE=false
```

## API Documentation

### Base URL
- Development: `http://localhost:5000/api/v1`
- Production: `https://your-app.onrender.com/api/v1`

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | User registration |
| POST | `/auth/login` | User login |
| POST | `/auth/verify-email` | Email verification |
| POST | `/auth/forgot-password` | Request password reset |
| POST | `/auth/reset-password` | Reset password |
| POST | `/auth/refresh-token` | Refresh access token |
| POST | `/auth/logout` | User logout |
| POST | `/auth/change-password` | Change password |

### User Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users/profile` | Get user profile |
| PUT | `/users/profile` | Update user profile |
| POST | `/users/upload-avatar` | Upload user avatar |
| GET | `/users/addresses` | Get user addresses |
| POST | `/users/addresses` | Add new address |
| PUT | `/users/addresses/{id}` | Update address |
| DELETE | `/users/addresses/{id}` | Delete address |

### Medications

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/medications` | List medications |
| GET | `/medications/{id}` | Get medication details |
| GET | `/medications/categories` | Get categories |

### Pharmacies

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/pharmacies` | List pharmacies |
| GET | `/pharmacies/{id}` | Get pharmacy details |
| GET | `/pharmacies/{id}/inventory` | Get pharmacy inventory |

### Orders

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/orders` | List user orders |
| POST | `/orders` | Create new order |
| GET | `/orders/{id}` | Get order details |
| PUT | `/orders/{id}/status` | Update order status |

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/chat/conversations` | List conversations |
| POST | `/chat/conversations` | Start new conversation |
| GET | `/chat/conversations/{id}/messages` | Get messages |
| POST | `/chat/conversations/{id}/messages` | Send message |

## Deployment

### Deploy to Render

1. **Fork this repository** to your GitHub account

2. **Create a new Web Service** on Render:
   - Connect your GitHub repository
   - Use the following settings:
     - **Environment**: Python 3
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT src.main:app`

3. **Add environment variables** in Render dashboard:
   - `FLASK_ENV=production`
   - `SECRET_KEY` (generate a secure key)
   - `JWT_SECRET_KEY` (generate a secure key)
   - `DATABASE_URL` (from Render PostgreSQL service)
   - `SENDGRID_API_KEY`
   - `SENDGRID_FROM_EMAIL`
   - `FRONTEND_URL`
   - `CORS_ORIGINS`

4. **Create a PostgreSQL database** on Render and connect it

5. **Deploy** - Render will automatically deploy when you push to main branch

### Deploy with Docker

1. **Build the image**
   ```bash
   docker build -t dawaksahl-backend .
   ```

2. **Run the container**
   ```bash
   docker run -p 5000:5000 --env-file .env dawaksahl-backend
   ```

### GitHub Actions CI/CD

The repository includes a GitHub Actions workflow that:
- Runs tests on every push/PR
- Performs security checks
- Automatically deploys to Render on main branch

To set up:
1. Add `RENDER_SERVICE_ID` and `RENDER_API_KEY` to GitHub secrets
2. Push to main branch to trigger deployment

## Database Schema

The application uses the following main models:

- **User**: Patients, pharmacies, and doctors
- **Pharmacy**: Pharmacy profiles and information
- **Medication**: Medication catalog with categories
- **Prescription**: Uploaded prescriptions
- **Order**: Order management and tracking
- **Chat**: Messaging system
- **Notification**: Multi-channel notifications
- **Review**: User feedback and ratings

## Security Features

- JWT token authentication
- Password hashing with bcrypt
- Input validation and sanitization
- Rate limiting
- CORS configuration
- File upload security
- SQL injection prevention
- XSS protection
- Security headers

## Multilingual Support

The API supports both Arabic and English:
- All responses include both languages
- Email templates in both languages
- Error messages in both languages
- User preference-based language selection

## File Uploads

Supported file types:
- **Prescriptions**: PNG, JPG, JPEG, PDF
- **Avatars**: PNG, JPG, JPEG
- **Documents**: PDF, DOC, DOCX

Maximum file size: 16MB

## Testing

Run tests with:
```bash
pytest tests/ -v --cov=src
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support, email support@dawaksahl.com or create an issue in the repository.

## Changelog

### v1.0.0
- Initial release
- Complete API implementation
- Multilingual support
- SendGrid integration
- Deployment configuration

