import requests
import re
import json
import os
import sys
import random
import base64
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

import streamlit as st
import pandas as pd

# --- Lazy imports for heavy/optional dependencies ---
# These are only imported when actually needed (live mode), not in demo mode.

def _import_vertexai():
    import vertexai
    return vertexai


def _import_generative_model():
    from vertexai.generative_models import GenerativeModel, GenerationConfig
    return GenerativeModel, GenerationConfig


def _import_langchain_vertexai():
    from langchain_google_vertexai import VertexAI
    return VertexAI


def _import_unstructured_loader():
    from langchain_community.document_loaders import UnstructuredURLLoader
    return UnstructuredURLLoader


def _import_google_auth():
    import google.auth
    return google.auth


def _import_google_oauth():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    return Credentials, Request


def _import_google_api_client():
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    return build, HttpError


def _import_mime():
    from email.mime.text import MIMEText
    return MIMEText


def _import_authenticate():
    from streamlit_auth import Authenticate
    return Authenticate

# Load environment variables from .env file if present
load_dotenv()

# --- Configuration from Environment ---
SERVICE_ACCOUNT_PATH = os.getenv('SERVICE_ACCOUNT_PATH', 'service_acc.json')
COOKIE_KEY = os.getenv('COOKIE_KEY', os.getenv('COOKIE_SECRET', 'change_me_in_production'))
COOKIE_NAME = os.getenv('COOKIE_NAME', 'gachena_auth')
COOKIE_EXPIRY_DAYS = float(os.getenv('COOKIE_EXPIRY_DAYS', '30'))
REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8501/')
MAX_GEMINI_RETRIES = int(os.getenv('MAX_GEMINI_RETRIES', '3'))
GEMINI_RETRY_DELAY = int(os.getenv('GEMINI_RETRY_DELAY', '60'))
VERTEX_PROJECT = os.getenv('VERTEX_PROJECT', '')
VERTEX_LOCATION = os.getenv('VERTEX_LOCATION', 'us-central1')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash-001')
LOGO_TIMEOUT = int(os.getenv('LOGO_TIMEOUT', '5'))

# --- Vertex AI initialization (lazy) ---
_vertex_initialized = False


def _init_vertex_ai():
    """Initialize Vertex AI once, using service account credentials."""
    global _vertex_initialized
    if _vertex_initialized:
        return

    vertexai = _import_vertexai()
    google_auth = _import_google_auth()

    if os.path.exists(SERVICE_ACCOUNT_PATH):
        credentials, project_id = google_auth.load_credentials_from_file(SERVICE_ACCOUNT_PATH)
        vertexai.init(
            project=project_id or VERTEX_PROJECT,
            location=VERTEX_LOCATION,
            credentials=credentials
        )
    else:
        vertexai.init(project=VERTEX_PROJECT, location=VERTEX_LOCATION)

    _vertex_initialized = True


def get_first_working_url(json_data, timeout=10):
    """
    Retrieve the first working URL from a list in a JSON response.

    Parameters:
        json_data (dict): JSON data containing a "success" status and a list of URLs under the "links" key.
        timeout (int): HTTP request timeout in seconds.

    Returns:
        str: The first URL that returns a successful HTTP response (status code 200).

    Raises:
        ValueError: If the operation is unsuccessful, no URLs are provided, or no valid URL is found.
    """
    if not json_data.get('success', False):
        raise ValueError("The FireCrawl operation was not successful")

    urls = json_data.get('links', [])
    if not urls:
        raise ValueError("No privacy URLs found by FireCrawl")

    for url in urls:
        try:
            response = requests.get(url, timeout=timeout, headers={'User-Agent': 'Gachena/1.0'})
            if response.status_code == 200:
                return url
        except requests.exceptions.RequestException as e:
            print(f"Error checking {url}: {e}")
            continue

    raise ValueError("No valid privacy URL found in the provided list")


