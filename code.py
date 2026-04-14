import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# --- CONFIGURATION ---
ADMIN_NUMBERS = ["9033004800", "9023564826"]
DATABASE_FILE = 'insurance_database.csv'

st.set_page_config(page_title="OM INSURANCE & INVESTMENT", layout="wide")
st.title("🏛️ OM INSURANCE & INVESTMENT")

# --- DATA LOADING ENGINE ---
def load_data():
    final_cols = [
        'sr.no.', 'date', 'ins. st. dt.', 'ins. end dt.', 'party name', 
        'm. no.', 'company', 'type of ins.', 'premium', 'gst', 'total', 
        'policy.no.', 'Renewed'
    ]

    # Load existing database or wait for upload
    if os.path.exists(DATABASE_FILE):
        df = pd.read_csv(DATABASE_FILE)
    else:
        st.info("👋 Welcome! Please upload your 'MAY REGISTER' CSV file to begin.")
        uploaded_file = st.file_uploader("Choose your CSV file", type="csv")
        
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
            mapping = {
                'Sr. No': 'sr.no.', 'Entry Date': 'date', 'Start Date': 'ins. st. dt.',
                'End Date': 'ins. end dt.', 'Party Name': 'party name', 
                'Company': 'company', 'Type': 'type of ins.', 'Premium': 'premium',
                'GST': 'gst', 'Total': 'total', 'Policy No.': 'policy.no.'
            }
            df = df.rename(columns=mapping)
            if 'm. no.' not in df.columns: df['m. no.'] = ""
            if 'Renewed' not in df.columns: df['Renewed'] = False
            df = df[[c for c in final_cols if c in df.columns]]
            df.to_csv(DATABASE_FILE, index=False)
            st.success("File processed! Please log in now.")
            st.stop()
        else:
            st.stop()

    # --- CRITICAL TYPE FIXER ---
    # This part fixes the 'StreamlitAPIException' by converting types
    df['ins. end dt.'] = pd.to_datetime(df['ins. end dt.'], errors='coerce')
    df['Renewed'] = df['Renewed'].astype(bool)
    df['m. no.'] = df['m. no.'].astype(str).replace('nan', '')
    
    return df

# --- ADMIN LOGIN ---
if "auth" not in st.session_state:
    st.session_state.auth = False

with st.sidebar:
    st.header("Admin Access")
    pwd = st.text_input("Admin Mobile Number", type="password")
    if st.button("Login"):
        if pwd in ADMIN_NUMBERS:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Invalid Admin Number")

if not st.session_state.auth:
    st.warning("Please log in from the sidebar to view policy data.")
    st.stop()

df = load_data()

# --- TABS ---
tab1, tab2 = st.tabs(["📊 Policy Manager", "🔔 Expiry Alerts"])

with tab1:
    st.subheader("Master Policy Register")
    
    # Using the Data Editor with correct types
    edited_df = st.data_editor(
        df, 
        num_rows="dynamic", 
        width="stretch",
        column_config={
            "Renewed": st.column_config.CheckboxColumn("Renewed", default=False),
            "ins. end dt.": st.column_config.DateColumn(
                "Expiry Date",
                format="DD-MM-YYYY",
                step=1,
            ),
            "m. no.": st.column_config.TextColumn("Mobile No.")
        }
    )
    
    if st.button("💾 Save All Changes"):
        # Before saving, we convert dates back to string so CSV can handle it
        save_df = edited_df.copy()
        save_df.to_csv(DATABASE_FILE, index=False)
        st.success("Database Updated!")

with tab2:
    st.subheader("Policies Expiring Within 7 Days")
    today = datetime.now().date()
    next_week = today + timedelta(days=7)
    
    # Filter: Not Renewed + Expiring in 7 days
    # We compare only the date part to avoid time-zone errors
    expiring = edited_df[
        (edited_df['ins. end dt.'].dt.date >= today) & 
        (edited_df['ins. end dt.'].dt.date <= next_week) & 
        (edited_df['Renewed'] == False)
    ]
    
    if not expiring.empty:
        st.error(f"Attention: {len(expiring)} policies are expiring soon!")
        st.dataframe(expiring[['party name', 'ins. end dt.', 'm. no.', 'company']])
        
        if st.button("🚀 Send WhatsApp/SMS Notifications"):
            for _, row in expiring.iterrows():
                if row['m. no.'] and str(row['m. no.']).strip() != "":
                    dt_str = row['ins. end dt.'].strftime('%d-%m-%Y')
                    st.info(f"Notification ready for {row['party name']} ({row['m. no.']})")
                    # (Logic for Twilio/WhatsApp API would go here)
                else:
                    st.warning(f"No mobile number for {row['party name']}")
    else:
        st.success("No policies are expiring this week.")
