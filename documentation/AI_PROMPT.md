# AI Documentation Prompt Template

## Purpose

This document provides a comprehensive prompt template for AI assistants (like GPT-4, Claude, Gemini, etc.) to generate or update documentation for the Fraud App Analyzer Flask project. Use this template when you need to:

- Generate new documentation sections
- Update existing documentation
- Explain specific features or components
- Create user guides or tutorials
- Document API changes or new features

## How to Use This Prompt

1. Copy the relevant section below
2. Replace placeholders with specific information
3. Provide the prompt to your AI assistant
4. Review and edit the generated documentation
5. Commit to the `documentation/` directory

---

## Master Prompt Template

```
You are a technical documentation expert tasked with creating comprehensive, accurate, and user-friendly documentation for the Fraud App Analyzer Flask application.

### Project Context

**Project Name**: Fraud App Analyzer
**Technology Stack**: Flask (Python 3.8+), Bootstrap 5, Gunicorn, Nginx
**Purpose**: Analyze Android apps from Google Play Store for fraud indicators using sentiment analysis and machine learning
**Deployment**: Production-ready with HTTPS, systemd service management, automated installer

**Key Features**:
- Google Play Store app analysis
- Sentiment analysis on user reviews
- ML-based risk classification
- PDF report generation
- Email delivery of reports
- Multi-app comparison
- User authentication and role-based access
- Admin dashboard with analytics

**Architecture**: Modular Flask application with blueprints (auth, main, admin), file-based storage (JSON/CSV), and separate analysis modules (data_fetcher, sentiment_analyzer, report_generator, email_sender).

### Documentation Requirements

1. **Accuracy**: All technical details must match the actual implementation
2. **Clarity**: Use clear, concise language suitable for developers and system administrators
3. **Completeness**: Cover setup, usage, troubleshooting, and advanced topics
4. **Examples**: Include code snippets, command examples, and configuration samples
5. **Structure**: Use markdown with proper headings, lists, tables, and code blocks
6. **Diagrams**: Use ASCII diagrams or mermaid syntax for visual representations
7. **Cross-references**: Link to related documentation files when relevant

### Specific Task

[REPLACE WITH YOUR SPECIFIC DOCUMENTATION REQUEST]

Examples:
- "Document the complete API for the main.py blueprint, including all routes, request/response formats, and authentication requirements"
- "Create a troubleshooting guide for common deployment issues on Ubuntu 20.04 with Nginx"
- "Write a user guide explaining how to analyze an app, interpret results, and export reports"
- "Document the data flow from app search to PDF report generation with diagrams"

### Output Format

Provide the documentation in Markdown format with:
- Clear section headings (##, ###, ####)
- Code blocks with language tags ```python, ```bash, ```json
- Tables for structured data
- Bullet points and numbered lists where appropriate
- ASCII diagrams or mermaid diagrams for visual flow
- Cross-references to other documentation files

### Additional Context

[PROVIDE ANY SPECIFIC FILES, FUNCTIONS, OR CODE SNIPPETS TO REFERENCE]

Example:
- Reference file_store.py for data storage functions
- Include examples from auth.py for authentication patterns
- Show configuration from config.py and .env

```

---

## Specific Use Cases

### 1. API Documentation

```markdown
Generate comprehensive API documentation for the Fraud App Analyzer.

**Task**: Document all Flask routes in main.py, auth.py, and admin.py including:
- Route path and HTTP methods
- Authentication requirements (@login_required, admin_required)
- Request parameters (query string, form data, JSON body)
- Response format (HTML templates, JSON, file downloads)
- Example requests and responses
- Error handling and status codes

**Focus on**:
- `/analyze` endpoint with app_id, country, num_reviews parameters
- `/results/<result_id>` endpoint for viewing analysis
- `/export/pdf` and `/export/csv` endpoints
- `/admin/users` CRUD operations
- Authentication endpoints (`/auth/login`, `/auth/register`)

**Format**: Create API.md with sections for each blueprint, route tables, and code examples.
```

### 2. Installation Guide

```markdown
Create a detailed installation guide for the Fraud App Analyzer.

**Task**: Document installation procedures for:
1. Local development environment (macOS, Linux, Windows)
2. Production deployment on Ubuntu 20.04 with Nginx
3. Automated installation using "Install on Hestia oracle server.sh"
4. Manual systemd service setup
5. SSL certificate configuration with Certbot

**Include**:
- System requirements and dependencies
- Step-by-step commands
- Configuration file examples
- Verification steps
- Troubleshooting common installation issues

**Format**: Create INSTALLATION.md with platform-specific sections and code blocks.
```

### 3. Configuration Reference

```markdown
Document all configuration options for the Fraud App Analyzer.

**Task**: Create a comprehensive configuration reference including:
- Environment variables in .env file
- config.py Config class attributes
- Flask configuration options (SECRET_KEY, SESSION_*, MAIL_*)
- Gunicorn configuration (workers, bind address, timeout)
- Nginx configuration (proxy settings, SSL, static files)
- systemd service configuration

**Include**:
- Description of each option
- Default values
- Valid value ranges/formats
- Examples
- Security considerations

**Format**: Create CONFIGURATION.md with tables for each configuration group.
```

### 4. Troubleshooting Guide

```markdown
Create a troubleshooting guide for common issues with the Fraud App Analyzer.

**Task**: Document solutions for:
1. Installation errors (missing dependencies, permission issues)
2. Runtime errors (ReportLab MD5 error, WordCloud timeout, Google Play scraper failures)
3. Deployment issues (Nginx 403, SSL certificate failures, systemd service crashes)
4. Performance issues (slow analysis, memory errors, worker timeouts)
5. Data issues (corrupt JSON, missing results, session errors)