def return_privacy_url(base_url):
    """
    Query FireCrawl API to retrieve URLs related to privacy information for a given website.

    Parameters:
        base_url (str): The base URL of the website for which to retrieve privacy-related links.

    Returns:
        requests.Response: The API response object containing privacy URLs.

    Raises:
        ValueError: If FIRECRAWL_API_KEY is not set.
    """
    firecrawl_key = os.getenv('FIRECRAWL_API_KEY')
    if not firecrawl_key:
        raise ValueError("FIRECRAWL_API_KEY environment variable is not set. "
                         "Please set it in your .env file or deployment environment.")

    api_url = "https://api.firecrawl.dev/v1/map"
    payload = {
        "url": base_url,
        "search": "privacy",
        "ignoreSitemap": False,
        "includeSubdomains": True,
        "limit": 3
    }
    headers = {
        "Authorization": f"Bearer {firecrawl_key}",
        "Content-Type": "application/json"
    }
    return requests.post(api_url, json=payload, headers=headers, timeout=30)


def extract_email(privacy_url):
    """
    Extract the data privacy or GDPR contact email address from a privacy URL.

    Parameters:
        privacy_url (str): The URL of the privacy page to analyze.

    Returns:
        str: The extracted email address if found; otherwise, "No email available".
    """
    try:
        url_list = [privacy_url]
        UnstructuredURLLoader = _import_unstructured_loader()
        loader = UnstructuredURLLoader(urls=url_list)
        data = loader.load()

        if not data or not data[0].page_content:
            return "No email available"

        _init_vertex_ai()
        VertexAI = _import_langchain_vertexai()
        model = VertexAI(model_name=GEMINI_MODEL, temperature=0)

        prompt = f"""
        Based on the below text, what is the email for data privacy/GDPR contact?
        Return only email address.
        {data[0].page_content[:8000]}
        """
        response = model.invoke(prompt)

        # Extract valid email from response
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        match = re.search(email_pattern, response)
        if match:
            return match.group(0)
        else:
            return "No email available"
    except Exception as e:
        print(f"Error extracting email from {privacy_url}: {e}")
        return "No email available"


def check_url(url, timeout=LOGO_TIMEOUT):
    """
    Check if a URL is accessible and returns a successful HTTP status.

    Parameters:
        url (str): The URL to check.
        timeout (int): Request timeout in seconds.

    Returns:
        bool: True if the URL returns a 200 status code, False otherwise.
    """
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        try:
            response = requests.get(url, timeout=timeout, stream=True, headers={'User-Agent': 'Gachena/1.0'})
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False


def read_json(file_path):
    """
    Read a JSON file and return its contents as a dictionary.

    Parameters:
        file_path (str): The path to the JSON file.

    Returns:
        dict: The data from the JSON file as a dictionary.
    """
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data


def compose_logo_url(logo_url_set, email_info):
    """
    Generate a logo URL based on company website information and add it to a set if valid.

    Parameters:
        logo_url_set (set): A set to store valid logo URLs.
        email_info (dict): Dictionary containing email interaction information.

    Returns:
        None
    """
    try:
        classification = json.loads(email_info.get("Interaction Type", "{}"))
        website = classification.get("website", "")

        if not website:
            return

        # Clean the website URL
        cleaned_website = re.sub(r'https?://(www\.)?', '', website).strip('/')

        logodev_key = os.getenv('LOGODEV_API_KEY', '')
        if not logodev_key:
            return

        logo_url = f"https://img.logo.dev/{cleaned_website}?token={logodev_key}"

        if check_url(logo_url):
            logo_url_set.add(logo_url)
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error composing logo URL: {e}")


def compose_df(classification_data, email_info):
    """
    Extract company details from email interaction data and append it as a dictionary to a list.

    Parameters:
        classification_data (list): A list to store classification dictionaries with company details.
        email_info (dict): Dictionary containing email interaction data.

    Returns:
        None
    """
    try:
        interaction_str = email_info.get("Interaction Type", email_info.get("Classification", "{}"))

        # Handle case where classification might already be a dict
        if isinstance(interaction_str, dict):
            interaction_dict = interaction_str
        else:
            interaction_dict = json.loads(interaction_str)

        company_name = interaction_dict.get("company_name", "")
        # Support both "category" and "interaction_type" keys from Gemini response
        category = interaction_dict.get("category", interaction_dict.get("interaction_type", ""))
        website = interaction_dict.get("website", "")

        if company_name:
            classification_data.append({
                "Company Name": company_name,
                "Interaction Type": category,
                "Website": website
            })
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error composing dataframe row: {e}")


