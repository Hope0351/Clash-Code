![Gachena Banner](https://github.com/user-attachments/assets/8861659d-57db-481a-bb38-dc1edfb47d59)
# 👣 [GACHENA](https://youtu.be/JzglW8pOG2s) - MLH Hackathon
**Detect · Protect · Control Your Digital Footprint**

## 🎥 Demo & Resources

### **Live Demo**
- **Application**: [https://gachena-app.com](https://gachena-app.com/)
- **Demo Video**: [Watch on YouTube](https://youtu.be/JzglW8pOG2s)

### **Presentation Materials**
- **Pitch Deck**: [CANVA](https://www.canva.com/design/DAG-A8hVKxA/bbe7FO5dtep7RjiMZYB6oQ/edit)
- **API Documentation**: [MLH Collection](https://gemini-hackathon-hub-614365371127.us-west1.run.app/)


**Gachena** is an innovative web application that empowers users to take control of their personal data by automating GDPR compliance requests. Connect your Gmail, scan your digital footprint, and send automated data privacy requests to companies holding your information.

## 🏗️ Architecture

![System Architecture](https://i.postimg.cc/zDVpcTk7/gachena-architecture.png)

## ✨ Features

### 🔐 **Smart Authentication**
- **Google OAuth Integration**: Secure login with Gmail account
- **Granular Permission Scopes**: Access only to Gmail read/send capabilities
- **Session Management**: Persistent login with cookie-based authentication

### 🤖 **AI-Powered Analysis**
- **Email Intelligence**: Gemini AI analyzes email content to identify companies and interaction types
- **Company Detection**: Automatically extracts company names and websites from emails
- **Privacy Policy Discovery**: FireCrawl integration finds privacy policy pages from company domains
- **GDPR Contact Extraction**: AI extracts GDPR-specific email addresses from privacy policies

### 📊 **Interactive Dashboard**
- **Visual Data Table**: Review all detected companies with logos and categorization
- **Advanced Filtering**: Customize date ranges and exclude email categories
- **Selection Interface**: Choose companies and request types with checkboxes
- **Real-time Preview**: Preview GDPR emails before sending

### 📧 **Automated Compliance**
- **Dynamic Templates**: Customizable GDPR request templates (Access, Erase, Modify)
- **Bulk Operations**: Send requests to multiple companies simultaneously
- **Email Validation**: Verify extracted email addresses before sending
- **Send Logs**: Track all sent requests with timestamps

## 🛠️ Tech Stack

### **Backend & AI**
- **Python 3.11+**: Core application logic
- **Google Gemini 1.5 Flash**: AI-powered email and document analysis
- **Vertex AI Integration**: Cloud-based AI model hosting
- **Google Gmail API**: Email reading and sending capabilities
- **FireCrawl**: Web scraping for privacy policy discovery

### **Frontend & UI**
- **Streamlit**: Interactive web application framework
- **Pandas**: Data manipulation and table display
- **HTML/CSS**: Custom UI components and styling

### **Authentication & Security**
- **Google OAuth 2.0**: Secure user authentication
- **JWT Tokens**: Session management and security (configurable secret key)
- **Cookie-based Auth**: Persistent user sessions

### **Deployment & DevOps**
- **Docker**: Containerized application (non-root user)
- **Google Container Registry**: Image storage and management
- **Google Cloud Run**: Serverless deployment platform
- **Environment Variables**: Secure configuration management via `.env`

## 🚀 Quick Start

### **Prerequisites**
- Python 3.11 or higher
- Google Cloud Project with Gmail API enabled
- Gemini API access (Vertex AI)
- FireCrawl API key
- Logo.dev API key
- A Google OAuth 2.0 client (download as `credentials.json`)

### **Installation**

1. **Clone the repository**
```bash
git clone https://github.com/Hope0351/Clash-Code.git
cd Clash-Code
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
# Copy the example env file
cp .env.example .env
# Then edit .env with your actual keys
```

Your `.env` file should look like:
```bash
# Google OAuth (credentials.json still needed for OAuth flow)
GOOGLE_REDIRECT_URI=http://localhost:8501/

# API Keys
FIRECRAWL_API_KEY=your_firecrawl_key
LOGODEV_API_KEY=your_logodev_key

# Vertex AI
SERVICE_ACCOUNT_PATH=service_acc.json
VERTEX_PROJECT=your-gcp-project-id
VERTEX_LOCATION=us-central1

# Security - CHANGE THIS IN PRODUCTION!
COOKIE_KEY=your_random_secret_string_here
```

4. **Set up Google OAuth**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create OAuth 2.0 credentials
   - Add `http://localhost:8501` to authorized redirect URIs
   - Download OAuth credentials as `credentials.json` to project root
   - Download Vertex AI service account key as `service_acc.json` to project root

5. **Run the application**
```bash
streamlit run app.py
```

6. **Access the application**
Open your browser and navigate to `http://localhost:8501`

## 📖 Usage Guide

### **Step 1: Authenticate**
- Click "Sign in with Google" in the sidebar
- Grant necessary permissions for Gmail access
- Your profile will load with personalized greeting

### **Step 2: Scan Your Inbox**
- Click "Scan Inbox" to analyze recent emails
- Toggle **Demo Mode** to use pre-loaded sample data (no API calls)
- Adjust date range and filters in "Advanced Options"
- View detected companies with logos and categories

### **Step 3: Select Companies**
- Browse the interactive table of detected companies
- Select companies using checkboxes
- Choose request type for each: Access, Erase, or Modify

### **Step 4: Send Requests**
- Click "Run Bot" to process selections
- Enable "Preview Email" to review before sending (single selection)
- Disable preview for bulk send to multiple companies
- Track success notifications for each sent request

## 🔧 Configuration

### **API Keys Setup**

| Service | How to Obtain | Usage |
|---------|---------------|-------|
| **FireCrawl** | Sign up at [firecrawl.dev](https://firecrawl.dev) | Privacy policy discovery |
| **Logo.dev** | Request access at [logo.dev](https://logo.dev) | Company logo retrieval |
| **Gemini AI** | Google Cloud Vertex AI console | Email and document analysis |
| **Gmail API** | Google Cloud Console API Library | Email reading and sending |

### **Environment Variables**

See [`.env.example`](.env.example) for the full list of configurable options:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FIRECRAWL_API_KEY` | Yes | - | FireCrawl API key |
| `LOGODEV_API_KEY` | Yes | - | Logo.dev API key |
| `SERVICE_ACCOUNT_PATH` | Yes | `service_acc.json` | Path to Vertex AI service account JSON |
| `VERTEX_PROJECT` | Yes | - | Your GCP project ID |
| `COOKIE_KEY` | Yes | - | JWT signing secret (use a strong random string) |
| `GOOGLE_REDIRECT_URI` | No | `http://localhost:8501/` | OAuth redirect URI |
| `GEMINI_MODEL` | No | `gemini-1.5-flash-001` | Vertex AI model name |
| `MAX_GEMINI_RETRIES` | No | `3` | Max retries on rate limit (429) |
| `GEMINI_RETRY_DELAY` | No | `60` | Base delay in seconds between retries |
| `COOKIE_EXPIRY_DAYS` | No | `30` | Days until auth cookie expires |

## 🐳 Docker Deployment

### **Build Docker Image**
```bash
docker build -t gachena-app .
```

### **Run Container**
```bash
docker run -p 8501:8501 \
  -v $(pwd)/credentials.json:/app/credentials.json:ro \
  -v $(pwd)/service_acc.json:/app/service_acc.json:ro \
  -e FIRECRAWL_API_KEY=your_key \
  -e LOGODEV_API_KEY=your_key \
  -e VERTEX_PROJECT=your-project \
  -e COOKIE_KEY=your_random_secret \
  gachena-app
```

### **Docker Compose**
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

## ☁️ Cloud Deployment

### **Google Cloud Run**
```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/your-project/gachena

# Deploy to Cloud Run
gcloud run deploy gachena \
  --image gcr.io/your-project/gachena \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="FIRECRAWL_API_KEY=$FIRECRAWL_KEY,VERTEX_PROJECT=$PROJECT_ID,COOKIE_KEY=$SECRET"
```

## 📁 Project Structure

```
Clash-Code/
├── app.py                 # Main Streamlit application
├── utils.py               # Core business logic, AI, Gmail API
├── streamlit_auth.py      # Google OAuth authentication module
├── streamlit_auth_cookie.py # JWT cookie session management
├── requirements.txt       # Pinned Python dependencies
├── Dockerfile             # Container config (non-root user)
├── .dockerignore          # Docker build exclusions
├── .gitignore             # Git exclusions (secrets)
├── .env.example           # Environment variable template
├── index.html             # Landing page (particles.js animation)
├── diagnostic.py          # OAuth setup debug utility
├── gemini_processed_emails.json # Sample email data for demo mode
├── LICENSE                # MIT License
└── README.md              # This file
```

## 🧪 Testing

### **Run Diagnostic Tests**
```bash
python diagnostic.py
```

### **Test Authentication Flow**
```bash
python -c "from utils import google_authenticate; auth = google_authenticate(); print('Auth module loaded successfully')"
```

### **Check API Connections**
```bash
# Test FireCrawl connection
curl -X POST https://api.firecrawl.dev/v1/scrape \
  -H "Authorization: Bearer $FIRECRAWL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

## 🔒 Security & Privacy

### **Data Protection**
- **No Data Storage**: Emails are processed in memory, not stored
- **End-to-End Encryption**: All API communications use HTTPS
- **Minimal Permissions**: Only requested Gmail scopes are accessed
- **Session Isolation**: User data is never shared between sessions
- **Configurable Secrets**: All sensitive keys loaded from environment variables

### **Compliance**
- **GDPR Compliant**: Helps users exercise GDPR rights
- **Transparent Operations**: Clear indication of all actions taken
- **User Consent**: Explicit permission for each email scan
- **Right to Revoke**: Users can disconnect access at any time

## 🤝 Contributing

We welcome contributions! Here's how:

1. **Fork the repository**
2. **Create a feature branch**
```bash
git checkout -b feature/amazing-feature
```
3. **Commit your changes**
```bash
git commit -m 'Add amazing feature'
```
4. **Push to the branch**
```bash
git push origin feature/amazing-feature
```
5. **Open a Pull Request**

## 👥 Team

**Gachena** was developed by a team of three during the MLH Hackathon:
- **Abdi Megersa** - Backend & AI Integration
- **Eba Alemu** - Frontend & UI Design
- **Osama Hasan** - DevOps & Deployment

## 📞 Support

For issues, questions, or support:
- **GitHub Issues**: [Create an issue](https://github.com/Hope0351/Clash-Code/issues)

## ⭐ Acknowledgements

- **MLH Hackathon** for the opportunity and platform
- **Google Cloud** for AI and infrastructure services
- **Streamlit** for the amazing framework
- **FireCrawl & Logo.dev** for their APIs
- All open-source contributors whose work made this possible

---

<div align="center">

**Gachena** - Detect, Protect, Control Your Digital Footprint

[![GitHub stars](https://img.shields.io/github/stars/Hope0351/Clash-Code?style=social)](https://github.com/Hope0351/Clash-Code)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

*Built with ❤️ during MLH Hackathon*

</div>