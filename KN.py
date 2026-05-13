import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="Total Expenses", layout="wide")

def connect_to_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Construct credentials using Streamlit Secrets
    creds_info = {
        "type": "service_account",
        "project_id": st.secrets["kn-expenses-web"],
        "private_key_id": st.secrets["354a5766bc079f82787a0b0d22dcb55de0a30f98"],
        "private_key": st.secrets["-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDrtvBknj178jKS\n24F5jO+z0jnvq4rTJZQgVBxE5RhlY3axPsFoDeiFc4gQ2z4UfVJl/xtnC7xrZtWW\nVW/aq3H3oR66j0HEHBsBT8vzDfKJVkuPjHPoGgcL5CDHeGYFbFEsd+xuk0vNwGww\n2IBKOaaDGRih2scueDR4QQDlz3w95+npCdcVJ/hoQ42BFNenqoQjFS0YwG5g/E4l\nNsY6BuX/WGF8+f1B8TrwvPcjwo/30tZB02XuLBnP/BbsMZT9OLFy25cEV1fpqEOB\n2OvRcrUeQo/3ppHTQl6X5sofwRzYq1MZn/uzuXxDmqomgbV+u+3tg3x8IwMssagn\nhHRJ2443AgMBAAECggEAFyo4CctmA3j+m2F9zJzwhF2UBV0jHDPEkOtzM8TIAal6\nuq841qm3QOuPuF2zhilNdb9SdBgP1luZgK1jfBFT9qAbov39L/FgfgqCN/Vrm9pN\nPA2ePnXVshzN/oxzNPPmLlaYIm3QtKcaetpsETSv4Tu601KVjJg89Sx+PWzcqutK\nz+yjnP9r9hCCnYkAd8GbDaXBBizGZ29/oDkz20wq2qu6OmPFlvSyYWwhbBbtNr9g\ng6UI1nJQTSqDmT3I2Oz4uk+7Y0GQ4ELGlKgBkTAQB6iic/5O4I3YkHLEeNBDYaak\ne+88F3zdUtFP35nkYeO1sIJNIgwZZpr49CkNpGUXYQKBgQD4Dh2AN2w+KIMKHm18\nqun7gGWOho/eF4K7n8AoCk/jObYtbbgrvD5Nja9yx/yf0G/1vMLEel3cqEPuyy8n\nJjEZIVtqku+vn9eiaNQqIpikSJ9d2WH6skDnZAy2qDhocT5slhWf/KEYtpeYdqU/\nRAvrDWCitVQKQHOe8wbsyqgrmQKBgQDzQ6PHZG+c4gJBRTPtwfnYBw5S+WiVoZyx\ngkbxvfu3Aa6fMAJNiCbiOfXLQljzqiG/QBTTIXuPnK1J3vlIm65Bq8MYAAHfR3hv\nnxpllJtSiOzNt74GH1xPcYNxa4cN1tLBJ6EKLYEvEgIWcmT7T/ZGYm24+/6cmex9\n4o6ueKcqTwKBgBAQOfDXpfbQgMvi9IwiNUzIH8t/A0oKk7i6u6LcKBg64IVImaib\nZB15k2cHdGCVCusK8kHu+q0TaHLKTZ9nZb6O3nCkW0kwPLKTv0mLO/9HhKp7LVEi\nwfk6DWi2tBBvZO97OKNHpNcI3ABPjpvuOCdckml2/J49Vj9w1X34EbPhAoGBAK7l\nPIUIkq5KV7CxnmocAhLsz8GcCzM5JD0DGxqGqsiibveIPr+bWclgPnVKWEWnVef4\nnIBHHFzeGkB4DOXE9/3DDdrddnsfGVm3G/VYaGtogkhNCFPCjE2ZoRUUZ97tSk0Q\nvtlgafZ7jgCxciS1Eqz760MJ+b6Bc+P11PtfR2BFAoGBAK/cAIxugtjxd6/FY2Z6\nybz8Rx9u7EMZuJr2kxbX/t2Xs1AAJy9ENYDF0dSxny4GmBX5laSuK0wrGejMMQ89\nzHIBQ7l8hcabgjHIdoO82UYUwrPpMLRW8D3kEvQY5zjcHukcLHWf/6shrRWVaQ6/\nHczHZtLrbzWVOf/G0dr2+H1x\n-----END PRIVATE KEY-----\n"],
        "client_email": st.secrets["kedschit@kn-budget.iam.gserviceaccount.com"],
        "client_id": st.secrets["118230820714069243770"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": st.secrets["https://www.googleapis.com/robot/v1/metadata/x509/kedschit%40kn-budget.iam.gserviceaccount.com"]
    }
    
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
    client = gspread.authorize(creds)
    # Ensure your Google Sheet is named "Budget"
    return client.open("Budget").sheet1

try:
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
