import pandas as pd
import random
import csv
from datetime import datetime, timedelta

random.seed(42)

# --- Configuration ---
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(script_dir, "..", "data", "transactions.csv")
NUM_ROWS = 10000

# Data pools
vendors = [
    "Office Depot", "Staples", "Amazon Business", "Dell Technologies",
    "Microsoft", "Adobe Systems", "Zoom Communications", "Salesforce",
    "FedEx", "UPS", "USPS", "WeWork", "Regus", "Hilton Hotels",
    "Marriott", "Delta Airlines", "United Airlines", "Enterprise Rent-A-Car",
    "Hertz", "Uber Business", "Lyft Business", "Grubhub Corporate",
    "Seamless", "Home Depot", "Grainger", "Uline", "Pitney Bowes",
    "Xerox", "Ricoh", "Canon", "HP Inc", "Lenovo", "Apple Business",
    "Cisco Systems", "Verizon Business", "AT&T Business", "Comcast Business",
    "Iron Mountain", "Shred-it", "Cintas", "ADP", "Paychex",
    "", "", ""  # blank vendors = missing values (suspicious)
]

departments = ["Finance", "IT", "Operations", "HR", "Marketing", "Sales", "Legal", "Procurement"]

account_codes = ["6100", "6200", "6300", "6400", "6500", "6600", "6700", "7100", "7200", "8000"]

approval_statuses = ["Approved", "Approved", "Approved", "Approved", "Pending", "Rejected", ""]  # weighted toward Approved

# --- Date helpers ---
start_date = datetime(2023, 1, 1)
end_date = datetime(2023, 12, 31)

def random_date(start, end, force_weekend=False):
    delta = end - start
    while True:
        random_days = random.randint(0, delta.days)
        d = start + timedelta(days=random_days)
        if force_weekend and d.weekday() < 5:
            continue
        return d.strftime("%Y-%m-%d")

# --- Amount generators ---
def normal_amount():
    """Most transactions: realistic business amounts"""
    return round(random.uniform(12.50, 4800.00), 2)

def round_number_amount():
    """Suspicious: perfectly round numbers"""
    rounds = [100, 200, 250, 500, 750, 1000, 1500, 2000, 2500, 5000]
    return float(random.choice(rounds))

def threshold_amount():
    """Suspicious: just below approval thresholds"""
    thresholds = [499.99, 999.99, 1999.99, 2499.99, 4999.99]
    return random.choice(thresholds)

def benford_skewed_amount():
    """Normal: Benford's Law says leading digit 1 should appear ~30% of time"""
    # Use log-uniform distribution to naturally follow Benford's Law
    magnitude = random.uniform(1, 4)  # $10 to $9999
    amount = 10 ** magnitude
    return round(amount, 2)

# --- Row generator ---
def generate_row(txn_id, suspicious_type=None):
    emp_id = f"EMP{random.randint(100, 999)}" if random.random() > 0.02 else ""  # 2% missing
    
    if suspicious_type == "weekend":
        date = random_date(start_date, end_date, force_weekend=True)
        amount = normal_amount()
        vendor = random.choice(vendors[:36])  # non-blank vendor
    elif suspicious_type == "round":
        date = random_date(start_date, end_date)
        amount = round_number_amount()
        vendor = random.choice(vendors[:36])
    elif suspicious_type == "threshold":
        date = random_date(start_date, end_date)
        amount = threshold_amount()
        vendor = random.choice(vendors[:36])
        emp_id = f"EMP{random.randint(100, 999)}"
    elif suspicious_type == "duplicate":
        date = random_date(start_date, end_date)
        amount = 1247.50  # known duplicate amount from original dataset
        vendor = random.choice(vendors[:36])
    elif suspicious_type == "missing_vendor":
        date = random_date(start_date, end_date)
        amount = normal_amount()
        vendor = ""
    else:
        date = random_date(start_date, end_date)
        amount = benford_skewed_amount()
        vendor = random.choice(vendors[:36])

    return {
        "Transaction_ID": f"TXN{str(txn_id).zfill(5)}",
        "Date": date,
        "Amount": amount,
        "Vendor_Name": vendor,
        "Employee_ID": emp_id,
        "Account_Code": random.choice(account_codes),
        "Department": random.choice(departments),
        "Approval_Status": random.choice(approval_statuses)
    }

# --- Build dataset ---
rows = []

# Inject suspicious transactions (~8% of dataset = 800 rows)
suspicious_counts = {
    "weekend": 200,
    "round": 200,
    "threshold": 200,
    "duplicate": 100,
    "missing_vendor": 100
}

txn_id = 1

# Add suspicious rows
for s_type, count in suspicious_counts.items():
    for _ in range(count):
        rows.append(generate_row(txn_id, suspicious_type=s_type))
        txn_id += 1

# Fill remaining with normal transactions
while len(rows) < NUM_ROWS:
    rows.append(generate_row(txn_id))
    txn_id += 1

# Shuffle so suspicious rows aren't all grouped together
random.shuffle(rows)

# Re-assign Transaction_IDs after shuffle
for i, row in enumerate(rows):
    row["Transaction_ID"] = f"TXN{str(i + 1).zfill(5)}"

# --- Write to CSV ---
fieldnames = ["Transaction_ID", "Date", "Amount", "Vendor_Name", "Employee_ID", 
              "Account_Code", "Department", "Approval_Status"]

with open(OUTPUT_FILE, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ Generated {len(rows)} transactions → {OUTPUT_FILE}")
print(f"   Suspicious breakdown:")
for s_type, count in suspicious_counts.items():
    print(f"   • {s_type}: {count} rows")