def display_random_logos(image_urls):
    """
    Display a grid of random logos with varying sizes in Streamlit.

    Parameters:
        image_urls (list): A list of image URLs to display.

    Returns:
        None
    """
    if not image_urls:
        return

    num_columns = 7
    shuffled = image_urls.copy()
    random.shuffle(shuffled)

    widths = [random.randint(30, 90) for _ in shuffled]

    for i in range(0, len(shuffled), num_columns):
        cols = st.columns(num_columns)
        for idx, img_url in enumerate(shuffled[i:i + num_columns]):
            with cols[idx]:
                width = widths[i + idx]
                img_html = f'''
                    <img src="{img_url}"
                         style="border-radius:50%;
                                width:{width}px;
                                height:{width}px;
                                object-fit:contain;
                                margin-bottom:10px;"
                         alt="Company logo"
                    />
                '''
                st.markdown(img_html, unsafe_allow_html=True)


def display_df(df):
    """
    Display an editable dataframe in Streamlit, allowing users to select and interact with company data.

    Parameters:
        df (pd.DataFrame): The dataframe containing company information.

    Returns:
        pd.DataFrame: A subset of the dataframe with only the selected rows.
    """
    if df.empty:
        st.info("No companies detected. Try scanning more emails or adjusting your filters.")
        return pd.DataFrame()

    # Drop duplicate companies
    df = df.drop_duplicates(subset=['Company Name']).copy()

    # Add interactive columns
    df['Select Option'] = '-'
    df['Select'] = False

    dropdown_options = ['Request Data', 'Modify Data', 'Erase Data']

    column_config = {
        'Select Option': st.column_config.SelectboxColumn(options=dropdown_options),
        'Website': st.column_config.LinkColumn(),
        'Select': st.column_config.CheckboxColumn(),
    }

    edited_df = st.data_editor(
        df,
        column_config=column_config,
        hide_index=True,
        width='stretch',
        column_order=['Select', 'Company Name', 'Interaction Type', 'Website', 'Select Option']
    )

    selected_rows = edited_df[edited_df['Select']]
    st.session_state['selected_rows'] = selected_rows
    return selected_rows


@st.dialog("Email Preview")
def preview_email(email, subject, body, service):
    """
    Display a dialog in Streamlit for previewing and sending an email.

    Parameters:
        email (str): The recipient's email address.
        subject (str): The subject of the email.
        body (str): The body content of the email.
        service (googleapiclient.discovery.Resource): The Gmail API service instance.

    Returns:
        None
    """
    st.text_input("To", email, disabled=True)
    st.text_input("Subject", subject, disabled=True)
    st.text_area(label="Body", value=body, label_visibility='hidden', height=300)

    st.write('')

    send_button = st.button("Send Email", type="primary")

    if send_button:
        sender_email = st.session_state['user_info'].get('email')
        message = create_message(sender_email, email, subject, body)
        result = send_message(service, 'me', message)
        if result:
            st.success("Email sent successfully!")
        else:
            st.error("Failed to send email. Check the logs for details.")


def get_email_template():
    """
    Retrieve predefined email templates for different types of GDPR requests.

    Returns:
        dict: A dictionary with GDPR request types as keys and their corresponding email subject and body.
    """
    email_template = {
        "Request Data": {
            "subject": "GDPR Data Access Request",
            "body": """Dear Data Protection Officer,

    I am writing to request access to my personal data as per Article 15 of the General Data Protection Regulation (GDPR). I would like to receive a copy of all personal data that {company_name} have collected about me, as well as any information regarding how and why my data is being processed.

    Please provide the following:
    - Categories of personal data being processed
    - The specific purposes for processing my data
    - Information on any third parties with whom my data has been shared
    - The source of my personal data if it was not collected directly from me

    Thank you for your attention to this matter. I look forward to receiving a response within the GDPR-mandated timeframe.

    Sincerely,
    {user_name}
    """
        },
        "Modify Data": {
            "subject": "GDPR Data Modification Request",
            "body": """Dear Data Protection Officer,

    I am reaching out to request a modification to my personal data under Article 16 of the General Data Protection Regulation (GDPR). I believe certain data you hold about me may be inaccurate or incomplete, and I would like this data to be corrected as soon as possible.

    Please update the following information:
    - [Specify the data to be updated, e.g., name, address, contact information, etc.]

    If you require any additional information from me to fulfill this request, please let me know at your earliest convenience.

    Thank you for your cooperation and prompt attention to this request.

    Sincerely,
    {user_name}
    """
        },
        "Erase Data": {
            "subject": "GDPR Data Erasure Request",
            "body": """Dear Data Protection Officer,

    I am contacting you to request the deletion of my personal data in accordance with Article 17 of the General Data Protection Regulation (GDPR). I no longer wish for my personal data to be processed by {company_name}, and I request that all relevant data be permanently deleted.

    Please confirm the deletion of my personal data, or, if my request cannot be fulfilled in full, kindly provide the reason and any alternative actions that can be taken.

    Thank you for your cooperation, and I look forward to your prompt confirmation of the erasure of my data.

    Sincerely,
    {user_name}
    """
        }
    }
    return email_template


