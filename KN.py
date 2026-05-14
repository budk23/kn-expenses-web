import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import base64
import json

# 1. Page Configuration
st.set_page_config(page_title="Total Expenses", layout="wide")

def get_current_user():
    # 1. เช็ก Localhost (ยอมให้ผ่านเลยเพื่อเทสในเครื่อง)
    if "localhost" in st.context.headers.get("host", ""):
        return "bkorn2303@gmail.com" 
    
    # 2. เช็คจาก st.user (วิธีหลักสำหรับ Public App)
    if hasattr(st, "user") and st.user.get("is_logged_in"):
        return st.user.get("email")
    
    # 3. ดึงจาก Header และจัดการแกะรหัสข้อความ (กรณีรันผ่านหลังบ้าน)
    user_data = st.context.headers.get("X-Streamlit-User")
    if user_data:
        try:
            cleaned_data = user_data.strip()
            cleaned_data += "=" * ((4 - len(cleaned_data) % 4) % 4)
            decoded = base64.b64decode(cleaned_data).decode("utf-8")
            return json.loads(decoded).get("email")
        except Exception:
            return user_data
            
    return None

# ตรวจสอบสถานะการล็อกอินผ่านโมดูลของ Streamlit
if not st.user.is_logged_in:
    st.info("Please log in to Streamlit Cloud to access this app.")
    # สั่งแสดงปุ่มล็อกอินสีแดงของ Streamlit Cloud บนหน้าเว็บเมื่อเป็น Public App
    st.login() 
    st.stop()

# รายชื่อผู้มีสิทธิ์
authorized_users = ["bkorn2303@gmail.com", "noeynim.nnim@gmail.com"]

current_user = get_current_user()

if current_user not in authorized_users:
    st.error(f"Access Denied: {current_user} is not authorized.")
    st.stop()

st.success(f"Welcome, {current_user}")

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

    # --- ดึงข้อมูลมาแสดงผล ---
    records = sheet.get_all_records()
    df = pd.DataFrame(records)

    if not df.empty:
        # แปลงคอลัมน์ Date เป็น datetime เพื่อใช้ทำสรุปรายเดือน
        df['Date'] = pd.to_datetime(df['Date'])
        
        # --- 1. Monthly Summary Dashboard ---
        st.divider()
        st.subheader("📅 Monthly Summary")
        
        # สร้างตัวเลือกเดือน
        df['Month'] = df['Date'].dt.strftime('%Y-%m')
        available_months = sorted(df['Month'].unique(), reverse=True)
        selected_month = st.selectbox("Select Month to View:", available_months)
        
        # กรองข้อมูลตามเดือนที่เลือก
        monthly_df = df[df['Month'] == selected_month]
        
        col_m1, col_m2 = st.columns(2)
        m_ked = monthly_df[monthly_df['Payer'] == 'Ked']['Total'].sum()
        m_noey = monthly_df[monthly_df['Payer'] == 'Noey']['Total'].sum()
        
        col_m1.metric(f"Ked's Total ({selected_month})", f"{m_ked:,.2f} ฿")
        col_m2.metric(f"Noey's Total ({selected_month})", f"{m_noey:,.2f} ฿")

        # --- 2. Overall Unpaid & Settled Up All ---
        st.divider()
        st.subheader("💰 Unpaid Balance")
        
        unpaid_df = df[df['Status'] == 'unpaid']
        ked_share = unpaid_df[unpaid_df['Payer'] == 'Ked']['Split_Amount'].sum()
        noey_share = unpaid_df[unpaid_df['Payer'] == 'Noey']['Split_Amount'].sum()

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

        # --- ปุ่ม Settled Up All ---
        if not unpaid_df.empty:
            if st.button("✅ Mark All as Settled (Paid)", use_container_width=True, type="primary"):
                # หาตำแหน่งแถวที่เป็น unpaid ทั้งหมดใน Google Sheets
                # (df.index เริ่มที่ 0, Header อยู่แถว 1 ดังนั้นต้อง +2)
                for index in unpaid_df.index:
                    gsheet_row_idx = int(index) + 2
                    # คอลัมน์ F คือ Status (ลำดับที่ 6)
                    sheet.update_cell(gsheet_row_idx, 6, "paid")
                
                st.success("All transactions marked as paid!")
                st.rerun()

        st.divider()
        st.subheader("📝 All Transactions")
        st.dataframe(df.drop(columns=['Month']), use_container_width=True)


    # --- 3. Manage Section (Edit/Delete) ---
        st.divider()
        with st.expander("🛠️ Manage Transactions (Edit/Delete)"):
            # ดึงรายชื่อจากคอลัมน์ 'Item' และ 'Total' ตามในภาพ image_ccc497.png
            row_options = []
            for i in range(len(df)):
                item = df.iloc[i].get('Item', 'Unknown')
                total = df.iloc[i].get('Total', 0)
                row_options.append(f"Row {i+1}: {item} ({total} ฿)")

            row_to_edit = st.selectbox("Select row to manage:", options=df.index, format_func=lambda x: row_options[x])
            
            current_row_data = df.iloc[row_to_edit]
            
            col_ed1, col_ed2, col_ed3, col_ed4 = st.columns(4)
            
            # แก้ไขชื่อ Key ให้ตรงกับ Sheets เป๊ะๆ
            new_item = col_ed1.text_input("Edit Item", value=str(current_row_data.get('Item', '')))
            new_total = col_ed2.number_input("Edit Total", value=float(current_row_data.get('Total', 0)), step=1.0)
            new_payer = col_ed3.selectbox("Edit Payer", ["Ked", "Noey"], 
                                         index=0 if current_row_data.get('Payer') == "Ked" else 1)
            new_status = col_ed4.selectbox("Edit Status", ["unpaid", "paid"], 
                                          index=0 if current_row_data.get('Status') == "unpaid" else 1)

            btn_col1, btn_col2, _ = st.columns([1, 1, 2])
            
            if btn_col1.button("✅ Update Row", use_container_width=True):
                gsheet_row_idx = int(row_to_edit) + 2
                # เรียงข้อมูลให้ตรงตามลำดับคอลัมน์ใน image_ccc497.png
                # Date(A), Item(B), Total(C), Payer(D), Split_Amount(E), Status(F)
                raw_date = current_row_data.get('Date', '')
                if hasattr(raw_date, 'strftime'):
                    clean_date = raw_date.strftime('%Y-%m-%d')
                else:
                    clean_date = str(raw_date)
                updated_values = [
                    clean_date, 
                    new_item, 
                    new_total, 
                    new_payer, 
                    new_total/2, 
                    new_status
                ]
                sheet.update(f"A{gsheet_row_idx}:F{gsheet_row_idx}", [updated_values])
                st.success(f"Updated row {row_to_edit + 1} successfully!")
                st.rerun()

            if btn_col2.button("🗑️ Delete Row", type="primary", use_container_width=True):
                gsheet_row_idx = int(row_to_edit) + 2
                sheet.delete_rows(gsheet_row_idx)
                st.success(f"Deleted row {row_to_edit + 1} successfully!")
                st.rerun()
    else:
        st.info("No records found.")

except Exception as e:
    st.error(f"Connection Error: {e}")
