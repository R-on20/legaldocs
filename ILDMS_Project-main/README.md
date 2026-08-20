# 📚 ILDMS - Intelligent Legal Document Management System

[![Django](https://img.shields.io/badge/Django-5.1.5-092E20?style=for-the-badge&logo=django&logoColor=white)](https://djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

A comprehensive, secure, and intelligent document management system designed for legal firms, libraries, and organizations that need advanced document processing, AI-powered search, and robust security features.

## 🌟 Key Features

### 📁 **Document Management**
- **Multi-format Support**: Upload and manage Word documents (DOCX), PDFs, images, and media files
- **Real-time Document Editing**: Advanced CKEditor integration with collaborative features
- **Document Conversion**: Automatic conversion between formats (DOCX to PDF, etc.)
- **Version Control**: Track document changes and maintain version history
- **Document Preview**: In-browser preview for DOCX and PDF files

### 🤖 **AI-Powered Search**
- **Intelligent Search**: OpenAI GPT-powered semantic search capabilities
- **Natural Language Queries**: Search using natural language descriptions
- **Content Analysis**: AI-driven document categorization and tagging
- **Fallback Search**: Traditional keyword search when AI is unavailable
- **Search Analytics**: Track and analyze search patterns

### 🔐 **Enterprise-Grade Security**
- **File Upload Validation**: Multi-layer validation (extension, MIME type, content analysis)
- **XSS Prevention**: HTML sanitization and content security policies
- **SQL Injection Protection**: Parameterized queries throughout the application
- **Security Headers**: Comprehensive browser security with CSRF protection
- **Audit Logging**: Complete audit trail for all user actions and security events
- **Role-Based Access Control**: Granular permissions system

### 👥 **User Management**
- **Multi-Role Support**: Lawyers, Paralegals, Clients, and Administrators
- **Authentication**: Secure login with session management
- **User Profiles**: Professional profiles with specializations and contact information
- **Permission System**: Fine-grained access control to documents and features

### 📊 **Analytics & Reporting**
- **Document Analytics**: Track document usage, downloads, and access patterns
- **User Activity Monitoring**: Monitor user engagement and system usage
- **Search Analytics**: Analyze search queries and results effectiveness
- **Custom Reports**: Generate detailed reports on system usage

### ⚡ **Real-time Features**
- **Live Notifications**: Real-time updates using Django Channels and WebSockets
- **Collaborative Editing**: Multiple users can work on documents simultaneously
- **Background Processing**: Asynchronous tasks using Celery for heavy operations

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- PostgreSQL 12+
- Redis (for real-time features and caching)
- Node.js (for frontend dependencies)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/R-on20/legaldocs.git
   cd ILDMS_Project/ILDMS
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Node.js dependencies**
   ```bash
   npm install
   ```

5. **Set up PostgreSQL database**
   ```sql
   CREATE DATABASE ilms_db;
   CREATE USER ilms_user WITH PASSWORD 'ilms123';
   GRANT ALL PRIVILEGES ON DATABASE ilms_db TO ilms_user;
   ```

6. **Configure environment variables**
   Create a `.env` file in the project root:
   ```env
   DEBUG=True
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=postgresql://ilms_user:ilms123@localhost/ilms_db
   OPENAI_API_KEY=your-openai-api-key-here
   AI_SEARCH_ENABLED=True
   REDIS_URL=redis://localhost:6379
   ```

7. **Run database migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

8. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

9. **Start the development server**
   ```bash
   python manage.py runserver
   ```

10. **Start Redis and Celery** (in separate terminals)
    ```bash
    # Terminal 1: Start Redis
    redis-server
    
    # Terminal 2: Start Celery worker
    celery -A ILDMS worker --loglevel=info
    ```

Visit `http://localhost:8000` to access the application.

## 🔧 Configuration

### OpenAI Integration

To enable AI-powered search features:

1. Get an OpenAI API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Add it to your `.env` file:
   ```env
   OPENAI_API_KEY=sk-your-actual-key-here
   OPENAI_MODEL=gpt-3.5-turbo
   AI_SEARCH_ENABLED=True
   ```

### Security Configuration

For production deployment, ensure:

```python
# settings.py
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### Database Configuration

The system supports PostgreSQL with full-text search capabilities:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ilms_db',
        'USER': 'ilms_user',
        'PASSWORD': 'ilms123',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## 🧪 Testing

### Run Security Tests
```bash
python simple_security_test.py
python test_comprehensive_security.py
```

### Test AI Search Functionality
```bash
python manage.py test_ai_search --query "Show me contracts uploaded last month"
python manage.py test_ai_search --run-samples
```

### Run Django Tests
```bash
python manage.py test
```

## 📁 Project Structure

```
ILDMS/
├── ILDMS/                      # Main Django project
│   ├── settings.py             # Project settings
│   ├── urls.py                 # URL configuration
│   └── wsgi.py                 # WSGI configuration
├── accounts/                   # User authentication app
│   ├── models.py               # User models
│   ├── views.py                # Authentication views
│   ├── middleware.py           # Security middleware
│   └── templates/              # Auth templates
├── documents/                  # Document management app
│   ├── models.py               # Document models
│   ├── views.py                # Document views
│   ├── ai_search.py           # AI search functionality
│   ├── validators.py          # File validation
│   ├── security_utils.py      # Security utilities
│   └── templates/             # Document templates
├── main/                      # Main application
│   ├── models.py              # Core models
│   └── views.py               # Main views
├── analytics/                 # Analytics and reporting
│   ├── models.py              # Analytics models
│   └── management/            # Analytics commands
├── static/                    # Static files (CSS, JS, images)
├── templates/                 # Global templates
├── media/                     # User uploaded files
├── requirements.txt           # Python dependencies
└── manage.py                  # Django management script
```

## 🔐 Security Features

ILDMS implements enterprise-grade security measures:

### File Upload Security
- **Extension Validation**: Only allowed file types
- **MIME Type Checking**: Validates actual file content
- **Content Analysis**: Scans for malicious content
- **Size Limitations**: Prevents oversized uploads
- **Sandboxed Processing**: Isolated file processing

### Input Validation
- **HTML Sanitization**: Prevents XSS attacks
- **SQL Injection Prevention**: Parameterized queries
- **CSRF Protection**: Cross-site request forgery protection
- **Input Length Limits**: Prevents buffer overflow attacks

### Security Headers
- **Content Security Policy (CSP)**
- **X-Frame-Options**: Clickjacking protection
- **X-Content-Type-Options**: MIME sniffing protection
- **HTTP Strict Transport Security (HSTS)**

### Audit Logging
- All user actions are logged
- Security events are monitored
- Failed authentication attempts tracked
- Document access history maintained

## 🌐 API Documentation

The system provides RESTful APIs for integration:

### Authentication
```bash
POST /api/auth/login/
POST /api/auth/logout/
POST /api/auth/register/
```

### Documents
```bash
GET /api/documents/              # List documents
POST /api/documents/             # Upload document
GET /api/documents/{id}/         # Get specific document
PUT /api/documents/{id}/         # Update document
DELETE /api/documents/{id}/      # Delete document
```

### Search
```bash
POST /api/search/                # Search documents
POST /api/search/ai/             # AI-powered search
```

## 📚 Documentation

### Additional Documentation Files

- [`AI_SEARCH_SETUP.md`](ILDMS/AI_SEARCH_SETUP.md) - Detailed AI search configuration
- [`HOW_TO_TEST_AI_SEARCH.md`](ILDMS/HOW_TO_TEST_AI_SEARCH.md) - AI search testing guide
- [`SECURITY_CHECKLIST.md`](ILDMS/SECURITY_CHECKLIST.md) - Security deployment checklist
- [`SECURITY_IMPLEMENTATION_COMPLETE.md`](ILDMS/SECURITY_IMPLEMENTATION_COMPLETE.md) - Security features overview
- [`SEARCH_UI_IMPROVEMENTS.md`](ILDMS/SEARCH_UI_IMPROVEMENTS.md) - Search interface enhancements

### Entity Relationship Diagrams

- [`ILDMS_Final_ERD.puml`](ILDMS/ILDMS_Final_ERD.puml) - Complete database schema
- [`ILDMS_Compact_ERD.puml`](ILDMS/ILDMS_Compact_ERD.puml) - Simplified ERD

## 🚀 Deployment

### Production Checklist

1. **Security Settings**
   - [ ] Set `DEBUG = False`
   - [ ] Configure `ALLOWED_HOSTS`
   - [ ] Enable HTTPS with SSL certificates
   - [ ] Set secure cookie flags
   - [ ] Configure security headers

2. **Database**
   - [ ] Use production PostgreSQL server
   - [ ] Configure database backups
   - [ ] Optimize database settings

3. **Static Files**
   - [ ] Run `python manage.py collectstatic`
   - [ ] Configure web server for static files
   - [ ] Enable GZIP compression

4. **Monitoring**
   - [ ] Set up logging
   - [ ] Configure error tracking
   - [ ] Monitor performance

### Docker Deployment

```dockerfile
# Example Dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "ILDMS.wsgi:application"]
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


## 🏆 Acknowledgments

- Django framework for the robust web development foundation
- OpenAI for AI-powered search capabilities
- PostgreSQL for reliable database functionality
- The open-source community for various libraries and tools



*Last updated: 2026*