def google_authenticate():
    """
    Authenticate the user with Google and return an authentication object.

    Returns:
        Authenticate: An authentication object with session management.
    """
    redirect = os.getenv('GOOGLE_REDIRECT_URI', REDIRECT_URI)
    # Ensure trailing slash consistency
    if not redirect.endswith('/'):
        redirect += '/'

    Authenticate = _import_authenticate()

    authenticator = Authenticate(
        secret_credentials_path='credentials.json',
        cookie_name=COOKIE_NAME,
        cookie_key=COOKIE_KEY,
        cookie_expiry_days=COOKIE_EXPIRY_DAYS,
        redirect_uri=redirect,
    )

    # Catch the login event
    authenticator.check_authentification()
    return authenticator


def build_gmail_service():
    """
    Build and return an authenticated Gmail API service instance using stored credentials.

    Returns:
        googleapiclient.discovery.Resource: The Gmail API service instance.

    Raises:
        ValueError: If credentials are not found in session state.
    """
    if "credentials" not in st.session_state:
        raise ValueError("No OAuth credentials found. Please re-authenticate.")

    try:
        Credentials, Request = _import_google_oauth()
        build_func, HttpError = _import_google_api_client()

        credentials_info = json.loads(st.session_state["credentials"])
        credentials = Credentials.from_authorized_user_info(credentials_info)

        # Refresh the token if expired
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            st.session_state["credentials"] = credentials.to_json()

        gmail_service = build_func('gmail', 'v1', credentials=credentials)
        return gmail_service
    except Exception as e:
        print(f"Error building Gmail service: {e}")
        raise


def create_message(sender, to, subject, message_text):
    """
    Create an email message in a format suitable for the Gmail API.

    Parameters:
        sender (str): The email address of the sender.
        to (str): The recipient's email address.
        subject (str): The subject of the email.
        message_text (str): The body of the email.

    Returns:
        dict: A dictionary containing the raw, base64-encoded message.
    """
    MIMEText = _import_mime()
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw_message}


def send_message(service, user_id, message):
    """
    Send an email message using the Gmail API.

    Parameters:
        service (googleapiclient.discovery.Resource): The Gmail API service instance.
        user_id (str): The sender's user ID, typically "me".
        message (dict): The email message created by `create_message`.

    Returns:
        dict: The response from the Gmail API if successful.
        None: If an error occurred during sending.
    """
    try:
        _, HttpError = _import_google_api_client()
        result = service.users().messages().send(userId=user_id, body=message).execute()
        print(f"Message sent. ID: {result['id']}")
        return result
    except HttpError as e:
        print(f"Gmail API error sending message: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error sending message: {e}")
        return None


def fetch_emails_by_label(service, label_id, days, num_emails=10):
    """
    Fetch emails from a specified category within a given date range.

    Parameters:
        service: The Gmail API service instance.
        label_id (str): The Gmail label ID to filter by (e.g., 'CATEGORY_PROMOTIONS').
        days (int): The number of past days to include.
        num_emails (int): Maximum number of emails to fetch. Defaults to 10.

    Returns:
        list: A list of email message dicts.
    """
    start_date = (datetime.now() - timedelta(days=days - 1)).strftime('%Y/%m/%d')
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y/%m/%d')

    query = f'after:{start_date} before:{tomorrow} -label:CATEGORY_PERSONAL'

    try:
        _, HttpError = _import_google_api_client()
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=num_emails,
            labelIds=[label_id]
        ).execute()

        return results.get('messages', [])
    except HttpError as e:
        print(f"Error fetching emails for label {label_id}: {e}")
        return []


