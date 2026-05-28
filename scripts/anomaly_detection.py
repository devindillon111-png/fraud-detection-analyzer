import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder
import matplotlib.pyplot as plt
import os

# --- Load data ---
script_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(script_dir, "..", "data", "transactions.csv")
output_dir = os.path.join(script_dir, "..", "outputs")
os.makedirs(output_dir, exist_ok=True)

df = pd.read_csv(data_path)
df['Date'] = pd.to_datetime(df['Date'])

print(f"Dataset loaded: {df.shape[0]} transactions\n")

# --- PART 1: Rule-Based Flagging ---
print("=" * 50)
print("PART 1: RULE-BASED ANOMALY FLAGS")
print("=" * 50)

df['Is_Weekend'] = df['Date'].dt.dayofweek >= 5
weekend_count = df['Is_Weekend'].sum()
print(f"\n Flag Weekend transactions: {weekend_count}")

round_numbers = [100, 200, 250, 500, 750, 1000, 1500, 2000, 2500, 5000]
df['Is_Round_Number'] = df['Amount'].isin(round_numbers)
round_count = df['Is_Round_Number'].sum()
print(f"Flag Round number amounts: {round_count}")

thresholds = [499.99, 999.99, 1999.99, 2499.99, 4999.99]
df['Is_Threshold'] = df['Amount'].isin(thresholds)
threshold_count = df['Is_Threshold'].sum()
print(f"Flag Threshold manipulation amounts: {threshold_count}")

df['Missing_Vendor'] = df['Vendor_Name'].isna() | (df['Vendor_Name'] == '')
missing_vendor_count = df['Missing_Vendor'].sum()
print(f"Flag Missing vendor names: {missing_vendor_count}")

df['Missing_Employee'] = df['Employee_ID'].isna() | (df['Employee_ID'] == '')
missing_emp_count = df['Missing_Employee'].sum()
print(f"Flag Missing employee IDs: {missing_emp_count}")

df['Is_Duplicate_Amount'] = df.duplicated(subset=['Amount'], keep=False)
dup_count = df['Is_Duplicate_Amount'].sum()
print(f"Flag Duplicate transaction amounts: {dup_count}")

df['Rule_Flag_Count'] = (
    df['Is_Weekend'].astype(int) +
    df['Is_Round_Number'].astype(int) +
    df['Is_Threshold'].astype(int) +
    df['Missing_Vendor'].astype(int) +
    df['Missing_Employee'].astype(int) +
    df['Is_Duplicate_Amount'].astype(int)
)

high_risk = df[df['Rule_Flag_Count'] >= 2]
print(f"\nHigh risk transactions with 2+ flags: {len(high_risk)}")

# --- PART 2: Isolation Forest ML ---
print("\n" + "=" * 50)
print("PART 2: ISOLATION FOREST ML MODEL")
print("=" * 50)

df['Day_of_Week'] = df['Date'].dt.dayofweek
df['Month'] = df['Date'].dt.month
df['Vendor_Missing'] = df['Missing_Vendor'].astype(int)
df['Employee_Missing'] = df['Missing_Employee'].astype(int)

le = LabelEncoder()
df['Department_Encoded'] = le.fit_transform(df['Department'].fillna('Unknown'))

features = ['Amount', 'Day_of_Week', 'Month', 'Vendor_Missing',
            'Employee_Missing', 'Department_Encoded']
X = df[features]

print("\nTraining Isolation Forest model...")
model = IsolationForest(contamination=0.08, random_state=42, n_estimators=100)
df['ML_Anomaly'] = model.fit_predict(X)
df['ML_Anomaly'] = df['ML_Anomaly'].map({1: 0, -1: 1})

ml_anomaly_count = df['ML_Anomaly'].sum()
print(f"ML detected anomalies: {ml_anomaly_count}")

df['Combined_Flag'] = ((df['Rule_Flag_Count'] >= 1) | (df['ML_Anomaly'] == 1)).astype(int)
combined_count = df['Combined_Flag'].sum()
print(f"\nTotal flagged transactions: {combined_count}")
print(f"That is {combined_count/len(df)*100:.1f}% of all transactions")

# --- PART 3: Department Summary ---
print("\n" + "=" * 50)
print("PART 3: FLAG SUMMARY BY DEPARTMENT")
print("=" * 50)

dept_summary = df.groupby('Department').agg(
    Total_Transactions=('Transaction_ID', 'count'),
    Flagged_Transactions=('Combined_Flag', 'sum'),
    Total_Amount=('Amount', 'sum'),
    Avg_Amount=('Amount', 'mean')
).round(2)
dept_summary['Flag_Rate_%'] = (dept_summary['Flagged_Transactions'] /
                                dept_summary['Total_Transactions'] * 100).round(1)
print(dept_summary.to_string())

# --- PART 4: Charts ---
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Anomaly Detection Results\nFraud Detection Analyzer', fontsize=14)

flag_names = ['Weekend', 'Round Number', 'Threshold', 'Missing Vendor',
              'Missing Employee', 'Duplicate Amount']
flag_counts = [weekend_count, round_count, threshold_count,
               missing_vendor_count, missing_emp_count, dup_count]
axes[0,0].bar(flag_names, flag_counts, color='#FF5722', alpha=0.8)
axes[0,0].set_title('Rule-Based Flags by Type')
axes[0,0].set_ylabel('Count')
axes[0,0].tick_params(axis='x', rotation=45)

labels = ['Normal', 'ML Anomaly']
sizes = [len(df) - ml_anomaly_count, ml_anomaly_count]
axes[0,1].pie(sizes, labels=labels, autopct='%1.1f%%',
              colors=['#2196F3', '#FF5722'])
axes[0,1].set_title('ML Anomaly Detection Results')

dept_summary['Flag_Rate_%'].plot(kind='bar', ax=axes[1,0],
                                  color='#FF9800', alpha=0.8)
axes[1,0].set_title('Flag Rate by Department (%)')
axes[1,0].set_ylabel('Flag Rate %')
axes[1,0].tick_params(axis='x', rotation=45)

normal_amounts = df[df['Combined_Flag'] == 0]['Amount']
flagged_amounts = df[df['Combined_Flag'] == 1]['Amount']
axes[1,1].hist(normal_amounts, bins=50, alpha=0.6, label='Normal', color='#2196F3')
axes[1,1].hist(flagged_amounts, bins=50, alpha=0.6, label='Flagged', color='#FF5722')
axes[1,1].set_title('Amount Distribution: Normal vs Flagged')
axes[1,1].set_xlabel('Amount ($)')
axes[1,1].set_ylabel('Frequency')
axes[1,1].legend()

plt.tight_layout()
output_path = os.path.join(output_dir, "anomaly_detection.png")
plt.savefig(output_path, dpi=150)
print(f"\nChart saved to outputs folder")
plt.show()

# --- Save flagged transactions ---
flagged_df = df[df['Combined_Flag'] == 1][[
    'Transaction_ID', 'Date', 'Amount', 'Vendor_Name',
    'Employee_ID', 'Department', 'Approval_Status',
    'Rule_Flag_Count', 'ML_Anomaly'
]]
flagged_path = os.path.join(output_dir, "flagged_transactions.csv")
flagged_df.to_csv(flagged_path, index=False)
print(f"Flagged transactions saved to outputs folder")
print(f"\nTotal flagged: {len(flagged_df)} transactions saved for review")