**Format**:
- Problem description
- Error messages/logs
- Root cause explanation
- Step-by-step solution
- Prevention tips

**Create**: TROUBLESHOOTING.md with problem-solution pairs and diagnostic commands.
```

### 5. User Guide

```markdown
Write a user guide for non-technical users of the Fraud App Analyzer.

**Task**: Explain how to:
1. Register and log in
2. Search for and analyze apps
3. Interpret analysis results (sentiment metrics, risk scores, ML classification)
4. Download PDF and CSV reports
5. Send reports via email
6. Compare multiple apps
7. View analysis history in user dashboard

**Include**:
- Screenshots or ASCII diagrams of UI
- Step-by-step instructions
- Explanation of metrics and terminology
- Tips for best results

**Format**: Create USER_GUIDE.md with numbered procedures and explanations.
```

### 6. Developer Guide

```markdown
Create a developer guide for contributors to the Fraud App Analyzer.

**Task**: Document:
1. Project structure and file organization
2. Blueprint architecture and route handling
3. Adding new analysis modules
4. Extending the sentiment analyzer
5. Custom report templates
6. Adding new API endpoints
7. Database schema and file storage
8. Testing procedures
9. Code style and conventions
10. Contribution workflow (branch, commit, PR)

**Include**:
- Code examples for common tasks
- Architecture diagrams
- API design patterns
- Security best practices

**Format**: Create DEVELOPMENT.md with code samples and architecture diagrams.
```

### 7. Data Model Documentation

```markdown
Document the data models and storage schema for the Fraud App Analyzer.

**Task**: Describe:
1. User model (users.json schema)
2. Message model (messages.json schema)
3. Analysis result model (results/*.json schema)
4. Search log schema (search_logs.csv)
5. Session storage structure
6. File-based storage patterns
7. Data validation and integrity

**Include**:
- JSON schema definitions
- Field descriptions and data types
- Relationships between entities
- Sample data
- Migration considerations

**Format**: Create DATABASE.md with schema definitions and examples.
```

### 8. Deployment Guide

```markdown
Create a production deployment guide for the Fraud App Analyzer.

**Task**: Document:
1. Server requirements and setup
2. Nginx configuration for reverse proxy
3. Gunicorn WSGI server setup
4. Systemd service creation and management
5. SSL certificate provisioning with Certbot
6. Firewall configuration
7. Log management
8. Backup and restore procedures
9. Monitoring and health checks
10. Scaling considerations

**Include**:
- Complete configuration files
- Security hardening steps
- Performance tuning tips
- Maintenance procedures

**Format**: Create DEPLOYMENT.md with production-ready configurations.
```

---

## Output Quality Checklist

When reviewing AI-generated documentation, verify:

- [ ] Technical accuracy matches actual code
- [ ] Commands and code examples are runnable
- [ ] File paths and names are correct
- [ ] Configuration values match project defaults
- [ ] Cross-references link to existing files
- [ ] Markdown syntax is valid
- [ ] Code blocks have language tags
- [ ] Diagrams are clear and accurate
- [ ] Security-sensitive information is handled appropriately
- [ ] Examples use realistic data (not "example.com" for actual domains)

## Continuous Documentation

### When to Update Documentation

1. **Feature additions**: Document new routes, modules, or functionality
2. **Configuration changes**: Update CONFIGURATION.md with new options
3. **Deployment changes**: Reflect infrastructure updates in DEPLOYMENT.md
4. **Bug fixes**: Add to TROUBLESHOOTING.md if issue was non-obvious
5. **API changes**: Update API.md with modified endpoints or parameters
6. **Security updates**: Document new security measures or requirements

### Documentation Workflow

```
1. Code Change Implemented
   ↓
2. Identify affected documentation files
   ↓
3. Use AI prompt with specific context
   ↓
4. Generate updated documentation
   ↓
5. Review for accuracy and clarity
   ↓
6. Commit documentation with code changes
   ↓
7. Update README.md table of contents if needed
```

---

## Example Prompt for Specific Feature

```
I need documentation for a new feature in the Fraud App Analyzer.

**Feature**: Email Delivery System (modules/email_sender.py)

**Context**: The application can now send analysis reports via email using SMTP. The system supports both SSL (port 465) and STARTTLS, falls back to Config values for SMTP settings, and can attach PDF and CSV files.

**Code Reference**:
```python
def send_analysis_email(
    to_email: str,
    subject: str,
    html_body: str,
    pdf_attachment: BytesIO = None,
    csv_attachment: str = None,
    sender_email: str = None,
    sender_password: str = None,
    smtp_server: str = None,
    smtp_port: int = None
):
    # Implementation...
```

**Documentation Needed**:
1. Add section to API.md documenting the `/send_email_report` endpoint
2. Add section to CONFIGURATION.md explaining MAIL_* environment variables
3. Add troubleshooting entry for common SMTP errors
4. Update USER_GUIDE.md with email sending instructions

**Requirements**:
- Include SMTP configuration examples for Gmail, Outlook, SendGrid
- Document security considerations (app passwords, OAuth)
- Provide error message interpretations
- Show example email templates

Generate the documentation sections as separate blocks that I can insert into the respective files.
```

---

## Meta-Documentation

This AI_PROMPT.md file itself should be updated when:
- New documentation patterns are established
- Common documentation requests are identified
- The project structure changes significantly
- New AI capabilities enable better documentation generation

**Last Updated**: February 2026  
**Maintained by**: Development Team
