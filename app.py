import pandas as pd
import streamlit as st
import os
import json

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

# ─── GACHENA Brand Colors & Theme ───────────────────────────────────────────
GACHENA_PRIMARY = "#0D9488"       # Teal - shield strength
GACHENA_DARK = "#0F172A"          # Deep navy background
GACHENA_CARD = "#1E293B"          # Card background
GACHENA_BORDER = "#334155"        # Subtle borders
GACHENA_TEXT = "#F1F5F9"          # Light text
GACHENA_MUTED = "#94A3B8"         # Muted text
GACHENA_ACCENT = "#2DD4BF"        # Bright teal accent
GACHENA_SUCCESS = "#22C55E"       # Green for success
GACHENA_WARNING = "#F59E0B"       # Amber for warnings
GACHENA_DANGER = "#EF4444"        # Red for errors
GACHENA_SHIELD = "🛡️"            # Shield emoji for branding

# ─── Custom CSS ─────────────────────────────────────────────────────────────
CUSTOM_CSS = f"""
<style>
    /* ── Global ── */
    .stApp {{
        background-color: {GACHENA_DARK};
        color: {GACHENA_TEXT};
    }}

    /* ── Hide Streamlit defaults ── */
    #MainMenu, footer, header {{ visibility: hidden; }}
    .stDeployButton {{ display: none !important; }}

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #0F172A 0%, #1A2744 100%);
        border-right: 1px solid {GACHENA_BORDER};
    }}
    [data-testid="stSidebar"] * {{
        color: {GACHENA_TEXT} !important;
    }}

    /* ── Cards ── */
    .gachena-card {{
        background: {GACHENA_CARD};
        border: 1px solid {GACHENA_BORDER};
        border-radius: 12px;
        padding: 24px;
        margin: 8px 0;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3);
    }}

    /* ── Header branding ── */
    .gachena-header {{
        text-align: center;
        padding: 32px 0 16px 0;
    }}
    .gachena-header h1 {{
        font-size: 2.4em;
        font-weight: 800;
        color: {GACHENA_ACCENT};
        margin-bottom: 4px;
        letter-spacing: -0.5px;
    }}
    .gachena-header .shield-icon {{
        font-size: 3.2em;
        display: block;
        margin-bottom: 8px;
    }}
    .gachena-header .tagline {{
        color: {GACHENA_MUTED};
        font-size: 1.05em;
        font-weight: 400;
    }}

    /* ── Step indicators ── */
    .step-badge {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: linear-gradient(135deg, {GACHENA_PRIMARY} 0%, {GACHENA_ACCENT} 100%);
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85em;
        font-weight: 600;
        margin-bottom: 12px;
    }}

    /* ── Stat counters ── */
    .stat-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
        margin: 20px 0;
    }}
    .stat-box {{
        background: {GACHENA_CARD};
        border: 1px solid {GACHENA_BORDER};
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        transition: transform 0.2s, box-shadow 0.2s;
    }}
    .stat-box:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(13, 148, 136, 0.15);
    }}
    .stat-box .stat-value {{
        font-size: 2em;
        font-weight: 800;
        color: {GACHENA_ACCENT};
    }}
    .stat-box .stat-label {{
        font-size: 0.85em;
        color: {GACHENA_MUTED};
        margin-top: 4px;
    }}

    /* ── Buttons ── */
    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, {GACHENA_PRIMARY} 0%, {GACHENA_ACCENT} 100%);
        border: none;
        color: white;
        font-weight: 600;
        border-radius: 8px;
        padding: 10px 24px;
        transition: all 0.3s;
    }}
    .stButton > button[kind="primary"]:hover {{
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(13, 148, 136, 0.4);
    }}

    /* ── Data editor ── */
    .stDataEditor {{
        border: 1px solid {GACHENA_BORDER};
        border-radius: 12px;
        overflow: hidden;
    }}

    /* ── Expander ── */
    .streamlit-expanderHeader {{
        background: {GACHENA_CARD};
        border-radius: 8px;
        font-weight: 600;
    }}

    /* ── Info / Warning / Error boxes ── */
    .stAlert {{
        border-radius: 10px;
    }}

    /* ── Divider ── */
    .gachena-divider {{
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, {GACHENA_BORDER}, transparent);
        margin: 24px 0;
    }}

    /* ── Footer ── */
    .gachena-footer {{
        text-align: center;
        padding: 24px;
        color: {GACHENA_MUTED};
        font-size: 0.85em;
    }}
    .gachena-footer a {{
        color: {GACHENA_ACCENT};
        text-decoration: none;
    }}

    /* ── GDPR article badges ── */
    .gdpr-badge {{
        display: inline-block;
        padding: 2px 10px;
        border-radius: 6px;
        font-size: 0.75em;
        font-weight: 600;
        margin: 2px;
    }}
    .gdpr-art15 {{ background: #1E3A5F; color: #60A5FA; }}
    .gdpr-art16 {{ background: #1E3F30; color: #4ADE80; }}
    .gdpr-art17 {{ background: #3F1E1E; color: #F87171; }}

    /* ── Instruction cards ── */
    .instruction-grid {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        margin: 16px 0;
    }}
    .instruction-card {{
        background: {GACHENA_CARD};
        border: 1px solid {GACHENA_BORDER};
        border-radius: 12px;
        padding: 20px 16px;
        text-align: center;
        transition: all 0.3s;
    }}
    .instruction-card:hover {{
        border-color: {GACHENA_PRIMARY};
        box-shadow: 0 4px 15px rgba(13, 148, 136, 0.15);
    }}
    .instruction-card .step-num {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: linear-gradient(135deg, {GACHENA_PRIMARY}, {GACHENA_ACCENT});
        color: white;
        font-weight: 700;
        font-size: 0.9em;
        margin-bottom: 10px;
    }}
    .instruction-card .step-title {{
        font-weight: 600;
        font-size: 0.95em;
        margin-bottom: 6px;
        color: {GACHENA_TEXT};
    }}
    .instruction-card .step-desc {{
        font-size: 0.8em;
        color: {GACHENA_MUTED};
        line-height: 1.4;
    }}

    /* ── Toggle styling ── */
    .stToggle > label > div {{
        background-color: {GACHENA_CARD};
    }}

    /* ── Scrollbar ── */
    ::-webkit-scrollbar {{
        width: 8px;
    }}
    ::-webkit-scrollbar-track {{
        background: {GACHENA_DARK};
    }}
    ::-webkit-scrollbar-thumb {{
        background: {GACHENA_BORDER};
        border-radius: 4px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: {GACHENA_PRIMARY};
    }}
</style>
"""


