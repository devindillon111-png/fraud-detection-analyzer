import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# --- Load data ---
script_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(script_dir, "..", "data", "transactions.csv")
output_dir = os.path.join(script_dir, "..", "outputs")
os.makedirs(output_dir, exist_ok=True)

df = pd.read_csv(data_path)

# --- Extract leading digits from Amount column ---
def get_leading_digit(amount):
    return int(str(abs(amount)).lstrip("0").replace(".", "")[0])

df["Leading_Digit"] = df["Amount"].apply(get_leading_digit)

# --- Actual distribution ---
actual_counts = df["Leading_Digit"].value_counts().sort_index()
actual_pct = actual_counts / actual_counts.sum() * 100

# --- Benford's expected distribution ---
benford_pct = pd.Series(
    [np.log10(1 + 1/d) * 100 for d in range(1, 10)],
    index=range(1, 10)
)

# --- Print comparison table ---
print("\n=== Benford's Law Analysis ===")
print(f"{'Digit':<8} {'Expected %':<14} {'Actual %':<12} {'Deviation'}")
print("-" * 45)
for digit in range(1, 10):
    expected = benford_pct[digit]
    actual = actual_pct.get(digit, 0)
    deviation = actual - expected
    flag = " ⚠️  FLAGGED" if abs(deviation) > 5 else ""
    print(f"{digit:<8} {expected:<14.1f} {actual:<12.1f} {deviation:+.1f}%{flag}")

# --- Plot ---
fig, ax = plt.subplots(figsize=(10, 6))

x = np.arange(1, 10)
width = 0.35

bars1 = ax.bar(x - width/2, benford_pct, width, label="Benford's Expected", color="#2196F3", alpha=0.8)
bars2 = ax.bar(x + width/2, [actual_pct.get(d, 0) for d in range(1, 10)], width, label="Actual Distribution", color="#FF5722", alpha=0.8)

ax.set_xlabel("Leading Digit", fontsize=12)
ax.set_ylabel("Percentage (%)", fontsize=12)
ax.set_title("Benford's Law Analysis — Transaction Amounts\nFraud Detection Analyzer", fontsize=14)
ax.set_xticks(x)
ax.legend()
ax.grid(axis="y", alpha=0.3)

# Add value labels on bars
for bar in bars1:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
            f'{bar.get_height():.1f}%', ha='center', va='bottom', fontsize=8)
for bar in bars2:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
            f'{bar.get_height():.1f}%', ha='center', va='bottom', fontsize=8)

plt.tight_layout()
output_path = os.path.join(output_dir, "benford_analysis.png")
plt.savefig(output_path, dpi=150)
print(f"\n✅ Chart saved → {output_path}")
plt.show()