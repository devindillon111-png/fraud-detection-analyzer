# 🔍 Fraud Detection Analyzer

A Python-based internal audit tool that detects anomalous financial transactions using machine learning and rule-based flagging techniques.

## 📊 Project Overview

This project simulates a real-world fraud detection system used in internal audit and IT audit environments. It analyzes 10,000 financial transactions to identify suspicious activity using multiple detection methods.

## 🛠️ Technologies Used

- **Python** — Core programming language
- **pandas & NumPy** — Data manipulation and analysis
- **scikit-learn** — Machine learning (Isolation Forest algorithm)
- **matplotlib** — Data visualization
- **Streamlit** — Interactive web dashboard

## 🔎 Detection Methods

- **Benford's Law Analysis** — Identifies unnatural first-digit distributions in transaction amounts
- **Rule-Based Flagging** — Flags weekend transactions, round numbers, threshold manipulation, missing vendors, and duplicate amounts
- **Isolation Forest ML Model** — Unsupervised machine learning algorithm that detects statistical anomalies

## 📁 Project Structure
