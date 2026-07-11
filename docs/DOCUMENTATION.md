# Gachena - Technical Documentation

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Getting Started](#getting-started)
4. [Demo Mode](#demo-mode)
5. [Configuration Reference](#configuration-reference)
6. [Code Architecture](#code-architecture)
7. [Authentication System](#authentication-system)
8. [AI Pipeline](#ai-pipeline)
9. [GDPR Email Templates](#gdpr-email-templates)
10. [Deployment Guide](#deployment-guide)
11. [Troubleshooting](#troubleshooting)
12. [Development Guide](#development-guide)

---

## Overview

Gachena is a GDPR compliance automation tool built with Streamlit that helps users exercise their data rights under the European General Data Protection Regulation (GDPR). The application scans a user's Gmail inbox, identifies companies holding their personal data through AI-powered email analysis, and automates the process of sending GDPR compliance requests (access, modification, or erasure) to those companies.

The application was built during the MLH Clash of Code hackathon and demonstrates integration between multiple Google Cloud services, third-party APIs, and modern Python web frameworks. It is designed to work in two modes: a fully functional demo mode that requires no external dependencies, and a live mode that connects to real Gmail accounts and uses Google Gemini AI for email classification.

### Key Capabilities

- **Email Scanning**: Fetches emails from Gmail categories (Promotions, Updates) using the Gmail API
- **AI Classification**: Uses Gemini 1.5 Flash to classify each email's interaction type (interacted vs. not interacted) and extract company information
- **Company Discovery**: Identifies companies from email metadata and content, deduplicates results, and retrieves company logos via Logo.dev
- **GDPR Contact Finding**: Uses FireCrawl to discover privacy policy pages, then extracts GDPR contact emails using AI analysis of the policy text
- **Automated Requests**: Generates and sends GDPR compliance emails using pre-built templates aligned with Articles 15, 16, and 17 of the GDPR

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Streamlit Frontend                          │
│  ┌──────────┐  ┌──────────────┐  ┌──────────┐  ┌───────────────┐   │
│  │  Landing  │  │   Dashboard  │  │  Data     │  │  Email        │   │
│  │  Page     │  │   + Toggle   │  │  Table    │  │  Preview      │   │
│  │ (particles)│  │  (demo/live)│  │ (editor)  │  │  Dialog       │   │
│  └──────────┘  └──────────────┘  └──────────┘  └───────────────┘   │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────────────┐
│                         app.py (Main Entry)                         │
│  - Page configuration                                               │
│  - Demo mode toggle (before auth)                                   │
│  - Route: auth required vs. demo bypass                             │
│  - Orchestrate scan → display → bot flow                            │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────────────┐
│                         utils.py (Business Logic)                   │
│  ┌────────────┐  ┌──────────────┐  ┌───────────┐  ┌──────────────┐  │
│  │  Gmail     │  │  Gemini AI   │  │ FireCrawl │  │  Logo.dev    │  │
│  │  Fetch +   │  │  Classify +  │  │  Privacy  │  │  Company     │  │
│  │  Send      │  │  Extract     │  │  URL Find │  │  Logos       │  │
│  └────────────┘  └──────────────┘  └───────────┘  └──────────────┘  │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────────────┐
│                    External Services (Live Mode Only)                │
│  ┌──────────┐  ┌──────────────┐  ┌───────────┐  ┌──────────────┐  │
│  │ Gmail    │  │ Vertex AI    │  │ FireCrawl │  │  Logo.dev    │  │
│  │ API      │  │ (Gemini 1.5) │  │  API      │  │  API         │  │
│  └──────────┘  └──────────────┘  └───────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Authentication**: User authenticates via Google OAuth (live mode) or auto-authenticates as "Demo User" (demo mode)
2. **Email Fetching**: Emails are fetched from Gmail categories (live) or loaded from `gemini_processed_emails.json` (demo)
3. **AI Classification**: Each email is sent to Gemini AI with a structured JSON output schema to extract company name, interaction type, and website
4. **Data Presentation**: Results are deduplicated and displayed in an interactive data table with company logos
5. **GDPR Request**: User selects companies and request types, the app finds privacy policy URLs via FireCrawl, extracts GDPR contact emails, and sends formatted emails

---

## Getting Started

### Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.12+ | Runtime |
| pip | Latest | Package manager |

### Installation

```bash
# Clone the repository
git clone https://github.com/Hope0351/Clash-Code.git
cd Clash-Code

# Install all dependencies
pip install -r requirements.txt

# Run the app (demo mode works immediately)
streamlit run app.py
```

Open `http://localhost:8501` in your browser. Demo mode is enabled by default.

### For Live Mode

In addition to the base dependencies, live mode requires:

1. **Google Cloud Console** setup:
   - Enable Gmail API
   - Enable Vertex AI API
   - Create OAuth 2.0 credentials (download as `credentials.json`)
   - Create a service account key (download as `service_acc.json`)
   - Add `http://localhost:8501` to authorized redirect URIs

2. **Third-party API keys**:
   - FireCrawl: Sign up at [firecrawl.dev](https://firecrawl.dev)
   - Logo.dev: Request access at [logo.dev](https://logo.dev)

3. **Environment configuration**:
```bash
cp .env.example .env
# Edit .env with your keys
```

---

## Demo Mode

Demo mode is the default way to experience Gachena. It bypasses all authentication and external API requirements, using a local JSON file with 18 pre-classified sample emails instead.

### How It Works

When demo mode is active (the default), the application:

1. **Skips OAuth entirely**: Instead of loading Google OAuth credentials and running the authentication flow, the app creates a mock user session with the name "Demo User". No `credentials.json` file is needed.

2. **Loads local data**: Clicking "Scan Inbox" reads from `gemini_processed_emails.json` instead of making Gmail API calls. This file contains 18 emails from 13 unique companies, each pre-classified with company name, interaction type, and website URL.

3. **Shows the full dashboard**: The data table, company selection, request type dropdowns, and Run Bot controls all work exactly as they do in live mode.

4. **Limits email sending**: The preview dialog will display the GDPR email that would be sent, but actual sending is disabled because no Gmail service is connected.

### Switching to Live Mode

Toggle "Demo Mode (no Google login required)" OFF in the main interface. The app will then require a valid `credentials.json` file and will attempt Google OAuth authentication. You must also configure API keys in `.env` for the full pipeline to work.

---

## Configuration Reference

All configuration is done through environment variables, loaded from a `.env` file in the project root. A `.env.example` template is provided.

### Required for Live Mode

| Variable | Example | Description |
|----------|---------|-------------|
| `FIRECRAWL_API_KEY` | `fc-xxxxxxxxxxxx` | API key for FireCrawl privacy policy discovery |
| `VERTEX_PROJECT` | `my-gcp-project-123` | Google Cloud project ID for Vertex AI |
| `SERVICE_ACCOUNT_PATH` | `service_acc.json` | Path to Vertex AI service account key file |

### Required for Production

| Variable | Example | Description |
|----------|---------|-------------|
| `COOKIE_KEY` | `a1b2c3d4e5f6...` | JWT signing secret for session cookies. Must be a strong random string. |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_REDIRECT_URI` | `http://localhost:8501/` | OAuth callback URL |
| `COOKIE_NAME` | `gachena_auth` | Browser cookie name for sessions |
| `COOKIE_EXPIRY_DAYS` | `30` | Session cookie lifetime in days |
| `GEMINI_MODEL` | `gemini-1.5-flash-001` | Vertex AI model for classification |
| `MAX_GEMINI_RETRIES` | `3` | Maximum retries on rate limit (429) |
| `GEMINI_RETRY_DELAY` | `60` | Seconds between retry attempts (multiplied by attempt number) |
| `LOGODEV_API_KEY` | (empty) | Logo.dev API key for company logo display |
| `LOGO_TIMEOUT` | `5` | HTTP timeout for logo URL validation |
| `VERTEX_LOCATION` | `us-central1` | Vertex AI region |

---

## Code Architecture

### File Structure

```
app.py                    # Entry point - Streamlit app, page config, routing
utils.py                  # Business logic - AI, Gmail, data processing (lazy imports)
streamlit_auth.py         # Google OAuth 2.0 authentication class
streamlit_auth_cookie.py  # JWT cookie-based session management
index.html                # Landing page with particles.js animation
gemini_processed_emails.json  # Demo data (18 sample emails)
requirements.txt          # Pinned Python dependencies
Dockerfile                # Container configuration (non-root user)
.env.example              # Environment variable template
.gitignore                # Git exclusions for secrets
.dockerignore             # Docker build exclusions
```

### Lazy Import System

One of the most important architectural decisions in Gachena is the **lazy import system**. The application has two modes of operation with vastly different dependency requirements:

- **Demo mode** requires only: `streamlit`, `pandas`, `requests`, `python-dotenv`, `pyjwt`, `extra-streamlit-components`
- **Live mode** additionally requires: `google-auth`, `google-auth-oauthlib`, `google-api-python-client`, `vertexai`, `langchain-google-vertexai`, `langchain-community`, `unstructured`

Rather than requiring all dependencies to be installed, `utils.py` defines helper functions that import heavy modules only when they are actually called:

```python
def _import_vertexai():
    import vertexai
    return vertexai

def _import_generative_model():
    from vertexai.generative_models import GenerativeModel, GenerationConfig
    return GenerativeModel, GenerationConfig
```

This means the app can start and run in demo mode even if Vertex AI, the Gmail API libraries, or FireCrawl's dependencies are not installed. The import only fails if a user tries to use a live-mode feature without the required packages.

Similarly, `streamlit_auth.py` uses lazy imports for `google_auth_oauthlib` and `googleapiclient`, so the authentication module can be loaded without those packages present.

### Demo Mode Bypass

In `app.py`, the demo mode toggle is rendered **before** any authentication logic. When enabled, `_activate_demo_session()` sets the necessary session state variables directly, completely bypassing the `google_authenticate()` function and its dependency chain.

---

## Authentication System

### OAuth Flow (Live Mode)

The authentication system uses Google OAuth 2.0 with the following scopes:

- `openid` - Basic identity verification
- `userinfo.profile` - User's name and profile picture
- `userinfo.email` - User's email address
- `gmail.readonly` - Read emails from inbox
- `gmail.send` - Send GDPR request emails

The flow works as follows:

1. `google_authenticate()` in `utils.py` creates an `Authenticate` instance from `streamlit_auth.py`
2. The `Authenticate` class checks for an existing session cookie (JWT)
3. If no cookie exists, it displays a "Sign in with Google" button
4. Clicking the button redirects to Google's consent screen
5. After approval, Google redirects back with an authorization code
6. `check_authentification()` exchanges the code for access tokens
7. User info is fetched and stored in `st.session_state`
8. A JWT cookie is set for persistent sessions

### Cookie-based Sessions

The `CookieHandler` class in `streamlit_auth_cookie.py` manages persistent sessions using JWT tokens stored in browser cookies. The token contains the user's name, email, profile picture URL, and OAuth ID, signed with the `COOKIE_KEY` secret. Sessions expire after `COOKIE_EXPIRY_DAYS` (default 30 days).

### Graceful Degradation

If `credentials.json` is missing, the authentication system does not crash. Instead, it displays a clear warning message: "Google OAuth credentials file not found. Place your `credentials.json` in the project root, or enable Demo Mode above." This allows users to always fall back to demo mode.

---

## AI Pipeline

### Email Classification (Live Mode)

Each email goes through the following pipeline:

1. **Fetch**: The email is retrieved from Gmail via the API, including subject, sender, date, and body content
2. **Body Extraction**: `_extract_body()` recursively navigates multipart MIME structures, preferring plain text over HTML
3. **Truncation**: Email content is truncated to 6,000 characters to manage token usage
4. **Gemini Classification**: The content is sent to Gemini 1.5 Flash with a structured JSON output schema:

```json
{
  "type": "OBJECT",
  "properties": {
    "company_name": {"type": "STRING"},
    "category": {"type": "STRING", "enum": ["interacted", "not interacted"]},
    "website": {"type": "STRING"}
  },
  "required": ["company_name", "category", "website"]
}
```

5. **Retry Logic**: On rate limit errors (429/RESOURCE_EXHAUSTED), the request is retried up to `MAX_GEMINI_RETRIES` times with exponential backoff (`delay * attempt_number`)

### Category Definitions

- **Interacted**: Emails triggered by a user's direct action (order confirmations, password resets, transaction notifications, login alerts, shipping confirmations)
- **Not Interacted**: Emails not triggered by user action (newsletters, promotional campaigns, marketing content, product announcements)

### GDPR Contact Extraction

When a user clicks "Run Bot", the app needs to find where to send the GDPR request:

1. **Privacy Policy Discovery**: FireCrawl API maps the company's website searching for pages containing "privacy"
2. **URL Validation**: Each discovered URL is checked with a HEAD request to verify it returns 200
3. **Email Extraction**: The privacy page content is loaded using `UnstructuredURLLoader`, then analyzed by Gemini AI to extract the GDPR/data protection contact email
4. **Email Validation**: The extracted email is validated with a regex pattern before use

---

## GDPR Email Templates

The application includes three pre-built email templates corresponding to the three main GDPR data subject rights:

### Article 15 - Right of Access (Request Data)

Requests a copy of all personal data the company holds, including categories of data, processing purposes, third-party sharing, and data sources.

### Article 16 - Right to Rectification (Modify Data)

Requests correction of inaccurate or incomplete personal data. The user is expected to specify which data needs updating in the template body.

### Article 17 - Right to Erasure (Erase Data)

Requests permanent deletion of all personal data. If the request cannot be fully fulfilled, the company must explain why and offer alternatives.

All templates are formatted as professional letters addressed to "Dear Data Protection Officer" and signed with the user's name. They reference specific GDPR articles to ensure legal weight.

---

## Deployment Guide

### Docker

The application includes a Dockerfile configured for production:

- **Base image**: `python:3.12-slim`
- **Security**: Runs as non-root `appuser`
- **System dependencies**: Includes `build-essential`, `libxml2-dev`, `libxslt1-dev` for the `unstructured` library
- **Port**: 8080 (map to 8501 on host)
- **Theme**: Dark theme with green (`#77dd77`) primary color

```bash
docker build -t gachena-app .
docker run -p 8501:8080 \
  -v $(pwd)/credentials.json:/app/credentials.json:ro \
  -v $(pwd)/service_acc.json:/app/service_acc.json:ro \
  -e FIRECRAWL_API_KEY=your_key \
  -e VERTEX_PROJECT=your-project \
  -e COOKIE_KEY=your_random_secret \
  gachena-app
```

### Docker Compose

```yaml
version: '3.8'
services:
  gachena:
    build: .
    ports:
      - "8501:8080"
    volumes:
      - ./credentials.json:/app/credentials.json:ro
      - ./service_acc.json:/app/service_acc.json:ro
    environment:
      - FIRECRAWL_API_KEY=${FIRECRAWL_API_KEY}
      - LOGODEV_API_KEY=${LOGODEV_API_KEY}
      - VERTEX_PROJECT=${VERTEX_PROJECT}
      - COOKIE_KEY=${COOKIE_KEY}
    restart: unless-stopped
```

### Google Cloud Run

```bash
gcloud builds submit --tag gcr.io/your-project/gachena
gcloud run deploy gachena \
  --image gcr.io/your-project/gachena \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="FIRECRAWL_API_KEY=$KEY,VERTEX_PROJECT=$PROJECT,COOKIE_KEY=$SECRET"
```

---

## Troubleshooting

### App crashes on startup

**Symptom**: The app fails to start or shows an error page immediately.

**Cause**: A required dependency is missing. Even though the lazy import system prevents most import errors, if you have partially installed dependencies, some modules may fail.

**Fix**: Install all dependencies with `pip install -r requirements.txt`. For demo mode, you only need the base packages: `streamlit`, `pandas`, `requests`, `python-dotenv`, `pyjwt`, `extra-streamlit-components`.

### "Demo data file not found"

**Symptom**: Clicking "Scan Inbox" in demo mode shows "No emails were found."

**Cause**: The `gemini_processed_emails.json` file is not in the same directory as `app.py`, or the working directory is wrong.

**Fix**: Ensure you run `streamlit run app.py` from the project root directory, not from a subdirectory.

### Google OAuth button not appearing

**Symptom**: No "Sign in with Google" button shows up, or a warning about missing credentials appears.

**Cause**: The `credentials.json` OAuth client file is not in the project root.

**Fix**: Download OAuth 2.0 credentials from Google Cloud Console and save as `credentials.json`. Or enable Demo Mode to bypass authentication.

### Gemini rate limit errors

**Symptom**: "429 Resource Exhausted" or "Quota exceeded" errors during email scanning.

**Fix**: The app has built-in retry logic with exponential backoff. If you consistently hit rate limits, increase `GEMINI_RETRY_DELAY` in your `.env` file, or reduce `MAX_EMAILS_SCAN` to process fewer emails per scan.

### Logos not showing

**Symptom**: The logo grid area is empty after scanning.

**Cause**: The `LOGODEV_API_KEY` environment variable is not set.

**Fix**: This is optional. To display company logos, sign up at [logo.dev](https://logo.dev) and set the API key in your `.env`.

### FireCrawl returns no privacy URLs

**Symptom**: "No GDPR contact email found" for all companies.

**Cause**: FireCrawl may not be able to map certain websites, or the API key is invalid.

**Fix**: Verify your FireCrawl API key is active. Some websites (especially small ones) may not have discoverable privacy policy pages through automated means.

---

## Development Guide

### Running Tests

The application includes basic diagnostic utilities. To verify the app loads correctly:

```bash
python -c "import app; print('App module loaded OK')"
```

To test authentication module loading:

```bash
python -c "from utils import google_authenticate; print('Auth module loaded OK')"
```

### Adding New GDPR Templates

Edit the `get_email_template()` function in `utils.py`. Each template needs a `subject` and `body` key. The body should use `{company_name}` and `{user_name}` as format placeholders:

```python
"New Template": {
    "subject": "Your Subject Here",
    "body": """Dear Data Protection Officer,

    Your email body with {company_name} and {user_name} placeholders.
    """
}
```

Then add the option to the `dropdown_options` list in `display_df()` within `utils.py`.

### Modifying the AI Classification Schema

The classification schema is defined in `classify_email_with_gemini()` in `utils.py`. The `response_schema` dict must have matching keys in both `properties` and `required` arrays. If you add a new property, add it to both places.

### Project Conventions

- **Environment variables**: All secrets and configuration must go through `os.getenv()` with sensible defaults
- **Error handling**: Functions that interact with external APIs should catch exceptions and return graceful fallbacks (empty strings, None, or empty lists)
- **No hardcoded secrets**: The codebase must never contain API keys, tokens, or passwords
- **Demo-first design**: Any new feature should work in demo mode without external dependencies
- **Lazy imports**: New dependencies for live-mode features should use the lazy import pattern to avoid breaking demo mode