def fetch_emails(service, days, ignored_categories=None, num_emails=10):
    """
    Fetch emails from multiple categories within a specified date range.

    Parameters:
        service: The Gmail API service instance.
        days (int): The number of past days to include.
        ignored_categories (list of str): Categories to skip (e.g., ['Promotions', 'Social']).
        num_emails (int): Maximum emails per category. Defaults to 10.

    Returns:
        list: Combined list of email messages.
    """
    # Map user-friendly category names to Gmail label IDs
    category_map = {
        'Promotions': 'CATEGORY_PROMOTIONS',
        'Updates': 'CATEGORY_UPDATES',
        'Social': 'CATEGORY_SOCIAL',
        'Forums': 'CATEGORY_FORUMS',
    }

    categories = ['CATEGORY_PROMOTIONS', 'CATEGORY_UPDATES']

    # Filter out ignored categories
    if ignored_categories:
        for cat_name in ignored_categories:
            label_id = category_map.get(cat_name)
            if label_id and label_id in categories:
                categories.remove(label_id)

    if not categories:
        print("All categories were filtered out. No emails to fetch.")
        return []

    combined_emails = []
    for category in categories:
        print(f"Fetching emails from {category} for the last {days} day(s)...")
        emails = fetch_emails_by_label(service, category, days=days, num_emails=num_emails)
        combined_emails.extend(emails)

    return combined_emails


def get_email_content(service, message_id):
    """
    Retrieve the content, subject, sender, and date of a specified email message.

    Parameters:
        service: The Gmail API service instance.
        message_id (str): The ID of the email message.

    Returns:
        tuple: (subject, sender, date, email_content) or (None, None, None, None) on failure.
    """
    try:
        message = service.users().messages().get(userId='me', id=message_id, format='full').execute()
        payload = message.get('payload', {})
        headers = payload.get('headers', [])
        data = ''

        subject = None
        sender = None
        date = None

        for header in headers:
            if header['name'] == 'Subject':
                subject = header['value']
            if header['name'] == 'From':
                sender = header['value']
            if header['name'] == 'Date':
                date_str = header['value']
                try:
                    parsed_date = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
                    date = parsed_date.strftime("%Y-%m-%d")
                except ValueError:
                    date = date_str

        # Try to extract content - plain text first, then HTML fallback
        email_content = _extract_body(payload)

        if email_content:
            return subject, sender, date, email_content
        else:
            print(f"No content found in email {message_id}")
            return None, None, None, None

    except Exception as e:
        print(f"Error retrieving email {message_id}: {e}")
        return None, None, None, None


def _extract_body(payload):
    """
    Recursively extract email body content from a Gmail message payload.
    Tries plain text first, falls back to stripping HTML.

    Parameters:
        payload (dict): The Gmail message payload.

    Returns:
        str or None: The extracted text content.
    """
    if not payload:
        return None

    # If the payload has parts (multipart), iterate through them
    if 'parts' in payload:
        for part in payload['parts']:
            content = _extract_body(part)
            if content:
                return content
        return None

    # Leaf node - check mimeType and get data
    mime_type = payload.get('mimeType', '')

    if mime_type == 'text/plain':
        data = payload.get('body', {}).get('data')
        if data:
            return base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8', errors='replace')

    elif mime_type == 'text/html' and 'parts' not in payload:
        data = payload.get('body', {}).get('data')
        if data:
            html_content = base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8', errors='replace')
            # Strip HTML tags to get plain text
            text = re.sub(r'<[^>]+>', ' ', html_content)
            text = re.sub(r'\s+', ' ', text).strip()
            if len(text) > 50:  # Only return if meaningful content
                return text

    return None


