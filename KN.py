import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="Total Expenses", layout="wide")

def connect_to_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # 1. ดึงข้อมูลแบบยกกลุ่มก้อนมาจากคำสั่งเดียว
    creds_info = dict(st.secrets["gcp_service_account"])
    
    # 2. บังคับเปลี่ยนตัวอักษร \n ให้เป็นการตัดบรรทัดจริงเพื่อป้องกันปัญหาบน Cloud
    creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
    
    # 3. ใส่ลิงก์มาตรฐานของ Google กลับไปให้ครบถ้วนในกรณีที่ระบบหาไม่เจอ
    creds_info["auth_uri"] = "https://accounts.google.com/o/oauth2/auth"
    creds_info["token_uri"] = "https://oauth2.googleapis.com/token"
    creds_info["auth_provider_x509_cert_url"] = "https://www.googleapis.com/oauth2/v1/certs"


    # # Construct credentials using Streamlit Secrets
    # creds_info = {
    #     "type": "service_account",
    #     "project_id": st.secrets["project_id"],
    #     "private_key_id": st.secrets["private_key_id"],
    #     "private_key": st.secrets["private_key"],
    #     "client_email": st.secrets["client_email"],
    #     "client_id": st.secrets["client_id"],
    #     "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    #     "token_uri": "https://oauth2.googleapis.com/token",
    #     "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    #     "client_x509_cert_url": st.secrets["client_x509_cert_url"]
    # }
    
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

        # --- 3. Manage Section (Edit/Delete) ---
        st.divider()
        with st.expander("🛠️ Manage Transactions (Edit/Delete)"):
            # ให้เลือกแถวที่จะจัดการ (ใช้ index ของ dataframe)
            row_to_edit = st.selectbox("Select row to manage:", options=df.index, format_func=lambda x: f"Row {x+1}: {df.iloc[x]['Description']} ({df.iloc[x]['Amount']} ฿)")
            
            # ดึงข้อมูลแถวที่เลือกมาใส่ในตัวแปร
            current_row_data = df.iloc[row_to_edit]
            
            col_ed1, col_ed2, col_ed3, col_ed4 = st.columns(4)
            new_desc = col_ed1.text_input("Edit Description", value=current_row_data['Description'])
            new_amt = col_ed2.number_input("Edit Amount", value=float(current_row_data['Amount']), step=1.0)
            new_payer = col_ed3.selectbox("Edit Payer", ["Ked", "Noey"], index=0 if current_row_data['Payer'] == "Ked" else 1)
            new_status = col_ed4.selectbox("Edit Status", ["unpaid", "paid"], index=0 if current_row_data['Status'] == "unpaid" else 1)

            btn_col1, btn_col2, _ = st.columns([1, 1, 2])
            
            # ปุ่มแก้ไข
            if btn_col1.button("✅ Update Row", use_container_width=True):
                # แถวใน Google Sheets จะเริ่มที่ 2 (เพราะแถว 1 คือ Header)
                gsheet_row_idx = int(row_to_edit) + 2
                updated_values = [
                    current_row_data['Date'], 
                    new_desc, 
                    new_amt, 
                    new_payer, 
                    new_amt/2, 
                    new_status
                ]
                # อัปเดตทั้งแถว
                sheet.update(f"A{gsheet_row_idx}:F{gsheet_row_idx}", [updated_values])
                st.success(f"Updated row {row_to_edit + 1} successfully!")
                st.rerun()

            # ปุ่มลบ
            if btn_col2.button("🗑️ Delete Row", type="primary", use_container_width=True):
                gsheet_row_idx = int(row_to_edit) + 2
                sheet.delete_rows(gsheet_row_idx)
                st.success(f"Deleted row {row_to_edit + 1} successfully!")
                st.rerun()
    else:
        st.info("No records found.")

except Exception as e:
    st.error(f"Connection Error: {e}")
