# Data Models & Storage

## Table of Contents

1. [Storage Architecture](#storage-architecture)
2. [User Data Model](#user-data-model)
3. [Messages Data Model](#messages-data-model)
4. [Analysis Results Model](#analysis-results-model)
5. [Search Logs Model](#search-logs-model)
6. [File Operations](#file-operations)
7. [Data Migration](#data-migration)
8. [Backup & Recovery](#backup--recovery)

---

## Storage Architecture

### File-Based Storage

The application uses **JSON files** and **CSV** for data persistence:

```
data/
├── users.json              # User accounts and authentication
├── messages.json           # Admin messages and notifications
├── search_logs.csv         # Search history and analytics
└── results/                # Analysis results (one file per analysis)
    ├── 1_20260202_125613_com.whatsapp.json
    ├── 2_20260202_130145_com.instagram.android.json
    └── ...
```

### Advantages

- ✅ Simple setup (no database server required)
- ✅ Easy backup (just copy files)
- ✅ Portable (works anywhere)
- ✅ Human-readable (JSON/CSV)
- ✅ Version control friendly

### Limitations

- ❌ Not suitable for high concurrency
- ❌ No ACID transactions
- ❌ Limited query capabilities
- ❌ File locking issues on NFS/shared storage

**Recommendation**: For production with >100 concurrent users, migrate to PostgreSQL/MySQL.

---

## User Data Model

**File**: `data/users.json`

### Schema

```json
[
  {
    "id": "unique-uuid-string",
    "username": "string (unique, 3-50 chars)",
    "email": "string (valid email)",
    "password": "string (bcrypt hash)",
    "role": "string (admin|user)",
    "created_at": "string (ISO 8601 datetime)",
    "last_login": "string|null (ISO 8601 datetime)"
  }
]
```

### Example

```json
[
  {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "username": "admin",
    "email": "admin@example.com",
    "password": "$2b$12$KIXqZ9N3x.L9.8Qh0vZ1XOeH7Y2Z3Z4Z5Z6Z7Z8Z9Z0Z1Z2Z3Z4Z5Z",
    "role": "admin",
    "created_at": "2024-01-15T10:30:00Z",
    "last_login": "2024-02-02T14:25:33Z"
  },
  {
    "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "username": "john_doe",
    "email": "john@example.com",
    "password": "$2b$12$...",
    "role": "user",
    "created_at": "2024-01-20T09:15:00Z",
    "last_login": "2024-02-01T11:45:22Z"
  }
]
```

### Fields Description

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | String (UUID) | Yes | Unique user identifier |
| `username` | String | Yes | Unique username (3-50 chars) |
| `email` | String | Yes | User email (validated) |
| `password` | String | Yes | Bcrypt hashed password |
| `role` | String | Yes | User role: `admin` or `user` |
| `created_at` | String (ISO 8601) | Yes | Account creation timestamp |
| `last_login` | String/Null | No | Last login timestamp |

### Password Hashing

**Algorithm**: bcrypt (via Werkzeug)
```python
from werkzeug.security import generate_password_hash, check_password_hash

# Hash password
hashed = generate_password_hash(password, method='pbkdf2:sha256')

# Verify password
is_valid = check_password_hash(hashed, password)
```

**Settings**:
- Method: `pbkdf2:sha256`
- Iterations: 260,000 (default)
- Salt length: 16 bytes

### User Roles

| Role | Permissions |
|------|-------------|
| `admin` | Full access: analysis, admin dashboard, user management, messages |
| `user` | Limited access: analysis, own results, profile |

**Role check** (in templates):
```python
{% if current_user.role == 'admin' %}
    <a href="{{ url_for('admin.dashboard') }}">Admin Panel</a>
{% endif %}
```

### File Operations

**Load users**:
```python
# file_store.py
def load_users():
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
```

**Save users**:
```python
def save_users(users):
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)
```

**Get user by username**:
```python
def get_user_by_username(username):
    users = load_users()
    for user in users:
        if user['username'] == username:
            return user
    return None
```

---

## Messages Data Model

**File**: `data/messages.json`

### Schema

```json
[
  {
    "id": "unique-uuid-string",
    "user_id": "string (UUID)",
    "username": "string",
    "email": "string",
    "subject": "string",
    "message": "string",
    "created_at": "string (ISO 8601)",
    "status": "string (new|read|resolved)",
    "admin_reply": "string|null"
  }
]
```

### Example

```json
[
  {
    "id": "m1n2o3p4-q5r6-s7t8-u9v0-w1x2y3z4a5b6",
    "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "username": "john_doe",
    "email": "john@example.com",
    "subject": "Unable to generate PDF report",
    "message": "When I click 'Download PDF', I get an error message...",
    "created_at": "2024-02-02T10:15:30Z",
    "status": "new",
    "admin_reply": null
  },
  {
    "id": "n2o3p4q5-r6s7-t8u9-v0w1-x2y3z4a5b6c7",
    "user_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "username": "jane_smith",
    "email": "jane@example.com",
    "subject": "Feature request: Export to Excel",
    "message": "It would be great if we could export results to Excel...",
    "created_at": "2024-02-01T14:20:15Z",
    "status": "read",
    "admin_reply": "Thanks for the suggestion! We'll consider it for the next release."
  }
]
```

### Fields Description

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | String (UUID) | Yes | Unique message identifier |
| `user_id` | String (UUID) | Yes | ID of user who sent message |
| `username` | String | Yes | Username (denormalized for display) |
| `email` | String | Yes | User email |
| `subject` | String | Yes | Message subject |
| `message` | String | Yes | Message body |
| `created_at` | String (ISO 8601) | Yes | Message timestamp |
| `status` | String | Yes | `new`, `read`, or `resolved` |
| `admin_reply` | String/Null | No | Admin's response to message |

### Message Status

| Status | Description |
|--------|-------------|
| `new` | Unread message |
| `read` | Admin has viewed message |
| `resolved` | Issue resolved, reply sent |

---

## Analysis Results Model

**Directory**: `data/results/`

**Filename format**: `{user_id}_{timestamp}_{app_id}.json`

Example: `1_20260202_125613_com.whatsapp.json`

### Schema

```json
{
  "user_id": "string (UUID)",
  "username": "string",
  "app_id": "string",
  "app_name": "string",
  "timestamp": "string (ISO 8601)",
  "search_id": "integer",
  "app_details": {
    "title": "string",
    "description": "string",
    "developer": "string",
    "genre": "string",
    "price": "string",
    "installs": "string",
    "score": "float",
    "ratings": "integer",
    "reviews": "integer",
    "icon": "string (URL)"
  },
  "reviews_data": [
    {
      "reviewId": "string",
      "userName": "string",
      "userImage": "string (URL)",
      "content": "string",
      "score": "integer (1-5)",
      "thumbsUpCount": "integer",
      "reviewCreatedVersion": "string",
      "at": "string (ISO 8601)",
      "replyContent": "string|null",
      "repliedAt": "string|null (ISO 8601)"
    }
  ],
  "sentiment_analysis": {
    "positive": "integer",
    "negative": "integer",
    "neutral": "integer",
    "positive_percentage": "float",
    "negative_percentage": "float",
    "neutral_percentage": "float",
    "total_reviews": "integer"
  },
  "classification_results": {
    "classified_reviews": [
      {
        "review": "string",
        "classification": "string (fraud|legitimate)",
        "confidence": "float (0-1)",
        "sentiment": "string (positive|negative|neutral)",
        "sentiment_score": "float (-1 to 1)"
      }
    ],
    "fraud_count": "integer",
    "legitimate_count": "integer",
    "fraud_percentage": "float"
  },
  "classification_metrics": {
    "accuracy": "float (0-1)",
    "precision": "float (0-1)",
    "recall": "float (0-1)",
    "f1_score": "float (0-1)",
    "confusion_matrix": "array[[int, int], [int, int]]"
  },
  "word_cloud_data": {
    "positive": "object (word: frequency)",
    "negative": "object (word: frequency)"
  }
}
```

### Example (Abbreviated)

```json
{
  "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "username": "admin",
  "app_id": "com.whatsapp",
  "app_name": "WhatsApp Messenger",
  "timestamp": "2024-02-02T12:56:13Z",
  "search_id": 1,
  "app_details": {
    "title": "WhatsApp Messenger",
    "description": "Simple. Secure. Reliable messaging...",
    "developer": "WhatsApp LLC",
    "genre": "Communication",
    "price": "Free",
    "installs": "5,000,000,000+",
    "score": 4.1,
    "ratings": 89234567,
    "reviews": 12345678,
    "icon": "https://play-lh.googleusercontent.com/..."
  },
  "reviews_data": [
    {
      "reviewId": "gp:AOqpT...",
      "userName": "John Doe",
      "userImage": "https://play-lh.googleusercontent.com/...",
      "content": "Great app! Very reliable and easy to use.",
      "score": 5,
      "thumbsUpCount": 123,
      "reviewCreatedVersion": "2.24.1.81",
      "at": "2024-01-15T10:30:00Z",
      "replyContent": "Thank you for your feedback!",
      "repliedAt": "2024-01-16T09:00:00Z"
    }
  ],
  "sentiment_analysis": {
    "positive": 350,
    "negative": 120,
    "neutral": 30,
    "positive_percentage": 70.0,
    "negative_percentage": 24.0,
    "neutral_percentage": 6.0,
    "total_reviews": 500
  },
  "classification_results": {
    "classified_reviews": [
      {
        "review": "Great app! Very reliable and easy to use.",
        "classification": "legitimate",
        "confidence": 0.95,
        "sentiment": "positive",
        "sentiment_score": 0.8
      }
    ],
    "fraud_count": 25,
    "legitimate_count": 475,
    "fraud_percentage": 5.0
  },
  "classification_metrics": {
    "accuracy": 0.92,
    "precision": 0.88,
    "recall": 0.85,
    "f1_score": 0.86,
    "confusion_matrix": [[450, 25], [10, 15]]
  },
  "word_cloud_data": {
    "positive": {
      "great": 150,
      "good": 120,
      "excellent": 80,
      "love": 75
    },
    "negative": {
      "bad": 45,
      "poor": 30,
      "worst": 25,
      "hate": 20
    }
  }
}
```

### Nested Objects

**app_details**: App metadata from Google Play Store
**reviews_data**: Array of raw review objects
**sentiment_analysis**: Sentiment distribution statistics
**classification_results**: Fraud detection results with confidence scores
**classification_metrics**: ML model performance metrics
**word_cloud_data**: Word frequency for visualization

---

## Search Logs Model

**File**: `data/search_logs.csv`

### Schema

CSV format with header:
```csv
search_id,user_id,username,app_id,app_name,timestamp,status
```

### Example

```csv
search_id,user_id,username,app_id,app_name,timestamp,status
1,a1b2c3d4-e5f6-7890-abcd-ef1234567890,admin,com.whatsapp,WhatsApp Messenger,2024-02-02T12:56:13Z,completed
2,a1b2c3d4-e5f6-7890-abcd-ef1234567890,admin,com.instagram.android,Instagram,2024-02-02T13:15:30Z,completed
3,b2c3d4e5-f6a7-8901-bcde-f12345678901,john_doe,com.facebook.katana,Facebook,2024-02-02T14:20:45Z,failed
```

### Fields Description

| Field | Type | Description |
|-------|------|-------------|
| `search_id` | Integer | Auto-incrementing search ID |
| `user_id` | String (UUID) | ID of user who performed search |
| `username` | String | Username (denormalized) |
| `app_id` | String | Google Play app ID |
| `app_name` | String | Human-readable app name |
| `timestamp` | String (ISO 8601) | Search timestamp |
| `status` | String | `completed`, `failed`, or `in_progress` |

### Status Values

| Status | Description |
|--------|-------------|
| `completed` | Analysis finished successfully |
| `failed` | Error during analysis |
| `in_progress` | Currently processing (rare, for long analyses) |

---

## File Operations

### Reading Data

**Users**:
```python
from file_store import load_users

users = load_users()
# Returns: list of user dicts
```

**Messages**:
```python
from file_store import load_messages

messages = load_messages()
# Returns: list of message dicts
```

**Analysis results**:
```python
import json
import os

def load_analysis_result(filename):
    filepath = os.path.join('data/results', filename)
    with open(filepath, 'r') as f:
        return json.load(f)
```

**Search logs**:
```python
import pandas as pd

df = pd.read_csv('data/search_logs.csv')
# Returns: pandas DataFrame
```

### Writing Data

**Users**:
```python
from file_store import save_users

users = load_users()
users.append(new_user)
save_users(users)
```

**Messages**:
```python
from file_store import save_messages

messages = load_messages()
messages.append(new_message)
save_messages(messages)
```

**Analysis results**:
```python
import json
import os

def save_analysis_result(data, filename):
    os.makedirs('data/results', exist_ok=True)
    filepath = os.path.join('data/results', filename)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
```

**Search logs**:
```python
import csv
import os

def append_search_log(search_data):
    file_exists = os.path.exists('data/search_logs.csv')
    
    with open('data/search_logs.csv', 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'search_id', 'user_id', 'username', 'app_id', 
            'app_name', 'timestamp', 'status'
        ])
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(search_data)
```

### Thread Safety

⚠️ **Important**: File-based storage is **not thread-safe** by default.

**For production**:
1. Use file locking:
```python
import fcntl

with open('data/users.json', 'r+') as f:
    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
    data = json.load(f)
    # ... modify data
    f.seek(0)
    json.dump(data, f)
    f.truncate()
    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
```

2. Or migrate to database (PostgreSQL/MySQL)

---

## Data Migration

### Migrate to PostgreSQL

**1. Install SQLAlchemy**:
```bash
pip install psycopg2-binary sqlalchemy
```

**2. Create models** (models.py):
```python
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(String(36), primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)
    created_at = Column(DateTime, nullable=False)
    last_login = Column(DateTime, nullable=True)
```

**3. Migration script**:
```python
import json
from datetime import datetime
from models import User, Message, engine, Session

# Create tables
Base.metadata.create_all(engine)

# Load JSON data
with open('data/users.json', 'r') as f:
    users_data = json.load(f)

# Insert into database
session = Session()
for user_data in users_data:
    user = User(
        id=user_data['id'],
        username=user_data['username'],
        email=user_data['email'],
        password=user_data['password'],
        role=user_data['role'],
        created_at=datetime.fromisoformat(user_data['created_at']),
        last_login=datetime.fromisoformat(user_data['last_login']) if user_data.get('last_login') else None
    )
    session.add(user)

session.commit()
print("Migration completed!")
```

---

## Backup & Recovery

### Backup Strategy

**What to backup**:
```bash
# All data files
tar -czf backup_$(date +%Y%m%d).tar.gz data/

# Or individual files
cp data/users.json backups/users_$(date +%Y%m%d).json
cp data/messages.json backups/messages_$(date +%Y%m%d).json
cp data/search_logs.csv backups/search_logs_$(date +%Y%m%d).csv
cp -r data/results backups/results_$(date +%Y%m%d)/
```

**Automated backup**:
```bash
# Cron job (daily at 2 AM)
0 2 * * * /usr/local/bin/backup-fraud-app.sh
```

See [DEPLOYMENT.md - Backup & Recovery](DEPLOYMENT.md#backup--recovery) for full backup script.

### Restore

```bash
# Extract backup
tar -xzf backup_20240202.tar.gz

# Stop application
sudo systemctl stop fraud-app

# Replace data
rm -rf data/
mv data/ data.old/
cp -r backup/data/ data/

# Fix permissions
sudo chown -R fraudapp:fraudapp data/
chmod 755 data/
chmod 644 data/*.json

# Restart
sudo systemctl start fraud-app
```

---

**Last Updated**: February 2026
