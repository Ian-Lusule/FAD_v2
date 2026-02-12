# API Documentation

## Overview

The Fraud App Analyzer exposes HTTP endpoints organized into three main blueprints:
- **Authentication** (`/auth/*`) - User registration, login, and profile management
- **Main Application** (`/*`) - Core analysis, results, comparison, and export features
- **Admin** (`/admin/*`) - Administrative functions (user management, analytics, messaging)

All routes return either HTML (rendered Jinja2 templates) or file downloads. API responses use Flask's flash message system for user feedback.

## Authentication Requirements

| Symbol | Meaning |
|--------|---------|
| 🔓 | Public (no authentication required) |
| 🔒 | Requires login (`@login_required`) |
| 👑 | Requires admin privileges (`@admin_required`) |

---

## Authentication Blueprint (`/auth`)

### POST `/auth/register` 🔓

Register a new user account.

**Request**:
```http
POST /auth/register
Content-Type: application/x-www-form-urlencoded

username=johndoe&email=john@example.com&password=SecurePass123&confirm_password=SecurePass123
```

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `username` | string | Yes | Unique username (alphanumeric + underscore) |
| `email` | string | Yes | Valid email address |
| `password` | string | Yes | Minimum 8 characters |
| `confirm_password` | string | Yes | Must match password |

**Response**:
- Success: Redirect to `/auth/login` with success message
- Error: Re-render registration form with error message

**Validation**:
- Username: 3-20 chars, alphanumeric + underscore, unique
- Email: Valid format, unique
- Password: Min 8 chars, uppercase, lowercase, digit

---

### POST `/auth/login` 🔓

Authenticate user and create session.

**Request**:
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=johndoe&password=SecurePass123&remember=on
```

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `username` | string | Yes | Registered username |
| `password` | string | Yes | User password |
| `remember` | boolean | No | Remember login (checkbox) |

**Response**:
- Success: Redirect to `/auth/dashboard`
- Error: Re-render login form with error message

---

### GET `/auth/dashboard` 🔒

User personal dashboard showing saved analyses.

**Response**: HTML page with:
- User information
- List of saved analysis results
- Quick actions (analyze, compare)
- Unread message count

---

### GET `/auth/logout` 🔒

End user session and redirect to landing page.

**Response**: Redirect to `/` with logout message

---

### GET/POST `/auth/change-password` 🔒

Change user password.

**Request (POST)**:
```http
POST /auth/change-password
Content-Type: application/x-www-form-urlencoded

current_password=OldPass123&new_password=NewPass456&confirm_password=NewPass456
```

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `current_password` | string | Yes | Current password for verification |
| `new_password` | string | Yes | New password (min 8 chars) |
| `confirm_password` | string | Yes | Must match new_password |

---

### GET/POST `/auth/contact-admin` 🔒

Send message to admin.

**Request (POST)**:
```http
POST /auth/contact-admin
Content-Type: application/x-www-form-urlencoded

subject=Question about analysis&message=How do I interpret the ML score?
```

---

## Main Application Blueprint (`/`)

### GET `/` 🔓

Landing page with app search form.

**Response**: HTML page with search form for app analysis

---

### POST `/analyze` 🔓

Analyze a Google Play Store app.

**Request**:
```http
POST /analyze
Content-Type: application/x-www-form-urlencoded

app_id=com.example.myapp&country=us&num_reviews=100&save_result=on
```

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `app_id` | string | Yes | - | App package ID or Play Store URL |
| `country` | string | No | `us` | Country code (us, gb, in, ke, etc.) |
| `num_reviews` | integer | No | `100` | Number of reviews to analyze (50-5000) |
| `save_result` | boolean | No | `false` | Save result to user history (requires login) |

**Response**:
- Success: Redirect to `/results/<result_id>`
- Error: Re-render form with error message

**Process**:
1. Extract app ID from URL if provided
2. Fetch app details from Google Play
3. Fetch user reviews (up to `num_reviews`)
4. Perform sentiment analysis
5. Run ML classification
6. Save result if user is logged in and `save_result=on`
7. Store in session for immediate display

**Example**:
```bash
curl -X POST http://localhost:5000/analyze \
  -d "app_id=https://play.google.com/store/apps/details?id=com.example.myapp" \
  -d "country=us" \
  -d "num_reviews=200"
```

---

### GET `/results/<result_id>` 🔓

Display analysis results.

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `result_id` | string | Yes | Either "latest" or UUID of saved result |

**Response**: HTML page with:
- App metadata (name, developer, score, downloads)
- Sentiment distribution chart
- Sentiment trend over time
- Word cloud of review text
- ML classification metrics (confusion matrix, precision, recall, F1)
- Risk indicators and warnings
- Sample reviews by sentiment
- Export options (PDF, CSV, Email)

**Data Structure**:
```python
{
    "app_id": "com.example.myapp",
    "app_name": "Example App",
    "developer": "Example Inc.",
    "score": 4.2,
    "reviews_analyzed": 200,
    "sentiment_counts": {
        "positive": 120,
        "neutral": 50,
        "negative": 30
    },
    "classification_metrics": {
        "confusion": {"tp": 110, "tn": 45, "fp": 5, "fn": 10},
        "precision": 0.96,
        "recall": 0.92,
        "f1_score": 0.94,
        "accuracy": 0.93
    },
    "reviews": [...],
    "timestamp": "2026-02-12T10:30:00"
}
```

---

### GET `/export/pdf` 🔒

Download analysis as PDF report.

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `result_id` | string | No | Saved result UUID (defaults to latest session result) |

**Response**: PDF file download
- Content-Type: `application/pdf`
- Content-Disposition: `attachment; filename="fraud_analysis_{app_name}_{timestamp}.pdf"`

**PDF Contents**:
1. Cover page with app info
2. Executive summary
3. Sentiment analysis charts
4. ML classification metrics
5. Risk indicators table
6. Sample reviews
7. Recommendations

---

### GET `/export/csv` 🔓

Download reviews as CSV.

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `result_id` | string | No | Saved result UUID (defaults to latest) |

**Response**: CSV file download
- Content-Type: `text/csv`
- Content-Disposition: `attachment; filename="reviews_{app_name}_{timestamp}.csv"`

**CSV Columns**:
```csv
content,score,at,thumbsUpCount,sentiment,fraud_score
"Great app!",5,2026-02-10,42,positive,0.05
"Terrible experience",1,2026-02-11,3,negative,0.85
```

---

### POST `/send_email_report` 🔓

Send analysis report via email.

**Request**:
```http
POST /send_email_report
Content-Type: application/x-www-form-urlencoded