# --- Page Config ---
st.set_page_config(
    page_title="GACHENA - GDPR Compliance Shield",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --- Demo mode user ---
DEMO_USER = {
    'name': 'Demo User',
    'email': 'demo@gachena.com',
    'picture': 'https://ui-avatars.com/api/?name=GACHENA+Shield&background=0D9488&color=fff&size=128&font-size=0.4',
    'id': 'demo_user_001'
}


def _activate_demo_session():
    """Set up a fake authenticated session for demo mode."""
    st.session_state['connected'] = True
    st.session_state['user_info'] = DEMO_USER
    st.session_state['oauth_id'] = DEMO_USER['id']
    st.session_state['gmail_service'] = None
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
    """Display logged-in user info and logout in the sidebar."""
    user_info = st.session_state.get('user_info', {})

    st.sidebar.markdown("---")
    st.sidebar.markdown(f'<div style="text-align:center; padding: 8px 0;">'
                        f'<img src="{user_info.get("picture", "")}" '
                        f'style="width:72px; height:72px; border-radius:50%; '
                        f'border: 2px solid {GACHENA_PRIMARY}; margin-bottom:8px;" />'
                        f'<br><b style="font-size:1.05em;">{user_info.get("name", "User")}</b>'
                        f'<br><span style="color:{GACHENA_MUTED}; font-size:0.85em;">'
                        f'{user_info.get("email", "")}</span></div>',
                        unsafe_allow_html=True)

    if st.sidebar.button('🚪 Log Out', use_container_width=True, key='logout_btn'):
        if authenticator:
            authenticator.logout()
        else:
            st.session_state['connected'] = False
            st.session_state['user_info'] = None
            st.session_state['gmail_service'] = None
        st.rerun()


def _display_homepage():
    """Display the landing page if the user is not connected."""
    try:
        with open(INDEX_HTML_PATH, 'r') as file:
            html_content = file.read()
        html(html_content, height=650)
    except FileNotFoundError:
        st.markdown(f'''
        <div class="gachena-header">
            <span class="shield-icon">{GACHENA_SHIELD}</span>
            <h1>GACHENA</h1>
            <p class="tagline">Detect &bull; Protect &bull; Control Your Digital Footprint</p>
        </div>
        ''', unsafe_allow_html=True)
        st.info("Sign in with Google to get started, or enable Demo Mode above.")


def _render_header():
    """Render the main GACHENA branded header."""
    st.markdown(f'''
    <div class="gachena-header">
        <span class="shield-icon">{GACHENA_SHIELD}</span>
        <h1>GACHENA</h1>
        <p class="tagline">Detect &bull; Protect &bull; Control Your Digital Footprint</p>
    </div>
    ''', unsafe_allow_html=True)


def _render_instruction_cards():
    """Render the 4-step instruction cards."""
    st.markdown('''
    <div class="instruction-grid">
        <div class="instruction-card">
            <div class="step-num">1</div>
            <div class="step-title">Scan Inbox</div>
            <div class="step-desc">Analyze your emails with AI to detect companies holding your data</div>
        </div>
        <div class="instruction-card">
            <div class="step-num">2</div>
            <div class="step-title">Review Results</div>
            <div class="step-desc">Browse detected companies, their interaction level, and your data footprint</div>
        </div>
        <div class="instruction-card">
            <div class="step-num">3</div>
            <div class="step-title">Select & Choose</div>
            <div class="step-desc">Pick companies and choose your GDPR request type</div>
        </div>
        <div class="instruction-card">
            <div class="step-num">4</div>
            <div class="step-title">Send Requests</div>
            <div class="step-desc">Preview and send automated GDPR compliance emails</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)


def _render_advanced_options():
    """Advanced options for email scanning in a clean card."""
    with st.expander('⚙️ Advanced Scan Options'):
        col1, col2, col3 = st.columns(3)
        with col1:
            day_range = st.slider(
                '📅 Date Range (Days)',
                min_value=1, max_value=60, step=7, value=7,
                help="Fetch emails from the past N days"
            )
        with col2:
            ignored_categories = st.multiselect(
                '📁 Ignore Categories',
                ['Personal', 'Promotions', 'Social', 'Updates', 'Forums'],
                help="Skip these Gmail categories during scanning"
            )
        with col3:
            max_emails = st.number_input(
                '📧 Max Emails / Category',
                min_value=5, max_value=100, value=10, step=5,
                help="Maximum emails to fetch per category"
            )
    return day_range, ignored_categories, max_emails


def _extract_email_data(email_data):
    """Process and extract email data for display."""
    logo_url_set = set()
    classification_data = []

    for email_id, email_info in email_data.items():
        compose_logo_url(logo_url_set, email_info)
        compose_df(classification_data, email_info)

    return list(logo_url_set), classification_data


def _render_stats(classification_data):
    """Render stat counter cards."""
    total = len(classification_data)
    interacted = sum(1 for d in classification_data if d.get('Interaction Type', '').lower() == 'interacted')
    not_interacted = total - interacted
    unique_companies = len(set(d.get('Company Name', '') for d in classification_data))

    st.markdown(f'''
    <div class="stat-grid">
        <div class="stat-box">
            <div class="stat-value">{total}</div>
            <div class="stat-label">Emails Scanned</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">{unique_companies}</div>
            <div class="stat-label">Companies Detected</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">{interacted}</div>
            <div class="stat-label">Active Services</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)


def _render_results(logo_url_list, classification_data):
    """Display logos, stats, and the classified data table."""
    if not classification_data:
        st.info("No companies were detected in the scanned emails.")
        return

    # Stats
    _render_stats(classification_data)

    st.markdown(f'<div class="step-badge">{GACHENA_SHIELD} Detected Companies</div>',
                unsafe_allow_html=True)

    # Logos
    if logo_url_list:
        display_random_logos(logo_url_list)

    # Data table
    df_clean = pd.DataFrame(classification_data)
    display_df(df_clean)


def _validate_selection(single_row=True):
    """Validate user selection based on single or multiple row selections."""
    selected_rows = st.session_state.get('selected_rows')
    if selected_rows is None or selected_rows.empty:
        st.warning('Please select at least one company from the table.')
        return False
    if single_row and len(selected_rows) != 1:
        st.warning('Please select exactly one row to preview the email.')
        return False
    elif not single_row and len(selected_rows) < 1:
        st.warning('Please select at least one row for mass email send.')
        return False
    if 'Select Option' in selected_rows.columns and '-' in selected_rows['Select Option'].values:
        st.warning('Please choose a request type for all selected rows.')
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
    st.markdown(f'<div class="step-badge">{GACHENA_SHIELD} Step 4: Send GDPR Requests</div>',
                unsafe_allow_html=True)

    st.markdown('''
    <div class="gachena-card">
        <p style="color:#94A3B8; margin-bottom: 12px;">
        Select a company from the table above, choose your request type, then click <b>Run Bot</b> to
        generate and send a GDPR compliance email.
        </p>
        <p style="font-size:0.85em; color:#64748B;">
        <span class="gdpr-badge gdpr-art15">Art. 15 — Access</span>
        <span class="gdpr-badge gdpr-art16">Art. 16 — Modify</span>
        <span class="gdpr-badge gdpr-art17">Art. 17 — Erase</span>
        </p>
    </div>
    ''', unsafe_allow_html=True)

    col_preview, col_run, col_spacer = st.columns([1, 1, 1])

    with col_preview:
        email_preview = st.toggle(
            '👁️ Preview Email',
            value=True,
            help='Preview the email before sending (single selection only)'
        )

    with col_run:
        run_button = st.button(
            f'{GACHENA_SHIELD} Run Bot',
            type='primary',
            use_container_width=True
        )

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
    for _ in range(8):
        st.sidebar.markdown('')

    st.sidebar.markdown(
        f"""
        ---
        <div style="text-align:center; padding: 12px 0;">
            <span style="font-size:1.6em;">{GACHENA_SHIELD}</span>
            <br>
            <b style="color:{GACHENA_ACCENT}; font-size:1.05em;">GACHENA</b>
            <br>
            <span style="color:{GACHENA_MUTED}; font-size:0.78em;">
                Detect &bull; Protect &bull; Control<br>
                Your Digital Footprint
            </span>
            <br><br>
            <span style="color:{GACHENA_MUTED}; font-size:0.72em;">
                <i>"Gachena" means <b>Shield</b> in Afaan Oromo</i>
            </span>
            <br><br>
            <a href="https://events.mlh.io/events/13215-clash-of-code" target="_blank"
               style="color:{GACHENA_ACCENT}; font-size:0.8em; text-decoration:none;">
                MLH Clash of Code 🏆
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )


def main():
    # ── Sidebar: Demo mode toggle (before any auth) ──
    with st.sidebar:
        st.markdown(f'''
        <div style="text-align:center; padding: 16px 0 8px 0;">
            <span style="font-size:2em;">{GACHENA_SHIELD}</span>
            <br>
            <b style="font-size:1.2em; color:{GACHENA_ACCENT};">GACHENA</b>
            <br>
            <span style="font-size:0.75em; color:{GACHENA_MUTED};">
                GDPR Compliance Shield
            </span>
        </div>
        ''', unsafe_allow_html=True)

        demo_mode = st.toggle(
            '🎮 Demo Mode',
            value=True,
            help='Use sample data — no API keys or Google login needed'
        )

        st.caption(
            '🔄 Turn OFF to connect real Gmail account'
            if demo_mode else
            '🎮 Turn ON for sample data (no login needed)'
        )

    # ── Auth ──
    authenticator = initialize_authenticator(demo_mode=demo_mode)

    if not st.session_state.get('connected'):
        _render_sidebar_footer()
        return

    # ── Main Dashboard ──
    _render_header()
    _render_instruction_cards()

    st.markdown(f'<div class="step-badge">{GACHENA_SHIELD} Step 1: Configure & Scan</div>',
                unsafe_allow_html=True)

    # Advanced options
    day_range, ignored_categories, max_emails = _render_advanced_options()

    # Scan button
    col_scan, col_info = st.columns([1, 2])
    with col_scan:
        scan_button = st.button(
            f'🔍 Scan Inbox',
            type='primary',
            use_container_width=True
        )
    with col_info:
        st.caption('Click to analyze emails and detect companies holding your personal data.')

    if scan_button:
        if demo_mode:
            st.info("Running in demo mode with 18 sample emails.")
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
                with st.spinner("Scanning your inbox with AI..."):
                    email_data = process_emails(gmail_service, day_range, ignored_categories, max_emails)
            except Exception as e:
                st.error(f"Failed to scan inbox: {e}")
                return

        if not email_data:
            st.warning("No emails were found or processed. Try adjusting your date range.")
            return

        logo_url_list, classification_data = _extract_email_data(email_data)

        st.markdown(f'<div class="step-badge">{GACHENA_SHIELD} Step 2 & 3: Review & Select</div>',
                    unsafe_allow_html=True)
        _render_results(logo_url_list, classification_data)

    # Bot controls only show after a scan has been done
    if 'selected_rows' in st.session_state:
        st.markdown('<hr class="gachena-divider">', unsafe_allow_html=True)
        _render_bot_controls()

    # ── Footer ──
    st.markdown(f'''
    <hr class="gachena-divider">
    <div class="gachena-footer">
        {GACHENA_SHIELD} <b>GACHENA</b> &mdash; "Shield" in Afaan Oromo &mdash;
        Detect, Protect, Control Your Digital Footprint<br>
        <span style="font-size:0.8em;">
            Built with ❤️ for the
            <a href="https://events.mlh.io/events/13215-clash-of-code" target="_blank">MLH Clash of Code</a>
        </span>
    </div>
    ''', unsafe_allow_html=True)

    _render_sidebar_footer()


if __name__ == '__main__':
    main()