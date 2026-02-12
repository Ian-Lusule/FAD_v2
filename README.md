# Fraud App Analyzer - Flask Edition

A Flask web application for analyzing Google Play Store apps for potential fraud risks using sentiment analysis and machine learning.

## Features

### Core Analysis
- **App Search**: Search by app name or Play Store URL with country selection
- **Sentiment Analysis**: Uses TextBlob with negative keyword override for accurate sentiment detection
- **Risk Assessment**: Automatic fraud risk detection based on customizable thresholds
- **Visualizations**: Sentiment trend charts and word clouds
- **App Comparison**: Side-by-side comparison of two apps

### User Features
- **Authentication**: User registration and login with secure password hashing
- **Dashboard**: Personalized dashboard with saved analysis history
- **Export Options**: Download analysis as CSV or PDF reports
- **Email Reports**: Send complete analysis reports via email
- **Admin Messaging**: Contact administrators directly from the dashboard

### Admin Features
- **User Management**: View, manage, and reset user passwords
- **Analytics Dashboard**: View search statistics and top apps/countries
- **Message Center**: Communicate with users
- **Data Export**: Export logs and user data as CSV

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd fraud-app-analyzer-flask