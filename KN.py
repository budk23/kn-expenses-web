import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import os

# 1. Page Configuration
st.set_page_config(page_title="Total Expenses", layout="wide")


def get_secret(key_name: str):
    """Read from Streamlit secrets first, then fallback to environment variables."""
    if key_name in st.secrets:
        return st.secrets[key_name]
    return os.getenv(key_name)


def require_app_password():
    """Optional lightweight access gate for public deployments."""
    expected_password = os.getenv("APP_PASSWORD")
    if not expected_password:
        return

    if st.session_state.get("authenticated", False):
        return

    st.title("🔒 Private App")
    st.write("Enter password to access this app")
    password_input = st.text_input("Password", type="password")

    if st.button("Login"):
        if password_input == expected_password:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password")

    st.stop()

def connect_to_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Construct credentials using Streamlit Secrets
    private_key = get_secret("private_key")
    if private_key:
        # Handle environments where newline is stored as escaped \n.
        private_key = private_key.replace("\\n", "\n")

    creds_info = {
        "type": "service_account",
        "project_id": get_secret("project_id"),
        "private_key_id": get_secret("private_key_id"),
        "private_key": private_key,
        "client_email": get_secret("client_email"),
        "client_id": get_secret("client_id"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": get_secret("client_x509_cert_url")
    }

    missing_keys = [k for k, v in creds_info.items() if not v]
    if missing_keys:
        raise ValueError(f"Missing required secret/env keys: {', '.join(missing_keys)}")
    
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
    client = gspread.authorize(creds)
    # Ensure your Google Sheet is named "Budget"
    return client.open("Budget").sheet1

try:
    require_app_password()
    sheet = connect_to_sheet()
    st.title("💸 Total Expenses")

    # Add Transaction
    with st.expander("➕ Add New Transaction", expanded=True):
        with st.form("add_expense", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            item_name = col1.text_input("Description")
            total_val = col2.number_input("Amount (THB)", min_value=0.0, step=1.0)
            payer_name = col3.selectbox("Who paid?", ["Ked", "Noey"])
            
            submit = st.form_submit_button("Save to Sheets")
            
            if submit and item_name:
                date_str = datetime.now().strftime("%Y-%m-%d")
                split_val = total_val / 2
                new_data = [date_str, item_name, total_val, payer_name, split_val, "unpaid"]
                sheet.append_row(new_data)
                st.success(f"Successfully added: {item_name}")
                st.rerun()

    # Dashboard
    records = sheet.get_all_records()
    df = pd.DataFrame(records)

    if not df.empty:
        unpaid_df = df[df['Status'] == 'unpaid']
        ked_share = unpaid_df[unpaid_df['Payer'] == 'Ked']['Split_Amount'].sum()
        noey_share = unpaid_df[unpaid_df['Payer'] == 'Noey']['Split_Amount'].sum()

        st.divider()
        st.subheader("📊 Summary")
        m1, m2, m3 = st.columns(3)
        m1.metric("Ked's Paid (Share)", f"{ked_share:,.2f} ฿")
        m2.metric("Noey's Paid (Share)", f"{noey_share:,.2f} ฿")
        
        diff = ked_share - noey_share
        if diff > 0:
            m3.warning(f"📢 Noey owes Ked: {abs(diff):,.2f} ฿")
        elif diff < 0:
            m3.warning(f"📢 Ked owes Noey: {abs(diff):,.2f} ฿")
        else:
            m3.success("All settled up!")

        st.divider()
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No records found.")

except Exception as e:
    st.error(f"Connection Error: {e}")