def classify_email_with_gemini(email_content):
    """
    Classify an email and extract company information using Gemini AI.

    Parameters:
        email_content (str): The text content of the email to classify.

    Returns:
        str: A JSON string containing company_name, category/interaction_type, and website.

    Raises:
        Exception: If classification fails after retries.
    """
    _init_vertex_ai()

    SYSTEM_INSTRUCTIONS = """
    You are a helpful AI that helps classify emails and extract relevant information.

    All emails are classified into one of the following categories: interacted, not interacted.
    Interacted emails are triggered directly by a user's action.
    They are functional and usually contain important information, such as confirmations (order confirmations,
    password resets, account creation), notifications about transactions, or updates on user-initiated requests.

    Not interacted emails are not triggered by any specific user action. They are often used to keep users engaged,
    provide updates, send offers, or remind users of products/services. Examples include newsletters, promotional emails, and other marketing content.
    """

    # Truncate very long emails to save tokens
    truncated_content = email_content[:6000] if len(email_content) > 6000 else email_content

    PROMPT = f"""
    Based on the following email content, identify the following:
    1. The name of the company (if not mentioned explicitly, infer from the context).
    2. Classify the email into one of the following categories: interacted, not interacted.
    3. Company website (if not mentioned explicitly, infer from the context).

    Email content:
    {truncated_content}
    """

    response_schema = {
        "type": "OBJECT",
        "properties": {
            "company_name": {"type": "STRING"},
            "category": {"type": "STRING", "enum": ["interacted", "not interacted"]},
            "website": {"type": "STRING"}
        },
        "required": ["company_name", "category", "website"]
    }

    GenerativeModel, GenerationConfig = _import_generative_model()

    model = GenerativeModel(
        GEMINI_MODEL,
        system_instruction=SYSTEM_INSTRUCTIONS
    )

    response = model.generate_content(
        [PROMPT],
        generation_config=GenerationConfig(
            response_mime_type="application/json",
            response_schema=response_schema
        )
    )

    return response.text


def process_emails(service, days, ignored_categories=None, max_emails=10):
    """
    Process emails by fetching, analyzing, and classifying them.

    Parameters:
        service: The Gmail API service object.
        days (int): The number of days from which to fetch emails.
        ignored_categories (list of str): Categories to ignore during processing.
        max_emails (int): Maximum emails to fetch per category.

    Returns:
        dict: A dictionary of processed email data keyed by message ID.
    """
    progress_bar = st.progress(0, text="Fetching emails...")
    messages = fetch_emails(service, days, ignored_categories=ignored_categories, num_emails=max_emails)

    if not messages:
        progress_bar.empty()
        st.warning("No emails found for the selected date range and categories.")
        return {}

    email_data = {}
    total = len(messages)

    progress_bar.progress(25, text=f"Analyzing {total} emails with AI...")

    for idx, msg in enumerate(messages):
        message_id = msg['id']
        subject, sender, date, email_content = get_email_content(service, message_id)

        if email_content is None or sender is None:
            continue

        # Retry mechanism with max retry cap
        retries = 0
        processed = False

        while retries < MAX_GEMINI_RETRIES and not processed:
            try:
                gemini_result = classify_email_with_gemini(email_content)

                if gemini_result:
                    email_data[message_id] = {
                        "Subject": subject,
                        "Sender": sender,
                        "Date": date,
                        "Interaction Type": gemini_result
                    }
                    print(f"Processed email {message_id} ({idx + 1}/{total}).")
                processed = True

            except Exception as e:
                error_str = str(e)
                if '429' in error_str or 'Quota exceeded' in error_str or 'RESOURCE_EXHAUSTED' in error_str:
                    retries += 1
                    if retries < MAX_GEMINI_RETRIES:
                        wait_time = GEMINI_RETRY_DELAY * retries  # Exponential backoff
                        print(f"Rate limit hit. Retry {retries}/{MAX_GEMINI_RETRIES}. Waiting {wait_time}s...")
                        progress_bar.progress(
                            25 + int(70 * idx / total),
                            text=f"Rate limited. Waiting {wait_time}s before retry..."
                        )
                        time.sleep(wait_time)
                    else:
                        print(f"Max retries ({MAX_GEMINI_RETRIES}) exceeded for email {message_id}. Skipping.")
                else:
                    print(f"Skipping email {message_id} due to error: {e}")
                    processed = True  # Don't retry non-rate-limit errors

        # Update progress
        progress_pct = 25 + int(70 * (idx + 1) / total)
        progress_bar.progress(min(progress_pct, 95), text=f"Processed {idx + 1}/{total} emails...")

    progress_bar.progress(100, text="Scan complete!")
    time.sleep(0.5)
    progress_bar.empty()

    return email_data