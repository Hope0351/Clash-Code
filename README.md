![Gachena Banner](https://github.com/user-attachments/assets/8861659d-57db-481a-bb38-dc1edfb47d59)

# 👣 GACHENA - MLH Hackathon using gemini-3-pro-preview
**Detect · Protect · Control Your Digital Footprint**

**Gachena** is an innovative web application that empowers users to take control of their personal data by automating GDPR compliance requests. Connect your Gmail, scan your digital footprint, and send automated data privacy requests to companies holding your information.

## 🏗️ Architecture

![System Architecture](https://i.postimg.cc/zDVpcTk7/tracectrl-architecture.png)

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
- **JWT Tokens**: Session management and security
- **Cookie-based Auth**: Persistent user sessions

### **Deployment & DevOps**
- **Docker**: Containerized application packaging
- **Google Container Registry**: Image storage and management
- **Google Cloud Run**: Serverless deployment platform
- **Environment Variables**: Secure configuration management

## 🚀 Quick Start

### **Prerequisites**
- Python 3.11 or higher
- Google Cloud Project with Gmail API enabled
- Gemini API access (Vertex AI)
- FireCrawl API key
- Logo.dev API key

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
Create a `.env` file with:
```bash
# Google OAuth Credentials
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8501

# API Keys
FIRECRAWL_API_KEY=your_firecrawl_key
LOGODEV_API_KEY=your_logodev_key
GEMINI_API_KEY=your_gemini_key

# Gmail Configuration
GMAIL_SCOPES=gmail.readonly,gmail.send
```

4. **Set up Google OAuth**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create OAuth 2.0 credentials
   - Add `http://localhost:8501` to authorized redirect URIs
   - Download `credentials.json` to project root

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
- Adjust date range and filters in "Advanced Options"
- View detected companies with logos and categories

### **Step 3: Select Companies**
- Browse the interactive table of detected companies
- Select companies using checkboxes
- Choose request type for each: Access, Erase, or Modify

### **Step 4: Send Requests**
- Click "Run Bot" to process selections
- Preview emails before sending
- Choose bulk send for multiple companies
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

Create a `.env` file in the root directory:
```bash
# Required for authentication
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here

# Required for external services
FIRECRAWL_API_KEY=your_firecrawl_api_key
LOGODEV_API_KEY=your_logodev_api_key
GEMINI_API_KEY=your_gemini_api_key

# Optional: Customize app behavior
SESSION_TIMEOUT=3600
MAX_EMAILS_SCAN=1000
DEFAULT_DATE_RANGE=7
```

## 🐳 Docker Deployment

### **Build Docker Image**
```bash
docker build -t gachena-app .
```

### **Run Container**
```bash
docker run -p 8501:8501 \
  -e GOOGLE_CLIENT_ID=your_id \
  -e GOOGLE_CLIENT_SECRET=your_secret \
  -e FIRECRAWL_API_KEY=your_key \
  gachena-app
```

### **Docker Compose**
```yaml
version: '3.8'
services:
  gachena:
    build: .
    ports:
      - "8501:8501"
    environment:
      - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
      - GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
      - FIRECRAWL_API_KEY=${FIRECRAWL_API_KEY}
      - LOGODEV_API_KEY=${LOGODEV_API_KEY}
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
  --set-env-vars="GOOGLE_CLIENT_ID=$CLIENT_ID,GOOGLE_CLIENT_SECRET=$CLIENT_SECRET"
```

## 📁 Project Structure

```
Clash-Code/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
├── credentials.json      # Google OAuth credentials
├── utils.py              # Utility functions and helpers
├── streamlit_auth.py     # Authentication module
├── streamlit_auth_cookie.py # Cookie management
├── gemini_processed_emails.json # Sample email data
├── index.html            # Landing page HTML
└── diagnostic.py         # Debug and testing utilities
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

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Team

**Gachena** was developed by a team of three during the MLH Hackathon:
- **Abdi Megersa** - Backend & AI Integration
- **Eba Alemu** - Frontend & UI Design  
- **Osama Hasan** - DevOps & Deployment

## 🎥 Demo & Resources

### **Live Demo**
- **Demo Video**: already uploaded
### **Presentation Materials**
- **Pitch Deck**: [CANVA](https://www.canva.com/design/DAG-A8hVKxA/bbe7FO5dtep7RjiMZYB6oQ/edit?utm_content=DAG-A8hVKxA&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton)  
- **API Documentation**: [documentation Collection](https://gemini-hackathon-hub-614365371127.us-west1.run.app/)  

## 📞 Support

For issues, questions, or support:
- **GitHub Issues**: [Create an issue](https://github.com/Hope0351/Clash-Code/issues)
- 
## ⭐ Acknowledgements

- **MLH Hackathon** for the opportunity and platform
- **Google Cloud** for AI and infrastructure services
- **Streamlit** for the amazing framework
- **FireCrawl & Logo.dev** for their APIs
- **All open-source contributors** whose work made this possible

---

<div align="center">
  
**Gachena** • **Detect • Protect • Control**

[![GitHub stars](https://img.shields.io/github/stars/Hope0351/Clash-Code?style=social)](https://github.com/Hope0351/Clash-Code)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

*Built with ❤️ during MLH Hackathon*

</div>

---
