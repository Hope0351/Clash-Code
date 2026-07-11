# GACHENA — Technical Documentation

> **"Gachena" means Shield in Afaan Oromo.** This document covers the complete technical architecture, configuration, and development guide for the GACHENA GDPR compliance platform.

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
10. [UI Design System](#ui-design-system)
11. [Deployment Guide](#deployment-guide)
12. [Troubleshooting](#troubleshooting)
13. [Development Guide](#development-guide)

---

## Overview

GACHENA is a GDPR compliance automation tool built with Streamlit that helps users exercise their data rights under the European General Data Protection Regulation (GDPR). The application scans a user's Gmail inbox, identifies companies holding their personal data through AI-powered email analysis, and automates the process of sending GDPR compliance requests (access, modification, or erasure) to those companies.

The application was built during the MLH Clash of Code hackathon and demonstrates integration between multiple Google Cloud services, third-party APIs, and modern Python web frameworks. It operates in two modes:

- **Demo Mode** (default): Fully functional with sample data — no API keys or credentials needed
- **Live Mode**: Connects to real Gmail accounts using Google Gemini AI for email classification

### Key Capabilities

- **Email Scanning**: Fetches emails from Gmail categories (Promotions, Updates) using the Gmail API
- **AI Classification**: Uses Gemini 1.5 Flash to classify each email's interaction type and extract company information
- **Company Discovery**: Identifies companies from email metadata, deduplicates results, retrieves logos via Logo.dev
- **GDPR Contact Finding**: Uses FireCrawl to discover privacy policy pages, extracts GDPR contact emails using AI
- **Automated Requests**: Generates and sends GDPR compliance emails using templates aligned with Articles 15, 16, and 17

---

## System Architecture

```
┌──────────────────────────────────────────────────────────┐
│                   Streamlit Frontend                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ Landing  │  │ Dashboard│  │  Data    │  │  Email   │ │
│  │ Page     │  │ + Stats  │  │  Table   │  │  Preview │ │
│  │(particles)│  │(4 steps)│  │(editor)  │  │(dialog)  │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────┴─────────────────────────────────┐
│                      app.py (Entry)                       │
│  Page config · Demo mode toggle · Auth routing · Scan    │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────┴─────────────────────────────────┐
│                  utils.py (Business Logic)                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │  Gmail   │ │  Gemini  │ │ FireCrawl│ │ Logo.dev │    │
│  │  API     │ │  AI      │ │  Scrape  │ │  Logos   │    │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │
└──────────────────────────────────────────────────────────┘
         │              │               │             │
    Gmail API    Vertex AI      FireCrawl API    Logo.dev API
```

### Data Flow

1. **Authentication**: User authenticates via Google OAuth (live) or auto-authenticates as "Demo User" (demo)
2. **Email Fetching**: Emails fetched from Gmail categories (live) or loaded from `gemini_processed_emails.json` (demo)
3. **AI Classification**: Each email is sent to Gemini 1.5 Flash with a structured JSON output schema
4. **Data Presentation**: Results are deduplicated and displayed in an interactive table with stat counters and logos
5. **GDPR Request**: User selects companies and request types; the app finds privacy policy URLs via FireCrawl, extracts GDPR contact emails, and sends formatted emails

---

## Getting Started

### Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.12+ | Runtime |
| pip | Latest | Package manager |

### Demo Mode Installation

```bash
git clone https://github.com/Hope0351/Clash-Code.git
cd Clash-Code
pip install streamlit pandas requests python-dotenv pyjwt extra-streamlit-components
streamlit run app.py
```

Open `http://localhost:8501`. Demo mode is enabled by default — click **Scan Inbox** to see it in action.

### Live Mode Setup

1. **Google Cloud Console**:
   - Enable Gmail API and Vertex AI API
   - Create OAuth 2.0 credentials (download as `credentials.json`)
   - Create a service account key (download as `service_acc.json`)
   - Add `http://localhost:8501/` to authorized redirect URIs

2. **API Keys**:
   - FireCrawl: [firecrawl.dev](https://firecrawl.dev)
   - Logo.dev: [logo.dev](https://logo.dev) (optional)

3. **Configure**:
```bash
cp .env.example .env
# Edit .env with your keys
pip install -r requirements.txt
streamlit run app.py
# Toggle Demo Mode OFF
```

---

## Demo Mode

Demo mode is the default experience. It bypasses all authentication and external API requirements, using a local JSON file with 18 pre-classified sample emails from 13 unique companies.

### How It Works

1. **Skips OAuth**: Creates a mock user session ("Demo User") — no `credentials.json` needed
2. **Loads local data**: `gemini_processed_emails.json` instead of Gmail API calls
3. **Shows full dashboard**: Data table, selection, request type dropdowns, and Run Bot controls all work
4. **Limits email sending**: Preview works, but actual sending is disabled (no Gmail service)

---

## Configuration Reference

### Required for Live Mode

| Variable | Example | Description |
|----------|---------|-------------|
| `FIRECRAWL_API_KEY` | `fc-xxxxxxxxxxxx` | FireCrawl API key |
| `VERTEX_PROJECT` | `my-gcp-project-123` | GCP project ID |
| `SERVICE_ACCOUNT_PATH` | `service_acc.json` | Vertex AI service account key |

### Required for Production

| Variable | Example | Description |
|----------|---------|-------------|
| `COOKIE_KEY` | `a1b2c3d4e5f6...` | JWT signing secret (strong random string) |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_REDIRECT_URI` | `http://localhost:8501/` | OAuth callback URL |
| `COOKIE_NAME` | `gachena_auth` | Browser cookie name |
| `COOKIE_EXPIRY_DAYS` | `30` | Session lifetime in days |
| `GEMINI_MODEL` | `gemini-1.5-flash-001` | Vertex AI model |
| `MAX_GEMINI_RETRIES` | `3` | Max retries on rate limit |
| `GEMINI_RETRY_DELAY` | `60` | Seconds between retries |
| `LOGODEV_API_KEY` | (empty) | Logo.dev API key for logos |
| `LOGO_TIMEOUT` | `5` | HTTP timeout for logo URL check |
| `VERTEX_LOCATION` | `us-central1` | Vertex AI region |

---

## Code Architecture

### File Structure

```
app.py                    # Entry point - GACHENA UI, page config, routing
utils.py                  # Business logic - AI, Gmail, data processing (lazy imports)
streamlit_auth.py         # Google OAuth 2.0 authentication class
streamlit_auth_cookie.py  # JWT cookie-based session management
index.html                # Landing page with particles.js animation
gemini_processed_emails.json  # Demo data (18 sample emails)
requirements.txt          # Pinned Python dependencies
Dockerfile                # Container (non-root user, GACHENA dark theme)
.env.example              # Environment variable template
.gitignore                # Git exclusions
.dockerignore             # Docker build exclusions
```

### Lazy Import System

GACHENA uses a **lazy import system** because the two modes have vastly different dependency requirements:

- **Demo mode**: `streamlit`, `pandas`, `requests`, `python-dotenv`, `pyjwt`, `extra-streamlit-components`
- **Live mode**: adds `google-auth`, `google-auth-oauthlib`, `google-api-python-client`, `vertexai`, `langchain-google-vertexai`, `langchain-community`, `unstructured`

Helper functions import heavy modules only when called:

```python
def _import_vertexai():
    import vertexai
    return vertexai
```

This means the app starts in demo mode even if Vertex AI or Gmail libraries aren't installed.

### Demo Mode Bypass

In `app.py`, the demo mode toggle is rendered **before** authentication. When enabled, `_activate_demo_session()` sets session state variables directly, completely bypassing `google_authenticate()`.

---

## Authentication System

### OAuth Flow (Live Mode)

Scopes: `openid`, `userinfo.profile`, `userinfo.email`, `gmail.readonly`, `gmail.send`

1. `google_authenticate()` creates an `Authenticate` instance
2. Checks for existing JWT session cookie
3. If no cookie, shows "Sign in with Google" button
4. After Google consent, exchanges code for tokens
5. Fetches user info, stores in `st.session_state`
6. Sets JWT cookie for persistent sessions

### Cookie-based Sessions

`CookieHandler` in `streamlit_auth_cookie.py` manages sessions using JWT tokens in browser cookies. Contains name, email, picture, and OAuth ID, signed with `COOKIE_KEY`. Expires after `COOKIE_EXPIRY_DAYS` (default 30).

### Graceful Degradation

If `credentials.json` is missing, shows: "Google OAuth credentials file not found. Place your `credentials.json` in the project root, or enable **Demo Mode** above."

---

## AI Pipeline

### Email Classification (Live Mode)

1. **Fetch**: Email retrieved via Gmail API (subject, sender, date, body)
2. **Body Extraction**: `_extract_body()` recursively navigates multipart MIME structures
3. **Truncation**: Content truncated to 6,000 characters
4. **Gemini Classification**: Structured JSON output schema:

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

5. **Retry Logic**: On 429/RESOURCE_EXHAUSTED, retries up to `MAX_GEMINI_RETRIES` with exponential backoff

### Category Definitions

- **Interacted**: Triggered by user action (order confirmations, password resets, transactions)
- **Not Interacted**: Not triggered by user (newsletters, promotions, marketing)

### GDPR Contact Extraction

1. FireCrawl maps company website searching for "privacy" pages
2. URL validated with HEAD request
3. Privacy page loaded via `UnstructuredURLLoader`
4. Gemini AI extracts GDPR contact email
5. Email validated with regex

---

## GDPR Email Templates

Three templates corresponding to GDPR data subject rights:

### Article 15 — Right of Access (Request Data)
Requests a copy of all personal data, processing purposes, third-party sharing, and data sources.

### Article 16 — Right to Rectification (Modify Data)
Requests correction of inaccurate or incomplete personal data.

### Article 17 — Right to Erasure (Erase Data)
Requests permanent deletion of all personal data.

All templates are addressed to "Dear Data Protection Officer" and cite specific GDPR articles.

---

## UI Design System

### Brand Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `GACHENA_PRIMARY` | `#0D9488` | Buttons, accents, links |
| `GACHENA_DARK` | `#0F172A` | Page background |
| `GACHENA_CARD` | `#1E293B` | Card backgrounds |
| `GACHENA_BORDER` | `#334155` | Borders, dividers |
| `GACHENA_TEXT` | `#F1F5F9` | Primary text |
| `GACHENA_MUTED` | `#94A3B8` | Secondary text |
| `GACHENA_ACCENT` | `#2DD4BF` | Highlights, shield icon |
| `GACHENA_SUCCESS` | `#22C55E` | Success states |
| `GACHENA_WARNING` | `#F59E0B` | Warning states |
| `GACHENA_DANGER` | `#EF4444` | Error states |

### Component Patterns

- **Step Badges**: Teal gradient pills (`STEP N: Title`) for section headers
- **Stat Grid**: 3-column CSS grid with hover animations for scan statistics
- **Instruction Cards**: 4-column grid with numbered circles and descriptions
- **GDPR Badges**: Color-coded inline badges (blue Art.15, green Art.16, red Art.17)
- **Sidebar**: Dark gradient with centered branding, user profile, and logout button
- **Landing Page**: Particles.js with Inter font, floating shield animation, teal particles

### Custom CSS

All styling is injected via `st.markdown(CUSTOM_CSS, unsafe_allow_html=True)` at the top of `app.py`. Streamlit's default header, footer, and menu are hidden for a clean branded experience.

---

## Deployment Guide

### Docker

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

The Dockerfile uses:
- `python:3.12-slim` base image
- Non-root `appuser` for security
- GACHENA dark theme via Streamlit CLI flags
- Port 8080 (map to 8501 on host)

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
Install all dependencies: `pip install -r requirements.txt`. For demo mode, only `streamlit`, `pandas`, `requests`, `python-dotenv`, `pyjwt`, `extra-streamlit-components` are needed.

### "Demo data file not found"
Ensure you run `streamlit run app.py` from the project root directory.

### Google OAuth button not appearing
Place `credentials.json` (OAuth client) in the project root, or enable Demo Mode.

### Gemini rate limit errors (429)
The app has built-in retry with exponential backoff. Increase `GEMINI_RETRY_DELAY` or reduce scan count.

### Logos not showing
Set `LOGODEV_API_KEY` in your `.env`. This is optional — the app works without logos.

### FireCrawl returns no privacy URLs
Verify your API key. Some websites may not have discoverable privacy policy pages.

---

## Development Guide

### Running Tests

```bash
python -c "import app; print('App module loaded OK')"
python -c "from utils import google_authenticate; print('Auth module loaded OK')"
```

### Adding New GDPR Templates

Edit `get_email_template()` in `utils.py`. Each template needs `subject` and `body` with `{company_name}` and `{user_name}` placeholders.

### Modifying the AI Schema

The classification schema is in `classify_email_with_gemini()` in `utils.py`. Update both `properties` and `required` arrays when adding fields.

### Project Conventions

- **Environment variables**: All secrets via `os.getenv()` with sensible defaults
- **Error handling**: External API functions catch exceptions, return graceful fallbacks
- **No hardcoded secrets**: Never commit API keys or tokens
- **Demo-first**: New features should work in demo mode without external dependencies
- **Lazy imports**: New live-mode deps should use the lazy import pattern