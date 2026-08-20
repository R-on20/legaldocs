# Contributing to ILDMS

Thank you for your interest in contributing to the Intelligent Library Document Management System (ILDMS)! We welcome contributions from the community.

## 🚀 Getting Started

1. Fork the repository
2. Clone your fork locally
3. Set up the development environment following the [README.md](README.md) instructions
4. Create a new branch for your feature or bug fix

## 🤝 How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/Shedie254/ILDMS_Project/issues)
2. If not, create a new issue with:
   - Clear description of the bug
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (Python version, Django version, etc.)

### Suggesting Features

1. Check existing [Issues](https://github.com/Shedie254/ILDMS_Project/issues) for similar suggestions
2. Create a new issue with:
   - Clear description of the feature
   - Use cases and benefits
   - Possible implementation approach

### Code Contributions

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow the coding standards below
   - Add tests for new functionality
   - Update documentation if needed

3. **Test your changes**
   ```bash
   python manage.py test
   python simple_security_test.py
   ```

4. **Commit your changes**
   ```bash
   git commit -m "Add: brief description of your changes"
   ```

5. **Push and create a Pull Request**

## 📝 Coding Standards

### Python Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use meaningful variable and function names
- Add docstrings for all functions and classes
- Keep functions small and focused
- Use type hints where appropriate

```python
def process_document(document: Document, user: User) -> bool:
    """
    Process a document for a specific user.
    
    Args:
        document: The document to process
        user: The user requesting processing
        
    Returns:
        bool: True if processing successful, False otherwise
    """
    # Implementation here
    pass
```

### Django Best Practices

- Use Django's built-in security features
- Follow Django's model, view, template pattern
- Use Django forms for data validation
- Implement proper error handling
- Use Django's translation framework for internationalization

### Security Guidelines

- Never commit sensitive information (API keys, passwords, etc.)
- Validate all user inputs
- Use Django's CSRF protection
- Implement proper authentication and authorization
- Follow OWASP security guidelines

### Frontend Standards

- Use semantic HTML
- Follow accessibility guidelines (WCAG 2.1)
- Ensure responsive design
- Optimize for performance
- Use consistent CSS naming conventions

## 🧪 Testing

### Running Tests

```bash
# Run Django tests
python manage.py test

# Run security tests
python simple_security_test.py
python test_comprehensive_security.py

# Test AI search functionality
python manage.py test_ai_search --run-samples
```

### Writing Tests

- Write tests for all new functionality
- Include edge cases and error conditions
- Use Django's testing framework
- Mock external dependencies
- Aim for high test coverage

Example test:

```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from documents.models import Document

User = get_user_model()

class DocumentTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_document_creation(self):
        """Test document creation with valid data."""
        document = Document.objects.create(
            title='Test Document',
            content='Test content',
            uploaded_by=self.user
        )
        self.assertEqual(document.title, 'Test Document')
        self.assertEqual(document.uploaded_by, self.user)
```

## 📚 Documentation

- Update README.md if your changes affect setup or usage
- Add docstrings to new functions and classes
- Update API documentation for new endpoints
- Include code examples in documentation

## 🔄 Pull Request Process

1. **Ensure your PR**:
   - Has a clear description of changes
   - References related issues
   - Includes tests for new functionality
   - Passes all existing tests
   - Follows the coding standards

2. **PR Description Template**:
   ```markdown
   ## Description
   Brief description of changes

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Documentation update
   - [ ] Refactoring

   ## Testing
   - [ ] Tests pass locally
   - [ ] Added tests for new functionality

   ## Related Issues
   Fixes #issue_number
   ```

3. **Review Process**:
   - PRs require at least one approval
   - Address all review comments
   - Ensure CI/CD checks pass

## 🐛 Security Issues

If you discover a security vulnerability, please:

1. **DO NOT** create a public issue
2. Email the maintainers directly
3. Provide detailed information about the vulnerability
4. Allow time for the issue to be addressed before public disclosure

## 📞 Getting Help

- Check existing [Issues](https://github.com/Shedie254/ILDMS_Project/issues)
- Read the [README.md](README.md) documentation
- Contact the maintainers

## 📋 Development Setup Checklist

- [ ] Python 3.8+ installed
- [ ] PostgreSQL 12+ installed and configured
- [ ] Redis installed and running
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Database migrations applied
- [ ] Superuser created
- [ ] Tests passing
- [ ] Development server running

Thank you for contributing to ILDMS! 🎉