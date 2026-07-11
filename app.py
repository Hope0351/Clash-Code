import pandas as pd
import streamlit as st
import os

# Resolve paths relative to this script file
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEMO_DATA_PATH = os.path.join(_SCRIPT_DIR, 'gemini_processed_emails.json')
INDEX_HTML_PATH = os.path.join(_SCRIPT_DIR, 'index.html')
from streamlit.components.v1 import html
from utils import (
    get_first_working_url, return_privacy_url, extract_email, display_df,
    display_random_logos, read_json, compose_df, compose_logo_url,
    preview_email, get_email_template, google_authenticate, build_gmail_service,
    create_message, send_message, process_emails
)

# --- Page Config ---
st.set_page_config(
    page_title="Gachena - GDPR Compliance Tool",
    page_icon="foot",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Demo mode toggle (must be before auth) ---
DEMO_USER = {
    'name': 'Demo User',
    'email': 'demo@gachena.com',
    'picture': 'https://ui-avatars.com/api/?name=Demo+User&background=77dd77&color=fff&size=128',
    'id': 'demo_user_001'
}


def _activate_demo_session():
    """Set up a fake authenticated session for demo mode."""
    st.session_state['connected'] = True
    st.session_state['user_info'] = DEMO_USER
    st.session_state['oauth_id'] = DEMO_USER['id']
    st.session_state['gmail_service'] = None  # No real Gmail in demo mode
    if 'logout' in st.session_state:
        del st.session_state['logout']


def initialize_authenticator(demo_mode=False):
    """Authenticate the user. In demo mode, skip real OAuth entirely."""
    if demo_mode:
        _activate_demo_session()
        return None

    authenticator = google_authenticate()
    with st.sidebar:
        authenticator.login()

    authenticator.check_authentification()

    if st.session_state.get('connected'):
        try:
            st.session_state['gmail_service'] = build_gmail_service()
        except (ValueError, Exception):
            st.session_state['gmail_service'] = None
        _display_user_info(authenticator)
    else:
        _display_homepage()
        return None

    return authenticator


def _display_user_info(authenticator):
    """Display logged-in user info and a logout button in the sidebar."""
    user_info = st.session_state.get('user_info', {})
    if user_info.get('picture'):
        st.sidebar.image(user_info['picture'], width=80)
    st.sidebar.write(f"**{user_info.get('name', 'User')}**")
    st.sidebar.caption(user_info.get('email', ''))
    if st.sidebar.button('Log out', use_container_width=True):
        if authenticator:
            authenticator.logout()
        else:
            # Demo mode logout
            st.session_state['connected'] = False
            st.session_state['user_info'] = None
            st.session_state['gmail_service'] = None
            st.rerun()


def _display_homepage():
    """Display the landing page if the user is not connected."""
    try:
        with open(INDEX_HTML_PATH, 'r') as file:
            html_content = file.read()
        html(html_content, height=600)
    except FileNotFoundError:
        st.title("Welcome to Gachena")
        st.write("Sign in with Google to get started.")


def _render_advanced_options():
    """Advanced options for email scanning."""
    with st.expander('Advanced Options'):
        day_range = st.slider('Fetch Emails From the Past (Days)', min_value=1, max_value=60, step=7, value=7)
        ignored_categories = st.multiselect('Ignore Categories', ['Personal', 'Promotions', 'Social', 'Updates', 'Forums'])
        max_emails = st.number_input('Max Emails Per Category', min_value=5, max_value=100, value=10, step=5)
    return day_range, ignored_categories, max_emails


def _render_instructions():
    """Render the how-to-get-started section."""
    st.markdown("""
    ### How to Get Started

    Follow these easy steps to control your digital footprint with **Gachena**:

    1. **Scan Your Inbox**: Click the **Scan Inbox** button to analyze your emails and identify companies with your data.
    2. **Adjust Advanced Settings** (Optional): Customize your scan with options like date range and categories to ignore.
    3. **Review and Select**: Browse the results, choose a company and request type (e.g., Access, Erase, Modify).
    4. **Run the Bot**: Click **Run Bot** to preview your request email, then hit **Send Email** to send it.
    """)


def _extract_email_data(email_data):
    """Process and extract email data for display."""
    logo_url_set = set()
    classification_data = []

    for email_id, email_info in email_data.items():
        compose_logo_url(logo_url_set, email_info)
        compose_df(classification_data, email_info)

    return list(logo_url_set), classification_data


def _render_results(logo_url_list, classification_data):
    """Display logos and the classified data table."""
    if not classification_data:
        st.info("No companies were detected in the scanned emails.")
        return

    st.subheader("These companies and more have your data...")
    if logo_url_list:
        display_random_logos(logo_url_list)

    df_clean = pd.DataFrame(classification_data)
    display_df(df_clean)


def _validate_selection(single_row=True):
    """Validate user selection based on single or multiple row selections."""
    selected_rows = st.session_state.get('selected_rows')
    if selected_rows is None or selected_rows.empty:
        st.warning('Please select at least one company from the table.')
        return False
    if single_row and len(selected_rows) != 1:
        st.warning('Please select exactly one row to proceed with preview.')
        return False
    elif not single_row and len(selected_rows) < 1:
        st.warning('Please select at least one row for mass email send.')
        return False
    if 'Select Option' in selected_rows.columns and '-' in selected_rows['Select Option'].values:
        st.warning('Please select a request type for all selected rows.')
        return False
    return True


def _send_email(row, preview=True):
    """Compose and send email based on row data, optionally preview."""
    selected_website = row['Website']
    selected_option = row['Select Option']
    selected_company = row['Company Name']

    if not selected_website or selected_website.strip() == '':
        st.error(f"No website found for {selected_company}. Cannot send request.")
        return

    try:
        with st.spinner(f"Finding privacy policy for {selected_company}..."):
            response = return_privacy_url(selected_website)
            url = get_first_working_url(response.json())
            email = extract_email(url)

        if not email or email == "No email available":
            st.warning(f"No GDPR contact email found for {selected_company}. Skipping.")
            return

        email_template = get_email_template()
        email_subject = email_template[selected_option]['subject']
        email_body = email_template[selected_option]['body'].format(
            company_name=selected_company, user_name=st.session_state['user_info'].get('name')
        )

        if preview:
            preview_email(email, email_subject, email_body, st.session_state.get('gmail_service'))
        else:
            if not st.session_state.get('gmail_service'):
                st.error("No Gmail connection. Cannot send emails in demo mode.")
                return
            message = create_message(
                st.session_state['user_info'].get('email'), email, email_subject, email_body
            )
            send_message(st.session_state['gmail_service'], 'me', message)
            st.success(f"Email sent to {selected_company} at {email}")
    except ValueError as e:
        st.error(f"Could not process {selected_company}: {e}")
    except Exception as e:
        st.error(f"Failed to send email to {selected_company}: {e}")


def _render_bot_controls():
    """Render the Run Bot section with email preview toggle."""
    columns = st.columns(3)

    with columns[0]:
        run_button = st.button('Run Bot', type='primary', use_container_width=True)

    with columns[2]:
        email_preview = st.toggle('Preview Email', value=True, help='Available for single selection only')

    if not run_button:
        return

    if email_preview:
        if not _validate_selection(single_row=True):
            return
        _send_email(st.session_state['selected_rows'].iloc[0])
    else:
        if not _validate_selection(single_row=False):
            return
        for _, row in st.session_state['selected_rows'].iterrows():
            _send_email(row, preview=False)


def _render_sidebar_footer():
    """Display the footer in the sidebar."""
    for _ in range(10):
        st.sidebar.markdown('')

    st.sidebar.markdown(
        """
        ---
        **Gachena** - Detect, Protect, Control Your Digital Footprint

        Project built with heart for the [MLH LEAGUE](https://events.mlh.io/events/13215-clash-of-code)
        """)


def main():
    # Demo mode toggle at the very top — before any auth
    demo_mode = st.toggle('Demo Mode (no Google login required)', value=True,
                          help='Use sample data with a demo account. No API keys or OAuth needed.')

    authenticator = initialize_authenticator(demo_mode=demo_mode)

    if not st.session_state.get('connected'):
        _render_sidebar_footer()
        return

    # Main dashboard content
    _render_instructions()

    day_range, ignored_categories, max_emails = _render_advanced_options()

    scan_button = st.button('Scan Inbox', type='primary', use_container_width=True)

    if scan_button:
        if demo_mode:
            st.info("Running in demo mode with sample data.")
            try:
                email_data = read_json(DEMO_DATA_PATH)
            except FileNotFoundError:
                st.error("Demo data file `gemini_processed_emails.json` not found.")
                email_data = None
        else:
            gmail_service = st.session_state.get('gmail_service')
            if not gmail_service:
                st.error("Gmail service not available. Please re-authenticate.")
                return
            try:
                with st.spinner("Scanning your inbox..."):
                    email_data = process_emails(gmail_service, day_range, ignored_categories, max_emails)
            except Exception as e:
                st.error(f"Failed to scan inbox: {e}")
                return

        if not email_data:
            st.warning("No emails were found or processed. Try adjusting your date range.")
            return

        logo_url_list, classification_data = _extract_email_data(email_data)
        _render_results(logo_url_list, classification_data)

    # Bot controls only show after a scan has been done
    if 'selected_rows' in st.session_state:
        st.divider()
        _render_bot_controls()

    _render_sidebar_footer()


if __name__ == '__main__':
    main()