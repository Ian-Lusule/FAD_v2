# Fraud App Analyzer - Complete Documentation

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Documentation Structure](#documentation-structure)
4. [System Requirements](#system-requirements)
5. [Key Features](#key-features)

## Overview

The **Fraud App Analyzer** is a comprehensive Flask-based web application designed to analyze Android applications from the Google Play Store for potential fraud indicators. The system uses sentiment analysis, review mining, and machine learning to assess app trustworthiness and provide detailed reports.

### Purpose

- Analyze Google Play Store apps for fraudulent patterns
- Perform sentiment analysis on user reviews
- Generate comprehensive PDF reports
- Send analysis reports via email
- Compare multiple apps side-by-side
- Admin dashboard for user management

### Technology Stack

- **Backend**: Flask (Python 3.8+)
- **Frontend**: Bootstrap 5, JavaScript
- **Data Processing**: Pandas, NumPy, scikit-learn
- **NLP**: TextBlob, WordCloud
- **Visualization**: Matplotlib, ReportLab (PDF generation)
- **Web Server**: Gunicorn + Nginx
- **Deployment**: Systemd, Certbot (SSL)
- **Data Scraping**: google-play-scraper

## Quick Start

### Local Development

```bash
# Clone the repository
git clone <repository-url>
cd fraud-app-analyzer-flask

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Run the application
python run.py
```

### Production Deployment

```bash
# Run the automated installer (Hestia/Oracle server)
sudo bash "Install on Hestia oracle server.sh"

# Or manually configure with systemd
sudo systemctl start fraud-app
sudo systemctl enable fraud-app
```

## Documentation Structure

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture, design patterns, and data flow |
| [INSTALLATION.md](INSTALLATION.md) | Detailed installation instructions for all environments |
| [API.md](API.md) | Complete API reference with all routes and endpoints |
| [DATABASE.md](DATABASE.md) | Data models, storage structure, and file formats |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Production deployment guide with Nginx, Gunicorn, SSL |
| [CONFIGURATION.md](CONFIGURATION.md) | All configuration options and environment variables |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common issues and their solutions |
| [DEVELOPMENT.md](DEVELOPMENT.md) | Developer guide for contributing and extending |
| [FILE_STRUCTURE.md](FILE_STRUCTURE.md) | Complete project file organization |
| [AI_PROMPT.md](AI_PROMPT.md) | Template for AI-assisted documentation generation |

## System Requirements

### Minimum Requirements

- **OS**: Linux (Ubuntu 20.04+, Debian 11+, Oracle Linux 8+)
- **Python**: 3.8 or higher
- **RAM**: 2GB minimum (4GB recommended)
- **Storage**: 2GB minimum
- **Network**: Outbound HTTPS access to Google Play Store

### Software Dependencies

- Python 3.8+
- Nginx (for production)
- System libraries: `python3-dev`, `build-essential`

## Key Features

### 1. App Analysis
- **Single App Analysis**: Fetch and analyze any Google Play Store app
- **Review Scraping**: Collect up to 5000+ user reviews
- **Sentiment Classification**: Positive, Negative, Neutral analysis
- **Fraud Indicators**: Detect suspicious patterns and keywords
- **ML Classification**: Machine learning model for risk assessment

### 2. Reporting
- **PDF Reports**: Professional, detailed reports with charts
- **Email Delivery**: Send reports directly to stakeholders
- **CSV Export**: Export raw data for further analysis
- **Visual Charts**: Sentiment trends, word clouds, distribution graphs

### 3. Comparison
- **Multi-App Compare**: Compare up to 5 apps side-by-side
- **Benchmarking**: Relative risk assessment and ranking
- **Competitive Analysis**: Developer comparison metrics

### 4. User Management
- **Authentication**: Secure login with password hashing
- **Role-Based Access**: Admin and regular user roles
- **User Dashboard**: Personal analysis history
- **Message System**: Admin-user communication

### 5. Admin Features
- **User Management**: Create, edit, delete users
- **Analytics Dashboard**: Usage statistics and trends
- **Message Center**: Send announcements and alerts
- **System Monitoring**: Track search logs and activity

## Project Status

- ✅ Core analysis engine operational
- ✅ PDF report generation functional
- ✅ Email sending configured
- ✅ Production deployment with HTTPS
- ✅ User authentication and authorization
- ✅ Admin dashboard and analytics
- ⚠️ Email SMTP requires valid credentials
- 🔄 Continuous improvements and bug fixes

## Support and Contribution

For issues, feature requests, or contributions:
- Review [DEVELOPMENT.md](DEVELOPMENT.md) for contribution guidelines
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- Refer to [API.md](API.md) for integration details

## License

[Specify your license here]

---

**Last Updated**: February 2026  
**Version**: 1.0.0
