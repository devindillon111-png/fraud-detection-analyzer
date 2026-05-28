import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# --- Page Config ---
st.set_page_config(
    page_title="Fraud Detection Analyzer",
    page_icon="🔍",
    layout="wide"
)

# --- Load Data ---
@st.cache_data
def load_data():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    flagged_path = os.path.join(script_dir, "..", "outputs", "flagged_transactions.csv")
    full_path = os.path.join(script_dir, "..", "data", "transactions.csv")
    flagged = pd.read_csv(flagged_path)
    full = pd.read_csv(full_path)
    flagged['Date'] = pd.to_datetime(flagged['Date'])
    full['Date'] = pd.to_datetime(full['Date'])
    return flagged, full

flagged_df, full_df = load_data()

# --- Header ---
st.title("🔍 Fraud Detection Analyzer")
st.markdown("**Internal Audit Dashboard** | Anomaly & Risk Flagging System")
st.markdown("---")

# --- Top KPI Metrics ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Transactions", f"{len(full_df):,}")
with col2:
    st.metric("Flagged Transactions", f"{len(flagged_df):,}")
with col3:
    flag_rate = len(flagged_df) / len(full_df) * 100
    st.metric("Flag Rate", f"{flag_rate:.1f}%")
with col4:
    flagged_amount = flagged_df['Amount'].sum()
    st.metric("$ at Risk", f"${flagged_amount:,.0f}")

st.markdown("---")

# --- Sidebar Filters ---
st.sidebar.header("🎛️ Filters")

departments = ["All"] + sorted(flagged_df['Department'].dropna().unique().tolist())
selected_dept = st.sidebar.selectbox("Department", departments)

min_amount = float(flagged_df['Amount'].min())
max_amount = float(flagged_df['Amount'].max())
amount_range = st.sidebar.slider(
    "Transaction Amount ($)",
    min_value=min_amount,
    max_value=max_amount,
    value=(min_amount, max_amount)
)

flag_types = st.sidebar.multiselect(
    "Flag Types",
    options=["Weekend Transaction", "Round Number", "Threshold Amount", "Missing Vendor", "ML Anomaly"],
    default=["Weekend Transaction", "Round Number", "Threshold Amount", "Missing Vendor", "ML Anomaly"]
)

# --- Apply Filters ---
filtered = flagged_df.copy()
if selected_dept != "All":
    filtered = filtered[filtered['Department'] == selected_dept]
filtered = filtered[
    (filtered['Amount'] >= amount_range[0]) &
    (filtered['Amount'] <= amount_range[1])
]

st.markdown(f"### Showing {len(filtered):,} flagged transactions")

# --- Charts Row ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📊 Flagged Transactions by Department")
    dept_counts = filtered['Department'].value_counts()
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    dept_counts.plot(kind='bar', ax=ax1, color='steelblue', edgecolor='black')
    ax1.set_xlabel("Department")
    ax1.set_ylabel("# Flagged Transactions")
    ax1.set_title("Flags by Department")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    st.pyplot(fig1)

with col_right:
    st.subheader("📈 Flag Distribution by Type")
    flag_col_map = {
        "Weekend Transaction": "Is_Weekend",
        "Round Number": "Is_Round_Number",
        "Threshold Amount": "Is_Threshold",
        "Missing Vendor": "Missing_Vendor",
        "ML Anomaly": "ML_Anomaly"
    }
    flag_counts = {}
    for label, col in flag_col_map.items():
        if col in filtered.columns:
            flag_counts[label] = filtered[col].sum()
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    ax2.bar(flag_counts.keys(), flag_counts.values(), color='tomato', edgecolor='black')
    ax2.set_ylabel("Count")
    ax2.set_title("Transactions Flagged by Rule Type")
    plt.xticks(rotation=30, ha='right')
    plt.tight_layout()
    st.pyplot(fig2)

# --- Benford's Law Chart ---
st.markdown("---")
st.subheader("📐 Benford's Law Analysis")

col_b1, col_b2 = st.columns([2, 1])
with col_b1:
    benford_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs", "benford_analysis.png")
    if os.path.exists(benford_path):
        st.image(benford_path, caption="Benford's Law: Expected vs Actual First Digit Distribution", use_column_width=True)
    else:
        st.warning("Run benford_analysis.py first to generate the chart.")

with col_b2:
    st.markdown("""
    **What is Benford's Law?**
    
    In legitimate financial data, the first digit of transaction amounts follows a predictable pattern — the number 1 appears ~30% of the time, 2 appears ~18%, and so on.
    
    When actual data **deviates significantly** from this expected distribution, it can indicate:
    - Fabricated transactions
    - Round-number manipulation
    - Data entry fraud
    
    Auditors use this as an early warning signal.
    """)

# --- Anomaly Detection Chart ---
st.markdown("---")
st.subheader("🤖 ML Anomaly Detection Results")
anomaly_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs", "anomaly_detection.png")
if os.path.exists(anomaly_path):
    st.image(anomaly_path, caption="Isolation Forest Anomaly Detection — 4-Panel Analysis", use_column_width=True)
else:
    st.warning("Run anomaly_detection.py first to generate the chart.")

# --- Flagged Transactions Table ---
st.markdown("---")
st.subheader("📋 Flagged Transactions — Detailed View")

display_cols = ['Date', 'Transaction_ID', 'Amount', 'Department', 'Vendor_Name',
                'Employee_ID', 'Is_Weekend', 'Is_Round_Number', 'Is_Threshold',
                'Missing_Vendor', 'ML_Anomaly', 'Rule_Flag_Count']
available_cols = [c for c in display_cols if c in filtered.columns]

st.dataframe(
    filtered[available_cols].sort_values('Rule_Flag_Count', ascending=False),
    use_container_width=True,
    height=400
)

# --- Download Button ---
csv = filtered[available_cols].to_csv(index=False)
st.download_button(
    label="⬇️ Download Filtered Results as CSV",
    data=csv,
    file_name="filtered_flagged_transactions.csv",
    mime="text/csv"
)

st.markdown("---")
st.caption("Fraud Detection Analyzer | Built with Python, scikit-learn & Streamlit | Devin Dillon")