import pandas as pd
import streamlit as st
import os
import time
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
    page_icon="👣",
    layout="wide",
    initial_sidebar_state="expanded"
)


def initialize_authenticator():
    """Authenticate the user and initialize Google service if connected."""
    authenticator = google_authenticate()
    with st.sidebar:
        authenticator.login()

    if st.session_state.get('connected'):
        st.session_state['gmail_service'] = build_gmail_service()
        display_user_info(authenticator)
    else:
        display_homepage()
        return False

    return True


def display_user_info(authenticator):
    """Display logged-in user info and a logout button."""
    st.sidebar.image(st.session_state['user_info'].get('picture'), width=80)
    st.sidebar.write(f"You are logged in as **{st.session_state['user_info'].get('name')}**")
    if st.sidebar.button('Log out'):
        authenticator.logout()


def display_homepage():
    """Display the homepage if the user is not connected."""
    try:
        with open('index.html', 'r') as file:
            html_content = file.read()
        html(html_content, height=600)
    except FileNotFoundError:
        st.title("Welcome to Gachena")
        st.write("Sign in with Google to get started.")


@st.fragment
def configure_advanced_options():
    """Set advanced options for scanning emails."""
    with st.expander('Advanced Options'):
        day_range = st.slider('Fetch Emails From the Past (Days)', min_value=1, max_value=60, step=7, value=7)
        ignored_categories = st.multiselect('Ignore Categories', ['Personal', 'Promotions', 'Social', 'Updates', 'Forums'])
        max_emails = st.number_input('Max Emails Per Category', min_value=5, max_value=100, value=10, step=5)
    return day_range, ignored_categories, max_emails


@st.fragment
def display_options():
    """Display advanced options and the Scan Inbox button."""

    st.markdown("""
    ### How to Get Started

    Follow these easy steps to control your digital footprint with **Gachena**:

    1. **Scan Your Inbox**: Click the **Scan Inbox** button to analyze your emails and identify companies with your data.
    2. **Adjust Advanced Settings** (Optional): Customize your scan with options like date range and categories to ignore.
    3. **Review and Select**: Browse the results, choose a company and request type (e.g., Access, Erase, Modify).
    4. **Run the Bot**: Click **Run Bot** to preview your request email, then hit **Send Email** to send it.

    """)

    # Toggle between live scan and demo mode
    demo_mode = st.toggle(
        'Demo Mode (uses sample data)',
        value=False,
        help='Enable this to scan pre-loaded sample emails instead of your real Gmail inbox.'
    )

    scan_button = st.button('Scan Inbox', type='primary')
    day_range, ignored_categories, max_emails = configure_advanced_options()

    if scan_button:
        gmail_service = st.session_state.get('gmail_service')

        if demo_mode:
            st.info("Running in demo mode with sample data.")
            email_data = read_json('gemini_processed_emails.json')
        else:
            if not gmail_service:
                st.error("Gmail service not available. Please re-authenticate.")
                return
            try:
                email_data = process_emails(gmail_service, day_range, ignored_categories, max_emails)
            except Exception as e:
                st.error(f"Failed to scan inbox: {e}")
                return

        if not email_data:
            st.warning("No emails were found or processed. Try adjusting your date range or disabling demo mode.")
            return

        logo_url_list, classification_data = extract_email_data(email_data)

        display_results(logo_url_list, classification_data)

        run_bot()


def extract_email_data(email_data):
    """Process and extract email data for display."""
    logo_url_set = set()
    classification_data = []

    for email_id, email_info in email_data.items():
        compose_logo_url(logo_url_set, email_info)
        compose_df(classification_data, email_info)

    return list(logo_url_set), classification_data


def display_results(logo_url_list, classification_data):
    """Display logos and the classified data table."""
    if not classification_data:
        st.info("No companies were detected in the scanned emails.")
        return

    st.subheader("These companies and more have your data...")
    if logo_url_list:
        display_random_logos(logo_url_list)
    df_clean = pd.DataFrame(classification_data)
    display_df(df_clean)


@st.fragment
def run_bot():
    """Control bot execution for single or multiple selected rows."""
    columns = st.columns(3)

    with columns[0]:
        run_button = st.button('Run Bot', type='primary')

    with columns[2]:
        email_preview = st.toggle('Preview Email', value=True, help='Available for single selection only')

    # Single email send with preview
    if run_button and email_preview:
        if not validate_selection(single_row=True):
            return
        send_email(st.session_state['selected_rows'].iloc[0])

    # Mass email send without preview
    if run_button and email_preview == False:
        if not validate_selection(single_row=False):
            return
        for _, row in st.session_state['selected_rows'].iterrows():
            send_email(row, preview=False)


def validate_selection(single_row=True):
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


def send_email(row, preview=True):
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
            preview_email(email, email_subject, email_body, st.session_state['gmail_service'])
        else:
            message = create_message(
                st.session_state['user_info'].get('email'), email, email_subject, email_body
            )
            send_message(st.session_state['gmail_service'], 'me', message)
            st.success(f"Email sent to {selected_company} at {email}")
    except ValueError as e:
        st.error(f"Could not process {selected_company}: {e}")
    except Exception as e:
        st.error(f"Failed to send email to {selected_company}: {e}")


def sidebar_footer():
    """Display the footer in the sidebar."""
    for _ in range(10):
        st.sidebar.markdown('')

    st.sidebar.markdown(
        """
        ---
        **Gachena** - Detect, Protect, Control Your Digital Footprint

        Project built with ❤️ for the [MLH LEAGUE](https://events.mlh.io/events/13215-clash-of-code)
        """)


def main():
    if initialize_authenticator():
        display_options()
    sidebar_footer()


if __name__ == '__main__':
    main()