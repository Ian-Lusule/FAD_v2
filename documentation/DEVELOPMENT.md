# Development Guide

## Table of Contents

1. [Development Setup](#development-setup)
2. [Project Structure](#project-structure)
3. [Code Style & Standards](#code-style--standards)
4. [Adding Features](#adding-features)
5. [Testing](#testing)
6. [Debugging](#debugging)
7. [Git Workflow](#git-workflow)
8. [Contributing](#contributing)

---

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- pip and venv
- Text editor/IDE (VS Code, PyCharm, etc.)

### Initial Setup

```bash
# 1. Clone repository
git clone <repository-url>
cd fraud-app-analyzer-flask

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# 4. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 5. Install development dependencies
pip install -r requirements-dev.txt  # If exists, otherwise:
pip install pytest pytest-cov flake8 black isort ipdb

# 6. Configure environment
cp .env.example .env
nano .env  # Update with development values

# 7. Run development server
python run.py
```

### Development Environment Variables

**.env** (development):
```bash
# Flask
SECRET_KEY=dev-secret-key-change-me
FLASK_ENV=development
DEBUG=True
PORT=5000
HOST=0.0.0.0

# Admin
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@localhost
ADMIN_PASSWORD=admin123

# Email (optional - use Mailtrap for testing)
MAIL_SERVER=smtp.mailtrap.io
MAIL_PORT=2525
MAIL_USERNAME=your-mailtrap-user
MAIL_PASSWORD=your-mailtrap-pass
```

### IDE Configuration

**VS Code** (`.vscode/settings.json`):
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.rulers": [88],
  "[python]": {
    "editor.tabSize": 4,
    "editor.insertSpaces": true
  }
}
```

**PyCharm**:
1. File → Settings → Project → Python Interpreter
2. Add Interpreter → Existing environment → `venv/bin/python`
3. Settings → Editor → Code Style → Python → Set line length to 88

---

## Project Structure

### Overview

```
fraud-app-analyzer-flask/
├── app.py                  # Application factory
├── run.py                  # Development server entry point
├── wsgi.py                 # Production WSGI entry point
├── config.py               # Configuration settings
├── requirements.txt        # Python dependencies
│
├── auth.py                 # Authentication & User model
├── main.py                 # Main blueprint (analysis routes)
├── admin.py                # Admin blueprint (dashboard, users, messages)
├── filters.py              # Jinja2 custom filters
├── file_store.py           # Data persistence layer
│
├── modules/                # Business logic modules
│   ├── __init__.py
│   ├── data_fetcher.py    # Google Play scraper wrapper
│   ├── sentiment_analyzer.py  # TextBlob sentiment analysis
│   ├── report_generator.py    # PDF generation with ReportLab
│   └── email_sender.py    # Email functionality
│
├── templates/              # Jinja2 templates
│   ├── base.html          # Base layout
│   ├── index.html         # Landing page
│   ├── error.html         # Error page
│   ├── auth/              # Authentication templates
│   ├── analysis/          # Analysis result templates
│   └── admin/             # Admin panel templates
│
├── static/                 # Static assets
│   ├── css/style.css      # Styles
│   └── js/main.js         # JavaScript
│
├── data/                   # Data storage (gitignored)
│   ├── users.json
│   ├── messages.json
│   ├── search_logs.csv
│   └── results/
│
└── documentation/          # Project documentation
    ├── README.md
    ├── ARCHITECTURE.md
    ├── API.md
    └── ...
```

### Key Files

**app.py**: Application factory pattern
```python
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    login_manager.init_app(app)
    mail.init_app(app)
    Session(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    
    return app
```

**config.py**: Centralized configuration
```python
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    # ... more settings
```

**Blueprints**:
- `auth.py`: `/auth/*` - Login, register, logout, profile
- `main.py`: `/` - Analysis, results, export
- `admin.py`: `/admin/*` - Dashboard, users, messages, analytics

---

## Code Style & Standards

### Python Style Guide

Follow **PEP 8** with minor modifications:

**Line length**: 88 characters (Black default)
**Indentation**: 4 spaces
**Quotes**: Double quotes for strings
**Imports**: Grouped and sorted with `isort`

### Code Formatting

**Black** (automatic formatter):
```bash
# Format all Python files
black .

# Check without modifying
black --check .

# Format specific file
black app.py
```

**isort** (import sorting):
```bash
# Sort imports
isort .

# Check without modifying
isort --check-only .
```

**Configuration** (pyproject.toml):
```toml
[tool.black]
line-length = 88
target-version = ['py38']
include = '\.pyi?$'

[tool.isort]
profile = "black"
line_length = 88
```

### Linting

**Flake8**:
```bash
# Check code quality
flake8 .

# Ignore specific warnings
flake8 --ignore=E501,W503 .
```

**Configuration** (.flake8):
```ini
[flake8]
max-line-length = 88
extend-ignore = E203, E501, W503
exclude = venv, __pycache__, .git
```

### Naming Conventions

**Variables**: `snake_case`
```python
user_id = "123"
analysis_results = {}
```

**Functions**: `snake_case`
```python
def load_users():
    pass

def analyze_app(app_id):
    pass
```

**Classes**: `PascalCase`
```python
class User:
    pass

class SentimentAnalyzer:
    pass
```

**Constants**: `UPPER_SNAKE_CASE`
```python
MAX_REVIEWS = 500
DEFAULT_TIMEOUT = 60
```

**Private methods/variables**: Prefix with `_`
```python
def _internal_helper():
    pass

_cache = {}
```

### Docstrings

**Google style**:
```python
def analyze_sentiment(reviews):
    """Analyze sentiment of reviews using TextBlob.
    
    Args:
        reviews (list): List of review strings to analyze.
    
    Returns:
        dict: Dictionary containing sentiment counts and percentages.
            - positive (int): Count of positive reviews
            - negative (int): Count of negative reviews
            - neutral (int): Count of neutral reviews
            - total_reviews (int): Total number of reviews
    
    Raises:
        ValueError: If reviews list is empty.
    
    Example:
        >>> reviews = ["Great app!", "Terrible experience"]
        >>> analyze_sentiment(reviews)
        {'positive': 1, 'negative': 1, 'neutral': 0, 'total_reviews': 2}
    """
    pass
```

### Type Hints

```python
from typing import List, Dict, Optional, Tuple

def fetch_app_details(app_id: str) -> Dict[str, any]:
    """Fetch app details from Google Play Store."""
    pass

def classify_reviews(
    reviews: List[str], 
    threshold: float = 0.5
) -> Tuple[List[Dict], int, int]:
    """Classify reviews as fraud or legitimate."""
    pass

def get_user_by_id(user_id: str) -> Optional[Dict]:
    """Get user by ID, returns None if not found."""
    pass
```

---

## Adding Features

### Adding a New Route

**1. Choose appropriate blueprint**:
- Auth-related → `auth.py`
- Analysis/results → `main.py`
- Admin features → `admin.py`

**2. Add route handler**:
```python
# main.py
@main_bp.route('/export/<format>')
@login_required
def export_results(format):
    """Export analysis results in specified format."""
    if format not in ['json', 'csv', 'pdf']:
        return jsonify({'error': 'Invalid format'}), 400
    
    # Implementation
    return send_file(...)
```

**3. Create template** (if needed):
```html
<!-- templates/analysis/export.html -->
{% extends "base.html" %}
{% block content %}
<h1>Export Results</h1>
<!-- ... -->
{% endblock %}
```

**4. Add navigation link** (if needed):
```html
<!-- templates/base.html -->
<a href="{{ url_for('main.export_results', format='pdf') }}">Export PDF</a>
```

### Adding a New Module

**1. Create module file**:
```bash
touch modules/new_feature.py
```

**2. Implement functionality**:
```python
# modules/new_feature.py
"""New feature module for XYZ functionality."""

def process_data(input_data):
    """Process input data and return results."""
    # Implementation
    return results
```

**3. Import in blueprint**:
```python
# main.py
from modules.new_feature import process_data

@main_bp.route('/new-feature')
def new_feature():
    results = process_data(request.args.get('data'))
    return render_template('new_feature.html', results=results)
```

### Adding Database Fields

**Current**: JSON files (add field to schema)
```python
# To add 'phone_number' to User model:

# 1. Update file_store.py schema documentation
"""
User schema:
- id: UUID
- username: string
- email: string
- password: string (hashed)
- phone_number: string (new field)  # <-- Add this
- role: string
- created_at: datetime
"""

# 2. Update user creation
new_user = {
    'id': str(uuid.uuid4()),
    'username': username,
    'email': email,
    'password': hashed_password,
    'phone_number': phone_number,  # <-- Add this
    'role': 'user',
    'created_at': datetime.now().isoformat()
}

# 3. Update User class in auth.py
class User:
    def __init__(self, user_dict):
        self.id = user_dict['id']
        self.username = user_dict['username']
        self.email = user_dict['email']
        self.password = user_dict['password']
        self.phone_number = user_dict.get('phone_number', '')  # <-- Add with default
        self.role = user_dict['role']
```

### Adding Frontend Assets

**CSS**:
```bash
# Add to static/css/style.css
.new-feature-class {
    color: #333;
    font-size: 16px;
}
```

**JavaScript**:
```bash
# Add to static/js/main.js or create new file
function handleNewFeature() {
    // Implementation
}
```

**Link in base.html**:
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/new-styles.css') }}">
<script src="{{ url_for('static', filename='js/new-script.js') }}"></script>
```

---

## Testing

### Unit Tests

**Structure**:
```
tests/
├── __init__.py
├── test_auth.py
├── test_main.py
├── test_admin.py
├── test_modules.py
└── conftest.py  # Pytest fixtures
```

**Example test**:
```python
# tests/test_auth.py
import pytest
from app import create_app
from file_store import load_users, save_users

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_register(client):
    """Test user registration."""
    response = client.post('/auth/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'Password123!'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Registration successful' in response.data

def test_login(client):
    """Test user login."""
    # First register
    client.post('/auth/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'Password123!'
    })
    
    # Then login
    response = client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'Password123!'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Dashboard' in response.data
```

**Running tests**:
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=. --cov-report=html

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_auth.py::test_register
```

### Integration Tests

```python
# tests/test_integration.py
def test_complete_analysis_workflow(client):
    """Test full analysis workflow."""
    # 1. Login
    client.post('/auth/login', data={
        'username': 'admin',
        'password': 'admin123'
    })
    
    # 2. Submit analysis
    response = client.post('/analyze', data={
        'app_id': 'com.whatsapp'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Analysis Results' in response.data
    
    # 3. Export PDF
    response = client.get('/download_pdf/1')
    assert response.status_code == 200
    assert response.content_type == 'application/pdf'
```

### Manual Testing Checklist

- [ ] User registration with valid/invalid data
- [ ] Login with correct/incorrect credentials
- [ ] Analysis with valid/invalid app IDs
- [ ] PDF generation and download
- [ ] Email sending
- [ ] CSV export
- [ ] Admin dashboard access (admin only)
- [ ] User management (admin only)
- [ ] Message submission and responses
- [ ] Session persistence
- [ ] Logout functionality

---

## Debugging

### Flask Debug Mode

**Enable in .env**:
```bash
DEBUG=True
FLASK_ENV=development
```

**Features**:
- Interactive debugger on errors
- Automatic reloading on code changes
- Detailed error pages

**⚠️ Never enable in production!**

### Python Debugger

**Using pdb**:
```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or in Python 3.7+
breakpoint()
```

**Using ipdb** (better interface):
```bash
pip install ipdb
```

```python
import ipdb; ipdb.set_trace()
```

**Commands**:
```
n (next)       - Execute next line
s (step)       - Step into function
c (continue)   - Continue execution
p var          - Print variable
pp var         - Pretty-print variable
l (list)       - Show current location
w (where)      - Show stack trace
q (quit)       - Exit debugger
```

### Logging

**Add logging**:
```python
import logging

# Configure logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Use in code
logger.debug("Fetching app details for: %s", app_id)
logger.info("Analysis completed successfully")
logger.warning("Review count below threshold: %d", count)
logger.error("Failed to fetch reviews: %s", error)
```

**View logs**:
```bash
# Development server output
python run.py

# Production systemd service
sudo journalctl -u fraud-app -f
```

### Common Issues

**Issue**: `ModuleNotFoundError`
**Solution**: Ensure venv is activated
```bash
source venv/bin/activate
which python  # Should show venv path
```

**Issue**: `TemplateNotFound`
**Solution**: Check template path
```python
# Correct
return render_template('auth/login.html')

# Wrong (missing blueprint prefix)
return render_template('login.html')
```

**Issue**: Database file locked
**Solution**: Check file permissions
```bash
ls -la data/*.json
chmod 644 data/*.json
```

---

## Git Workflow

### Branching Strategy

**Main branches**:
- `main`: Production-ready code
- `develop`: Integration branch for features

**Feature branches**:
```bash
# Create feature branch
git checkout -b feature/new-export-format

# Work on feature
git add .
git commit -m "feat: Add Excel export format"

# Push to remote
git push origin feature/new-export-format

# Create pull request on GitHub/GitLab
```

### Commit Messages

**Format**: `<type>(<scope>): <subject>`

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples**:
```bash
git commit -m "feat(analysis): Add sentiment confidence scores"
git commit -m "fix(auth): Resolve password reset email issue"
git commit -m "docs(api): Update API documentation"
git commit -m "refactor(main): Extract analysis logic to module"
git commit -m "test(auth): Add user registration tests"
```

### Pull Request Process

1. **Create feature branch**
2. **Make changes and commit**
3. **Push to remote**
4. **Open pull request**:
   - Clear title and description
   - Link related issues
   - Add screenshots (if UI changes)
5. **Code review**:
   - Address feedback
   - Update PR with fixes
6. **Merge** (after approval):
   - Squash and merge (preferred)
   - Or merge commit

---

## Contributing

### Getting Started

1. **Fork repository**
2. **Clone your fork**:
   ```bash
   git clone https://github.com/Ian-Lusule/fraud-app-analyzer-flask.git
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/original/fraud-app-analyzer-flask.git
   ```
4. **Sync with upstream**:
   ```bash
   git fetch upstream
   git merge upstream/main
   ```

### Code Review Checklist

Before submitting PR:
- [ ] Code follows style guide (Black, Flake8)
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No secrets in code
- [ ] No debug code (print statements, breakpoints)
- [ ] Tested locally
- [ ] Commit messages follow convention

### Areas for Contribution

**High priority**:
- Database migration (JSON → PostgreSQL)
- Unit tests (currently minimal)
- API documentation (OpenAPI/Swagger)
- Performance optimization

**Feature requests**:
- Multi-language support (i18n)
- Advanced analytics dashboard
- Export to Excel/Word
- Scheduled analysis
- Webhook notifications

**Bug fixes**:
- Check GitHub Issues for open bugs

---

**Last Updated**: February 2026