email=recipient@example.com&result_id=abc123
```

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `email` | string | Yes | Recipient email address |
| `result_id` | string | No | Saved result UUID |

**Response**:
- Success: Flash message + redirect to results page
- Error: Flash error message

**Email Contents**:
- HTML email body with summary
- PDF report attachment
- CSV data attachment

**Requirements**:
- Valid SMTP configuration in `.env`
- Working SMTP server credentials

---

### GET `/compare` 🔓

Multi-app comparison page.

**Response**: HTML form to input multiple app IDs (up to 5)

---

### POST `/compare` 🔓

Compare multiple apps side-by-side.

**Request**:
```http
POST /compare
Content-Type: application/x-www-form-urlencoded

app_ids=com.app1,com.app2,com.app3&country=us&num_reviews=100
```

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `app_ids` | string | Yes | Comma-separated app IDs (2-5 apps) |
| `country` | string | No | Country code |
| `num_reviews` | integer | No | Reviews per app |

**Response**: HTML comparison table with:
- App metadata side-by-side
- Sentiment distribution comparison
- ML metrics comparison
- Risk ranking
- Visual charts

---

### GET `/delete_result/<result_id>` 🔒

Delete a saved analysis result.

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `result_id` | string | Yes | UUID of saved result |

**Response**: Redirect to `/auth/dashboard` with confirmation message

**Authorization**: User can only delete their own results (admins can delete any)

---

## Admin Blueprint (`/admin`)

### GET `/admin/dashboard` 👑

Admin overview dashboard.

**Response**: HTML page with:
- Total users count
- Recent searches
- System statistics
- Quick links to admin functions

---

### GET `/admin/users` 👑

User management interface.

**Response**: HTML table with:
- All registered users
- User roles (admin/regular)
- Registration dates
- Last login times
- Action buttons (edit, delete, promote)

---

### POST `/admin/create_user` 👑

Create a new user account.

**Request**:
```http
POST /admin/create_user
Content-Type: application/x-www-form-urlencoded

username=newuser&email=new@example.com&password=Pass123&is_admin=on
```

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `username` | string | Yes | Username |
| `email` | string | Yes | Email |
| `password` | string | Yes | Initial password |
| `is_admin` | boolean | No | Grant admin privileges |

---

### POST `/admin/edit_user/<user_id>` 👑

Update user information.

**Parameters** (URL):
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | integer | Yes | User ID to edit |

**Request Body**:
```http
POST /admin/edit_user/5
Content-Type: application/x-www-form-urlencoded

email=updated@example.com&is_admin=on
```

---

### POST `/admin/delete_user/<user_id>` 👑

Delete a user account.

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | integer | Yes | User ID to delete |

**Response**: Redirect to `/admin/users` with confirmation

**Restrictions**: Cannot delete the main admin account

---

### GET `/admin/messages` 👑

Message center for admin-user communication.

**Response**: HTML page with:
- List of messages from users
- Message read/unread status
- Reply functionality

---

### POST `/admin/send_message` 👑

Send message to a user or all users.

**Request**:
```http
POST /admin/send_message
Content-Type: application/x-www-form-urlencoded

user_id=5&subject=System Update&message=We're performing maintenance tonight
```

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | integer | No | Specific user (omit for broadcast) |
| `subject` | string | Yes | Message subject |
| `message` | string | Yes | Message body |

---

### GET `/admin/analytics` 👑

Usage analytics and statistics.

**Response**: HTML page with:
- Search logs table
- Usage trends over time
- Popular apps analyzed
- User activity metrics

---

## Error Responses

### Common HTTP Status Codes

| Code | Meaning | When It Occurs |
|------|---------|----------------|
| 200 | OK | Successful request |
| 302 | Found (Redirect) | After successful form submission |
| 400 | Bad Request | Invalid input parameters |
| 401 | Unauthorized | Not logged in (redirects to login) |
| 403 | Forbidden | Insufficient privileges (not admin) |
| 404 | Not Found | Invalid result_id or route |
| 500 | Internal Server Error | Application error (check logs) |

### Error Handling

All errors display flash messages:
- **Success**: Green alert (`alert-success`)
- **Info**: Blue alert (`alert-info`)
- **Warning**: Yellow alert (`alert-warning`)
- **Error**: Red alert (`alert-danger`)

---

## Rate Limiting

Currently not implemented. External API limits:
- **Google Play Scraper**: ~100 requests/min per IP
- **TextBlob**: No limits (local processing)

---

## Security Considerations

1. **Password Hashing**: PBKDF2-SHA256 with salt (Werkzeug)
2. **Session Management**: Server-side sessions, signed cookies
3. **CSRF Protection**: Flask-WTF (not yet fully implemented)
4. **SQL Injection**: N/A (file-based storage)
5. **XSS Protection**: Jinja2 auto-escaping enabled
6. **HTTPS**: Required in production (Nginx + Certbot)

---

**Last Updated**: February 2026
