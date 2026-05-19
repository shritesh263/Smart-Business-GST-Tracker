<div align="center">
  <h1>💼 Smart Business & GST Tracker</h1>
  <p>
    <em>A powerful, all-in-one digital ledger and compliance assistant for modern SMEs and freelancers.</em>
  </p>
  
  [![Python](https://img.shields.io/badge/Python-3.8+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](#)
  [![Flask](https://img.shields.io/badge/Flask-2.0+-black.svg?style=for-the-badge&logo=flask&logoColor=white)](#)
  [![SQLite](https://img.shields.io/badge/SQLite-Database-003B57.svg?style=for-the-badge&logo=sqlite&logoColor=white)](#)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](#)
  
  <br />
  <strong><a href="https://smart-business-gst-tracker.vercel.app" target="_blank">🚀 View Live Demo</a></strong>
</div>

<hr>

## 📖 About the Project

**Smart Business & GST Tracker** is a comprehensive, full-stack web application built to streamline day-to-day operations for small-to-medium enterprises (SMEs). From managing pending customer payments to staying on top of GST compliance, this platform replaces outdated paper ledgers with a modern, automated system.

> **Mission:** To make business management and tax compliance effortless, accessible, and error-free for non-accountants.

---

## 🌍 The Real-World Need

In today's fast-paced business environment, business owners face several critical challenges:
- ❌ **Complex Software:** Traditional accounting software is often expensive and requires formal accounting knowledge.
- ❌ **Missed Deadlines:** Failing to file GST on time results in heavy penalties and compound interest.
- ❌ **Lost Revenue:** Tracking *udhari* (pending payments) manually on paper often leads to forgotten debts and cash flow issues.
- ❌ **Stockouts:** Without proper inventory tracking, businesses run out of crucial items unexpectedly.

**The Solution:** An intuitive, centralized system that empowers business owners to take control of their finances and compliance with zero friction.

---

## ✨ Key Features & Benefits

| Feature | Description |
| :--- | :--- |
| 📊 **Real-time Dashboard** | Get instant insights into monthly sales, expenses, net profit, and outstanding debts. |
| ⏱️ **GST Compliance & Penalties** | Track upcoming GSTR-1 and GSTR-3B deadlines. Automatically calculate late fees if missed. |
| 🧾 **Instant PDF Invoicing** | Generate professional, GST-compliant invoices with HSN codes and email them instantly to clients. |
| 📦 **Smart Inventory Management** | Track stock movements and receive low-stock alerts before you run out of essential items. |
| 👥 **Customer & Debt Tracking** | Keep comprehensive records of all customer transactions and set automated payment reminders. |
| 📒 **Digital Cashbook** | Categorize daily cash-in and cash-out to maintain a crystal-clear financial ledger. |

---

## 🗂️ Project Structure

The architecture is deliberately kept **flat and simple** to ensure ease of understanding and modification for developers of all skill levels:

```text
📁 Project Root
├── app.py               # Core application, API routes, and DB models
├── email_helper.py      # Dedicated module for handling email delivery
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables configuration
├── 📁 templates/        # HTML views for the frontend application
├── 📁 static/           # CSS, JavaScript, and static assets
└── 📁 instance/         # Secure storage for the local SQLite database
```

---

## 🚀 Getting Started Locally

Ready to run the project on your machine? Follow these simple steps:

### 1. Clone the Repository
```bash
git clone https://github.com/shritesh263/Smart-Business-GST-Tracker.git
cd Smart-Business-GST-Tracker
```

### 2. Set Up a Virtual Environment (Recommended)
```bash
# Create the environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Mac/Linux)
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
Create a `.env` file in the root directory (if not already present) and add your necessary environment variables (e.g., SMTP details for emails).

### 5. Launch the Application
```bash
python app.py
```

🎉 **Access the Local App:** Open your web browser and navigate to [http://127.0.0.1:5000](http://127.0.0.1:5000)

🌐 **Access the Live Deployed App:** [https://smart-business-gst-tracker.vercel.app](https://smart-business-gst-tracker.vercel.app)
