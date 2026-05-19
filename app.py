import os
import re
import uuid
import io
from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from datetime import datetime, date, timedelta
import pdfkit
from sqlalchemy import extract, func

# ============================================================
# App & DB Setup
# ============================================================
load_dotenv()

app = Flask(__name__)
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///gst_tracker.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# ============================================================
# ORM Models — Existing
# ============================================================

class User(db.Model):
    __tablename__ = "users"
    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.String(50), unique=True, nullable=False)
    name          = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password      = db.Column(db.String(200), nullable=False)
    business_name = db.Column(db.String(150))
    business_type = db.Column(db.String(50))
    turnover      = db.Column(db.Float, default=0.0)
    gst_number    = db.Column(db.String(20))
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)


class Sale(db.Model):
    __tablename__ = "sales"
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.String(50), nullable=False)
    product     = db.Column(db.String(150), nullable=False)
    hsn_code    = db.Column(db.String(20))
    amount      = db.Column(db.Float, nullable=False)
    gst_rate    = db.Column(db.Float, nullable=False)
    gst_amount  = db.Column(db.Float, nullable=False)
    total       = db.Column(db.Float, nullable=False)
    sale_date   = db.Column(db.Date, nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)


class Invoice(db.Model):
    __tablename__ = "invoices"
    id             = db.Column(db.Integer, primary_key=True)
    invoice_id     = db.Column(db.String(50), unique=True, nullable=False)
    user_id        = db.Column(db.String(50))
    invoice_no     = db.Column(db.String(30))
    buyer_name     = db.Column(db.String(150))
    buyer_email    = db.Column(db.String(120))
    buyer_gst      = db.Column(db.String(20))
    buyer_address  = db.Column(db.String(300))
    seller_name    = db.Column(db.String(150))
    seller_address = db.Column(db.String(300))
    seller_gstin   = db.Column(db.String(20))
    subtotal       = db.Column(db.Float)
    total_gst      = db.Column(db.Float)
    grand_total    = db.Column(db.Float)
    total_amount   = db.Column(db.String(30))
    html_content   = db.Column(db.Text)
    invoice_date   = db.Column(db.Date, default=date.today)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)


class InvoiceItem(db.Model):
    __tablename__ = "invoice_items"
    id             = db.Column(db.Integer, primary_key=True)
    invoice_id     = db.Column(db.Integer, db.ForeignKey("invoices.id"))
    product_name   = db.Column(db.String(150))
    hsn_code       = db.Column(db.String(20))
    quantity       = db.Column(db.Float)
    rate           = db.Column(db.Float)
    taxable_amount = db.Column(db.Float)
    gst_rate       = db.Column(db.Float)
    gst_amount     = db.Column(db.Float)
    total_amount   = db.Column(db.Float)
    invoice        = db.relationship("Invoice", backref="items")


class HsnProduct(db.Model):
    __tablename__ = "hsn_products"
    id           = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(150), nullable=False)
    hsn_code     = db.Column(db.String(20), nullable=False)
    gst_rate     = db.Column(db.Float, nullable=False)
    is_exempt    = db.Column(db.Boolean, default=False)


class Deadline(db.Model):
    __tablename__ = "deadlines"
    id           = db.Column(db.Integer, primary_key=True)
    return_name  = db.Column(db.String(50), nullable=False)
    description  = db.Column(db.String(200))
    due_day      = db.Column(db.Integer)
    frequency    = db.Column(db.String(20))
    applies_to   = db.Column(db.String(100))


class PenaltyLog(db.Model):
    __tablename__ = "penalty_logs"
    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.String(50))
    return_type   = db.Column(db.String(50))
    due_date      = db.Column(db.Date)
    filed_date    = db.Column(db.Date)
    days_late     = db.Column(db.Integer)
    late_fee      = db.Column(db.Float)
    interest      = db.Column(db.Float)
    total_penalty = db.Column(db.Float)
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)


# ============================================================
# ORM Models — New Features
# ============================================================

class Expense(db.Model):
    __tablename__ = "expenses"
    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.String(50), nullable=False)
    category     = db.Column(db.String(50), nullable=False)
    description  = db.Column(db.String(200))
    amount       = db.Column(db.Float, nullable=False)
    expense_date = db.Column(db.Date, nullable=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)


class Customer(db.Model):
    __tablename__ = "customers"
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.String(50), nullable=False)
    name       = db.Column(db.String(150), nullable=False)
    phone      = db.Column(db.String(20))
    email      = db.Column(db.String(120))
    address    = db.Column(db.String(300))
    gst_number = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    transactions = db.relationship("CustomerTransaction", backref="customer", lazy=True)


class CustomerTransaction(db.Model):
    __tablename__ = "customer_transactions"
    id          = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    user_id     = db.Column(db.String(50), nullable=False)
    txn_type    = db.Column(db.String(20), nullable=False)   # 'sale' | 'payment_received'
    amount      = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    txn_date    = db.Column(db.Date, nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)


class StockItem(db.Model):
    __tablename__ = "stock_items"
    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.String(50), nullable=False)
    product_name     = db.Column(db.String(150), nullable=False)
    hsn_code         = db.Column(db.String(20))
    unit             = db.Column(db.String(20), default="piece")
    current_quantity = db.Column(db.Float, default=0.0)
    minimum_quantity = db.Column(db.Float, default=0.0)
    purchase_price   = db.Column(db.Float, default=0.0)
    selling_price    = db.Column(db.Float, default=0.0)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)
    movements        = db.relationship("StockMovement", backref="stock_item", lazy=True)


class StockMovement(db.Model):
    __tablename__ = "stock_movements"
    id            = db.Column(db.Integer, primary_key=True)
    stock_item_id = db.Column(db.Integer, db.ForeignKey("stock_items.id"), nullable=False)
    user_id       = db.Column(db.String(50), nullable=False)
    movement_type = db.Column(db.String(20), nullable=False)  # 'stock_in' | 'stock_out'
    quantity      = db.Column(db.Float, nullable=False)
    note          = db.Column(db.String(200))
    movement_date = db.Column(db.Date, nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)


class CashBook(db.Model):
    __tablename__ = "cashbook"
    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.String(50), nullable=False)
    entry_type   = db.Column(db.String(20), nullable=False)  # 'cash_in' | 'cash_out'
    amount       = db.Column(db.Float, nullable=False)
    description  = db.Column(db.String(200))
    payment_mode = db.Column(db.String(20), default="cash")  # cash|upi|card|cheque
    entry_date   = db.Column(db.Date, nullable=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)


class PaymentReminder(db.Model):
    __tablename__ = "payment_reminders"
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.String(50), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=True)
    amount_due  = db.Column(db.Float, nullable=False)
    due_date    = db.Column(db.Date, nullable=False)
    status      = db.Column(db.String(20), default="pending")  # pending|paid|overdue
    note        = db.Column(db.String(300))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    customer    = db.relationship("Customer", backref="reminders")


# ============================================================
# Seed Data
# ============================================================

def seed_data():
    if Deadline.query.count() == 0:
        db.session.add_all([
            Deadline(return_name="GSTR-1",  description="Outward supplies return",
                     due_day=11, frequency="Monthly",  applies_to="Regular taxpayers"),
            Deadline(return_name="GSTR-3B", description="Summary return and tax payment",
                     due_day=20, frequency="Monthly",  applies_to="Regular taxpayers"),
            Deadline(return_name="GSTR-9",  description="Annual return",
                     due_day=31, frequency="Annually (Dec)", applies_to="All taxpayers"),
            Deadline(return_name="CMP-08",  description="Composition dealer payment",
                     due_day=18, frequency="Quarterly", applies_to="Composition dealers"),
        ])
        db.session.commit()

    if HsnProduct.query.count() == 0:
        products = [
            ("Rice", "1006", 0, True), ("Wheat", "1001", 0, True),
            ("Sugar", "1701", 5, False), ("Milk", "0401", 0, True),
            ("Butter", "0405", 12, False), ("Cotton Shirt", "6205", 12, False),
            ("Mobile Phone", "8517", 18, False), ("Laptop", "8471", 18, False),
            ("Biscuits", "1905", 18, False), ("Toothpaste", "3306", 18, False),
            ("Soap", "3401", 18, False), ("Shampoo", "3305", 18, False),
            ("Cement", "2523", 28, False), ("Paint", "3208", 28, False),
            ("Tea", "0902", 5, False), ("Coffee", "0901", 5, False),
            ("Medicines", "3004", 12, False), ("Pen", "9608", 18, False),
            ("Notebook", "4820", 12, False), ("Shoes", "6403", 18, False),
            ("Books", "4901", 0, True), ("Furniture", "9403", 18, False),
            ("Refrigerator", "8418", 18, False), ("Air Conditioner", "8415", 28, False),
            ("Spectacles", "9004", 12, False), ("Spices", "0910", 5, False),
            ("Motorcycle", "8711", 28, False), ("LED Bulb", "8539", 12, False),
            ("Hardware/Tools", "8205", 18, False), ("Restaurant Bill", "9963", 5, False),
        ]
        db.session.add_all([
            HsnProduct(product_name=p, hsn_code=h, gst_rate=r, is_exempt=e)
            for p, h, r, e in products
        ])
        db.session.commit()


# ============================================================
# UI Page Routes
# ============================================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard_page():
    return render_template('dashboard.html')

@app.route('/sales')
def sales_page():
    return render_template('sales.html')

@app.route('/checker')
def checker_page():
    return render_template('checker.html')

@app.route('/invoice')
def invoice_page():
    return render_template('invoice.html')

@app.route('/summary')
def summary_page_route():
    return render_template('summary.html')

# New feature pages
@app.route('/expenses')
def expenses_page():
    return render_template('expenses.html')

@app.route('/customers')
def customers_page():
    return render_template('customers.html')

@app.route('/inventory')
def inventory_page():
    return render_template('inventory.html')

@app.route('/profit-loss')
def profit_loss_page():
    return render_template('profit_loss.html')

@app.route('/cashbook')
def cashbook_page():
    return render_template('cashbook.html')

@app.route('/reminders')
def reminders_page():
    return render_template('reminders.html')


# ============================================================
# REST API — Auth
# ============================================================

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json or {}
    required_fields = ['name', 'email', 'password', 'business_name', 'business_type', 'turnover']
    if not all(k in data for k in required_fields):
        return jsonify({"success": False, "message": "Missing fields"}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"success": False, "message": "Email already registered"}), 400
    new_uid = str(uuid.uuid4())
    user = User(user_id=new_uid, name=data['name'], email=data['email'],
                password=data['password'], business_name=data['business_name'],
                business_type=data['business_type'], turnover=float(data['turnover']))
    try:
        db.session.add(user)
        db.session.commit()
        return jsonify({"success": True, "message": "Registered successfully. Please login.",
                        "user_id": new_uid}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/login', methods=['POST'])
def login():
    data = request.json or {}
    user = User.query.filter_by(email=data.get('email'), password=data.get('password')).first()
    if user:
        return jsonify({"success": True, "user_id": user.user_id,
                        "name": user.name, "business_name": user.business_name or ''}), 200
    return jsonify({"success": False, "message": "Invalid email or password"}), 401


# ============================================================
# REST API — Enhanced Dashboard
# ============================================================

@app.route('/api/dashboard/<user_id>', methods=['GET'])
def get_dashboard_data(user_id):
    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    today = datetime.now()

    # GST Deadline (GSTR-3B → 20th)
    deadline_day = 20
    next_deadline = today.replace(day=deadline_day, hour=0, minute=0, second=0, microsecond=0)
    if today.day > deadline_day:
        if today.month == 12:
            next_deadline = next_deadline.replace(year=today.year + 1, month=1)
        else:
            next_deadline = next_deadline.replace(month=today.month + 1)
    days_remaining = (next_deadline - today).days

    # This month sales
    sales_this_month = Sale.query.filter(
        Sale.user_id == user_id,
        extract('month', Sale.sale_date) == today.month,
        extract('year', Sale.sale_date) == today.year
    ).all()
    total_sales = sum(s.amount for s in sales_this_month)
    total_gst   = sum(s.gst_amount for s in sales_this_month)

    # This month expenses
    expenses_this_month = Expense.query.filter(
        Expense.user_id == user_id,
        extract('month', Expense.expense_date) == today.month,
        extract('year', Expense.expense_date) == today.year
    ).all()
    total_expenses = sum(e.amount for e in expenses_this_month)

    # Net profit
    net_profit = total_sales - total_expenses - total_gst

    # Today's cashbook closing balance
    today_date = today.date()
    cash_in_today  = db.session.query(func.sum(CashBook.amount)).filter(
        CashBook.user_id == user_id,
        CashBook.entry_type == 'cash_in',
        CashBook.entry_date == today_date
    ).scalar() or 0
    cash_out_today = db.session.query(func.sum(CashBook.amount)).filter(
        CashBook.user_id == user_id,
        CashBook.entry_type == 'cash_out',
        CashBook.entry_date == today_date
    ).scalar() or 0
    closing_balance = cash_in_today - cash_out_today

    # Outstanding udhari (sum of all sale txns - payment_received txns across customers)
    customers = Customer.query.filter_by(user_id=user_id).all()
    total_outstanding = 0
    top_debtors = []
    for c in customers:
        sales_amt    = sum(t.amount for t in c.transactions if t.txn_type == 'sale')
        payments_amt = sum(t.amount for t in c.transactions if t.txn_type == 'payment_received')
        balance = sales_amt - payments_amt
        if balance > 0:
            total_outstanding += balance
            top_debtors.append({"name": c.name, "phone": c.phone or '', "balance": balance})
    top_debtors.sort(key=lambda x: x['balance'], reverse=True)
    top_debtors = top_debtors[:3]

    # Stock alerts
    stock_items = StockItem.query.filter_by(user_id=user_id).all()
    low_stock_count     = sum(1 for s in stock_items if 0 < s.current_quantity <= s.minimum_quantity)
    out_of_stock_count  = sum(1 for s in stock_items if s.current_quantity <= 0)
    low_stock_items = [
        {"name": s.product_name, "qty": s.current_quantity, "unit": s.unit, "min": s.minimum_quantity}
        for s in stock_items if s.current_quantity <= s.minimum_quantity
    ]

    # Payment reminders — auto-update overdue
    all_reminders = PaymentReminder.query.filter(
        PaymentReminder.user_id == user_id,
        PaymentReminder.status != 'paid'
    ).all()
    for r in all_reminders:
        if r.due_date < today_date and r.status == 'pending':
            r.status = 'overdue'
    db.session.commit()

    overdue_count   = sum(1 for r in all_reminders if r.status == 'overdue')
    due_today_count = sum(1 for r in all_reminders if r.due_date == today_date and r.status == 'pending')

    # Recent 5 sales
    recent_sales = Sale.query.filter_by(user_id=user_id).order_by(Sale.sale_date.desc()).limit(5).all()
    recent_list = [{"product": s.product, "amount": s.amount,
                    "gst_amount": s.gst_amount, "gst_rate": s.gst_rate,
                    "date": s.sale_date.isoformat()} for s in recent_sales]

    return jsonify({
        "success": True,
        "name": user.name,
        "business_name": user.business_name or '',
        "total_sales_month":    total_sales,
        "gst_collected":        total_gst,
        "gst_payable":          total_gst,
        "total_expenses_month": total_expenses,
        "net_profit_month":     net_profit,
        "today_closing_balance": closing_balance,
        "total_outstanding":    total_outstanding,
        "low_stock_count":      low_stock_count,
        "out_of_stock_count":   out_of_stock_count,
        "overdue_reminders_count": overdue_count,
        "due_today_count":      due_today_count,
        "next_deadline_days":   days_remaining,
        "next_deadline_date":   next_deadline.strftime("%d %b %Y"),
        "recent_sales":         recent_list,
        "top_debtors":          top_debtors,
        "low_stock_items":      low_stock_items,
    }), 200


# ============================================================
# REST API — Sales
# ============================================================

@app.route('/api/add-sale', methods=['POST'])
def add_sale():
    data = request.json or {}
    required_fields = ['user_id', 'date', 'product', 'amount', 'gst_rate']
    if not all(k in data for k in required_fields):
        return jsonify({"success": False, "message": "Missing fields"}), 400
    amount     = float(data['amount'])
    gst_rate   = float(data['gst_rate'])
    gst_amount = (amount * gst_rate) / 100
    total      = amount + gst_amount
    try:
        sale_date = date.fromisoformat(data['date'])
    except ValueError:
        return jsonify({"success": False, "message": "Invalid date format. Use YYYY-MM-DD"}), 400

    sale = Sale(user_id=data['user_id'], product=data['product'],
                hsn_code=data.get('hsn_code', ''), amount=amount,
                gst_rate=gst_rate, gst_amount=gst_amount, total=total, sale_date=sale_date)
    try:
        db.session.add(sale)
        db.session.commit()
        return jsonify({"success": True,
                        "message": f"Sale added! GST collected: \u20b9{gst_amount:.2f}",
                        "gst_collected": gst_amount}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/sales', methods=['GET'])
def get_sales():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "User ID required"}), 400
    sales = Sale.query.filter_by(user_id=user_id).order_by(Sale.sale_date.desc()).all()
    return jsonify({"success": True, "sales": [
        {"id": s.id, "product": s.product, "hsn_code": s.hsn_code,
         "amount": s.amount, "gst_rate": s.gst_rate, "gst_amount": s.gst_amount,
         "total": s.total, "date": s.sale_date.isoformat()} for s in sales
    ]}), 200


# ============================================================
# REST API — Summary / Chart
# ============================================================

@app.route('/api/summary', methods=['GET'])
def get_summary():
    user_id = request.args.get('user_id')
    month   = request.args.get('month')
    if not user_id:
        return jsonify({"success": False, "message": "User ID required"}), 400
    base_q = Sale.query.filter_by(user_id=user_id)
    if month:
        try:
            y, m = month.split('-')
            base_q = base_q.filter(
                extract('year',  Sale.sale_date) == int(y),
                extract('month', Sale.sale_date) == int(m)
            )
        except ValueError:
            return jsonify({"success": False, "message": "Invalid month format"}), 400
    sales = base_q.all()
    today = datetime.now()
    chart_data = []
    for i in range(5, -1, -1):
        cm = today.month - i
        cy = today.year
        if cm <= 0: cm += 12; cy -= 1
        m_sales = Sale.query.filter(Sale.user_id == user_id,
            extract('year', Sale.sale_date) == cy,
            extract('month', Sale.sale_date) == cm).all()
        chart_data.append({"month": datetime(cy, cm, 1).strftime('%b %Y'),
                            "sales": sum(s.amount for s in m_sales),
                            "gst":   sum(s.gst_amount for s in m_sales)})
    return jsonify({"success": True,
        "total_sales": sum(s.amount for s in sales),
        "total_gst_collected": sum(s.gst_amount for s in sales),
        "net_gst_payable": sum(s.gst_amount for s in sales),
        "sales_count": len(sales), "chart_data": chart_data}), 200


# ============================================================
# REST API — Eligibility & HSN Search
# ============================================================

@app.route('/api/check-eligibility', methods=['GET'])
def check_eligibility():
    turnover      = float(request.args.get('turnover', 0))
    business_type = request.args.get('business_type', 'goods').lower()
    threshold            = 4000000 if business_type == 'goods' else 2000000
    needs_registration   = turnover > threshold
    composition_eligible = turnover <= 15000000
    return jsonify({"success": True, "turnover": turnover, "threshold": threshold,
        "needs_registration": needs_registration,
        "composition_eligible": composition_eligible,
        "message": "Registration Required" if needs_registration else "Registration Not Required",
        "docs_needed": ["PAN Card of the Business or Applicant", "Aadhar Card",
            "Proof of Business Registration",
            "Identity and Address Proof of Promoters/Director",
            "Bank Account Statement/Canceled Cheque"]}), 200


@app.route('/api/hsn-search', methods=['GET'])
def hsn_search():
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify({"success": True, "results": []}), 200
    results = HsnProduct.query.filter(HsnProduct.product_name.ilike(f"%{query}%")).all()
    return jsonify({"success": True, "results": [
        {"product_name": p.product_name, "hsn_code": p.hsn_code,
         "gst_rate": p.gst_rate, "is_exempt": p.is_exempt} for p in results
    ]}), 200


# ============================================================
# REST API — Penalty (kept as API, no separate page)
# ============================================================

@app.route('/api/penalty', methods=['POST'])
def calculate_penalty():
    data      = request.json or {}
    days_late = int(data.get('days_late', 0))
    tax_due   = float(data.get('tax_due', 0))
    daily_penalty = days_late * 50
    interest      = (tax_due * 0.18 * days_late) / 365
    total_penalty = daily_penalty + interest
    user_id = data.get('user_id')
    if user_id and days_late > 0:
        try:
            db.session.add(PenaltyLog(user_id=user_id,
                return_type=data.get('return_type', 'Unknown'),
                days_late=days_late, late_fee=round(daily_penalty, 2),
                interest=round(interest, 2), total_penalty=round(total_penalty, 2)))
            db.session.commit()
        except Exception:
            db.session.rollback()
    return jsonify({"success": True, "days_late": days_late,
        "daily_penalty_component": daily_penalty,
        "interest_component": round(interest, 2),
        "total_penalty": round(total_penalty, 2)}), 200


# ============================================================
# REST API — Invoice
# ============================================================

@app.route('/api/generate-invoice', methods=['POST'])
def generate_invoice():
    return jsonify({"success": True, "message": "Invoice generated successfully",
                    "invoice_data": request.json or {}}), 200


@app.route('/api/invoice/save', methods=['POST'])
def save_invoice():
    data = request.json or {}
    new_invoice_id = str(uuid.uuid4())
    invoice = Invoice(invoice_id=new_invoice_id, user_id=data.get('user_id', 'guest'),
        invoice_no=data.get('invoice_no', ''), buyer_name=data.get('buyer_name', ''),
        buyer_email=data.get('buyer_email', ''), buyer_gst=data.get('buyer_gstin', ''),
        buyer_address=data.get('buyer_address', ''), seller_name=data.get('seller_name', ''),
        seller_address=data.get('seller_address', ''), seller_gstin=data.get('seller_gstin', ''),
        total_amount=data.get('total_amount', '0'), html_content=data.get('html_content', ''))
    try:
        db.session.add(invoice)
        db.session.flush()
        for it in data.get('items', []):
            db.session.add(InvoiceItem(invoice_id=invoice.id,
                product_name=it.get('name', ''), hsn_code=it.get('hsn', ''),
                quantity=float(it.get('qty', 1)), rate=float(it.get('rate', 0)),
                taxable_amount=float(it.get('taxableAmount', 0)),
                gst_rate=float(it.get('gstRate', 0)), gst_amount=float(it.get('gstAmount', 0)),
                total_amount=float(it.get('totalAmount', 0))))
        db.session.commit()
        return jsonify({"success": True, "invoice_id": new_invoice_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


def generate_invoice_pdf(invoice_obj):
    html_content = invoice_obj.html_content or '<h1>Invoice</h1>'
    path_wk = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    opts = {'enable-local-file-access': None, 'encoding': 'UTF-8', 'quiet': ''}
    try:
        if os.path.exists(path_wk):
            return pdfkit.from_string(html_content, False, options=opts,
                                      configuration=pdfkit.configuration(wkhtmltopdf=path_wk))
        return pdfkit.from_string(html_content, False, options=opts)
    except Exception:
        return html_content.encode('utf-8')


@app.route('/invoice/download/<invoice_id>', methods=['GET'])
def download_invoice(invoice_id):
    invoice = Invoice.query.filter_by(invoice_id=invoice_id).first()
    if not invoice:
        return "Invoice not found", 404
    try:
        pdf = generate_invoice_pdf(invoice)
        fname = f"Invoice_{invoice.invoice_no or invoice_id}_{invoice.buyer_name or 'Buyer'}.pdf"
        return send_file(io.BytesIO(pdf), download_name=fname.replace(" ", "_"),
                         as_attachment=True, mimetype='application/pdf')
    except Exception as e:
        return f"Error generating PDF: {str(e)}", 500


@app.route('/api/invoice/send-email', methods=['POST'])
def send_invoice_email_route():
    from email_helper import send_invoice_email
    data           = request.json or {}
    receiver_email = data.get('receiver_email', '').strip()
    invoice_id     = data.get('invoice_id', '').strip()
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    if not receiver_email:
        return jsonify({"success": False, "message": "Please enter receiver email"}), 400
    if not re.match(pattern, receiver_email):
        return jsonify({"success": False, "message": "Please enter a valid email address"}), 400
    if not invoice_id:
        return jsonify({"success": False, "message": "invoice_id is required"}), 400
    invoice = Invoice.query.filter_by(invoice_id=invoice_id).first()
    if not invoice:
        return jsonify({"success": False, "message": "Invoice not found."}), 404
    result = send_invoice_email(receiver_email=receiver_email,
        buyer_name=invoice.buyer_name or 'Buyer', seller_name=invoice.seller_name or 'Seller',
        invoice_number=invoice.invoice_no or invoice_id,
        total_amount=invoice.total_amount or '0', pdf_bytes=generate_invoice_pdf(invoice))
    return jsonify(result), 200 if result['success'] else 500


# ============================================================
# REST API — Expenses
# ============================================================

@app.route('/api/expenses', methods=['GET'])
def get_expenses():
    user_id  = request.args.get('user_id')
    month    = request.args.get('month')
    category = request.args.get('category', '')
    if not user_id:
        return jsonify({"success": False, "message": "user_id required"}), 400
    q = Expense.query.filter_by(user_id=user_id)
    if month:
        try:
            y, m = month.split('-')
            q = q.filter(extract('year', Expense.expense_date) == int(y),
                         extract('month', Expense.expense_date) == int(m))
        except ValueError:
            pass
    if category:
        q = q.filter_by(category=category)
    expenses = q.order_by(Expense.expense_date.desc()).all()
    total = sum(e.amount for e in expenses)
    return jsonify({"success": True, "total": total, "expenses": [
        {"id": e.id, "category": e.category, "description": e.description,
         "amount": e.amount, "date": e.expense_date.isoformat()} for e in expenses
    ]}), 200


@app.route('/api/expenses/add', methods=['POST'])
def add_expense():
    data = request.json or {}
    required = ['user_id', 'category', 'amount', 'date']
    if not all(k in data for k in required):
        return jsonify({"success": False, "message": "Missing required fields"}), 400
    try:
        exp = Expense(user_id=data['user_id'], category=data['category'],
                      description=data.get('description', ''),
                      amount=float(data['amount']),
                      expense_date=date.fromisoformat(data['date']))
        db.session.add(exp)
        db.session.commit()
        return jsonify({"success": True, "message": "Expense added successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


# ============================================================
# REST API — Customers
# ============================================================

@app.route('/api/customers', methods=['GET'])
def get_customers():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "user_id required"}), 400
    customers = Customer.query.filter_by(user_id=user_id).order_by(Customer.name).all()
    result = []
    for c in customers:
        sales_amt    = sum(t.amount for t in c.transactions if t.txn_type == 'sale')
        payments_amt = sum(t.amount for t in c.transactions if t.txn_type == 'payment_received')
        balance = sales_amt - payments_amt
        result.append({"id": c.id, "name": c.name, "phone": c.phone or '',
                        "email": c.email or '', "address": c.address or '',
                        "balance": round(balance, 2)})
    total_outstanding = sum(r['balance'] for r in result if r['balance'] > 0)
    return jsonify({"success": True, "customers": result,
                    "total_outstanding": round(total_outstanding, 2)}), 200


@app.route('/api/customers/add', methods=['POST'])
def add_customer():
    data = request.json or {}
    if not data.get('user_id') or not data.get('name'):
        return jsonify({"success": False, "message": "user_id and name required"}), 400
    try:
        c = Customer(user_id=data['user_id'], name=data['name'],
                     phone=data.get('phone', ''), email=data.get('email', ''),
                     address=data.get('address', ''), gst_number=data.get('gst_number', ''))
        db.session.add(c)
        db.session.commit()
        return jsonify({"success": True, "message": "Customer added", "id": c.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/customers/<int:cid>', methods=['GET'])
def get_customer_detail(cid):
    c = Customer.query.get_or_404(cid)
    txns = CustomerTransaction.query.filter_by(customer_id=cid).order_by(
        CustomerTransaction.txn_date.desc()).all()
    sales_total    = sum(t.amount for t in txns if t.txn_type == 'sale')
    payments_total = sum(t.amount for t in txns if t.txn_type == 'payment_received')
    balance = sales_total - payments_total
    return jsonify({"success": True,
        "customer": {"id": c.id, "name": c.name, "phone": c.phone or '',
                     "email": c.email or '', "address": c.address or '', "balance": round(balance, 2)},
        "transactions": [{"id": t.id, "type": t.txn_type, "amount": t.amount,
                           "description": t.description or '', "date": t.txn_date.isoformat()}
                          for t in txns]}), 200


@app.route('/api/customers/transaction', methods=['POST'])
def add_customer_transaction():
    data = request.json or {}
    required = ['user_id', 'customer_id', 'type', 'amount', 'date']
    if not all(k in data for k in required):
        return jsonify({"success": False, "message": "Missing fields"}), 400
    if data['type'] not in ('sale', 'payment_received'):
        return jsonify({"success": False, "message": "type must be 'sale' or 'payment_received'"}), 400
    try:
        txn = CustomerTransaction(
            customer_id=int(data['customer_id']), user_id=data['user_id'],
            txn_type=data['type'], amount=float(data['amount']),
            description=data.get('description', ''),
            txn_date=date.fromisoformat(data['date']))
        db.session.add(txn)
        db.session.commit()
        return jsonify({"success": True, "message": "Transaction recorded"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


# ============================================================
# REST API — Inventory
# ============================================================

@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "user_id required"}), 400
    items = StockItem.query.filter_by(user_id=user_id).order_by(StockItem.product_name).all()
    return jsonify({"success": True, "items": [
        {"id": i.id, "product_name": i.product_name, "hsn_code": i.hsn_code or '',
         "unit": i.unit, "current_quantity": i.current_quantity,
         "minimum_quantity": i.minimum_quantity, "purchase_price": i.purchase_price,
         "selling_price": i.selling_price} for i in items
    ]}), 200


@app.route('/api/inventory/add', methods=['POST'])
def add_stock_item():
    data = request.json or {}
    if not data.get('user_id') or not data.get('product_name'):
        return jsonify({"success": False, "message": "user_id and product_name required"}), 400
    try:
        item = StockItem(
            user_id=data['user_id'], product_name=data['product_name'],
            hsn_code=data.get('hsn_code', ''), unit=data.get('unit', 'piece'),
            current_quantity=float(data.get('current_quantity', 0)),
            minimum_quantity=float(data.get('minimum_quantity', 0)),
            purchase_price=float(data.get('purchase_price', 0)),
            selling_price=float(data.get('selling_price', 0)))
        db.session.add(item)
        db.session.commit()
        return jsonify({"success": True, "message": "Stock item added", "id": item.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/inventory/stock-in', methods=['POST'])
def stock_in():
    data = request.json or {}
    item_id  = data.get('item_id')
    qty      = float(data.get('quantity', 0))
    user_id  = data.get('user_id')
    if not item_id or qty <= 0:
        return jsonify({"success": False, "message": "item_id and positive quantity required"}), 400
    item = StockItem.query.get(item_id)
    if not item:
        return jsonify({"success": False, "message": "Stock item not found"}), 404
    try:
        item.current_quantity += qty
        mv = StockMovement(stock_item_id=item.id, user_id=user_id or item.user_id,
                           movement_type='stock_in', quantity=qty,
                           note=data.get('note', ''),
                           movement_date=date.fromisoformat(data.get('date', date.today().isoformat())))
        db.session.add(mv)
        db.session.commit()
        return jsonify({"success": True, "message": f"Stock updated. New qty: {item.current_quantity}"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/inventory/low-stock', methods=['GET'])
def get_low_stock():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "user_id required"}), 400
    items = StockItem.query.filter(
        StockItem.user_id == user_id,
        StockItem.current_quantity <= StockItem.minimum_quantity
    ).all()
    return jsonify({"success": True, "items": [
        {"id": i.id, "product_name": i.product_name, "current_quantity": i.current_quantity,
         "minimum_quantity": i.minimum_quantity, "unit": i.unit} for i in items
    ]}), 200


# ============================================================
# REST API — Profit & Loss
# ============================================================

@app.route('/api/profit-loss', methods=['GET'])
def get_profit_loss():
    user_id = request.args.get('user_id')
    month   = request.args.get('month')  # YYYY-MM
    if not user_id or not month:
        return jsonify({"success": False, "message": "user_id and month required"}), 400
    try:
        y, m = int(month.split('-')[0]), int(month.split('-')[1])
    except (ValueError, IndexError):
        return jsonify({"success": False, "message": "Invalid month"}), 400

    sales = Sale.query.filter(Sale.user_id == user_id,
        extract('year', Sale.sale_date) == y,
        extract('month', Sale.sale_date) == m).all()
    total_sales = sum(s.amount for s in sales)
    total_gst   = sum(s.gst_amount for s in sales)

    expenses = Expense.query.filter(Expense.user_id == user_id,
        extract('year', Expense.expense_date) == y,
        extract('month', Expense.expense_date) == m).all()
    total_expenses = sum(e.amount for e in expenses)

    # Expenses by category
    categories = {}
    for e in expenses:
        categories[e.category] = categories.get(e.category, 0) + e.amount

    gross_profit = total_sales - total_expenses
    net_profit   = gross_profit - total_gst

    # 6-month chart
    today = datetime.now()
    chart_data = []
    for i in range(5, -1, -1):
        cm = today.month - i
        cy = today.year
        if cm <= 0: cm += 12; cy -= 1
        m_sales = sum(s.amount for s in Sale.query.filter(
            Sale.user_id == user_id,
            extract('year', Sale.sale_date) == cy,
            extract('month', Sale.sale_date) == cm).all())
        m_exp   = sum(e.amount for e in Expense.query.filter(
            Expense.user_id == user_id,
            extract('year', Expense.expense_date) == cy,
            extract('month', Expense.expense_date) == cm).all())
        chart_data.append({"month": datetime(cy, cm, 1).strftime('%b %Y'),
                            "income": m_sales, "expenses": m_exp})

    return jsonify({"success": True,
        "total_sales": total_sales, "total_gst": total_gst,
        "total_expenses": total_expenses, "expense_by_category": categories,
        "gross_profit": gross_profit, "net_profit": net_profit,
        "chart_data": chart_data}), 200


# ============================================================
# REST API — Cash Book
# ============================================================

@app.route('/api/cashbook', methods=['GET'])
def get_cashbook():
    user_id    = request.args.get('user_id')
    entry_date = request.args.get('date', date.today().isoformat())
    if not user_id:
        return jsonify({"success": False, "message": "user_id required"}), 400
    try:
        d = date.fromisoformat(entry_date)
    except ValueError:
        d = date.today()
    entries = CashBook.query.filter_by(user_id=user_id, entry_date=d)\
        .order_by(CashBook.created_at.desc()).all()
    cash_in  = sum(e.amount for e in entries if e.entry_type == 'cash_in')
    cash_out = sum(e.amount for e in entries if e.entry_type == 'cash_out')
    return jsonify({"success": True,
        "date": d.isoformat(), "cash_in": cash_in, "cash_out": cash_out,
        "closing_balance": cash_in - cash_out,
        "entries": [{"id": e.id, "type": e.entry_type, "amount": e.amount,
                     "description": e.description or '', "payment_mode": e.payment_mode,
                     "date": e.entry_date.isoformat()} for e in entries]}), 200


@app.route('/api/cashbook/add', methods=['POST'])
def add_cashbook_entry():
    data = request.json or {}
    required = ['user_id', 'type', 'amount']
    if not all(k in data for k in required):
        return jsonify({"success": False, "message": "Missing required fields"}), 400
    if data['type'] not in ('cash_in', 'cash_out'):
        return jsonify({"success": False, "message": "type must be cash_in or cash_out"}), 400
    try:
        entry = CashBook(user_id=data['user_id'], entry_type=data['type'],
                         amount=float(data['amount']),
                         description=data.get('description', ''),
                         payment_mode=data.get('payment_mode', 'cash'),
                         entry_date=date.fromisoformat(data.get('date', date.today().isoformat())))
        db.session.add(entry)
        db.session.commit()
        return jsonify({"success": True, "message": "Entry added successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/cashbook/summary', methods=['GET'])
def cashbook_monthly_summary():
    user_id = request.args.get('user_id')
    month   = request.args.get('month', date.today().strftime('%Y-%m'))
    if not user_id:
        return jsonify({"success": False, "message": "user_id required"}), 400
    try:
        y, m = month.split('-')
        entries = CashBook.query.filter(CashBook.user_id == user_id,
            extract('year', CashBook.entry_date) == int(y),
            extract('month', CashBook.entry_date) == int(m)).all()
        total_in  = sum(e.amount for e in entries if e.entry_type == 'cash_in')
        total_out = sum(e.amount for e in entries if e.entry_type == 'cash_out')
        return jsonify({"success": True, "month": month,
            "total_in": total_in, "total_out": total_out,
            "net": total_in - total_out}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ============================================================
# REST API — Payment Reminders
# ============================================================

@app.route('/api/reminders', methods=['GET'])
def get_reminders():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "user_id required"}), 400
    today_date = date.today()
    reminders = PaymentReminder.query.filter(
        PaymentReminder.user_id == user_id,
        PaymentReminder.status != 'paid'
    ).order_by(PaymentReminder.due_date).all()
    # Auto-update overdue
    for r in reminders:
        if r.due_date < today_date and r.status == 'pending':
            r.status = 'overdue'
    db.session.commit()
    return jsonify({"success": True, "reminders": [
        {"id": r.id,
         "customer_name": r.customer.name if r.customer else "—",
         "amount_due": r.amount_due,
         "due_date": r.due_date.isoformat(),
         "status": r.status, "note": r.note or '',
         "days_diff": (r.due_date - today_date).days}
        for r in reminders
    ]}), 200


@app.route('/api/reminders/add', methods=['POST'])
def add_reminder():
    data = request.json or {}
    required = ['user_id', 'amount_due', 'due_date']
    if not all(k in data for k in required):
        return jsonify({"success": False, "message": "Missing required fields"}), 400
    try:
        r = PaymentReminder(user_id=data['user_id'],
                            customer_id=data.get('customer_id') or None,
                            amount_due=float(data['amount_due']),
                            due_date=date.fromisoformat(data['due_date']),
                            note=data.get('note', ''))
        db.session.add(r)
        db.session.commit()
        return jsonify({"success": True, "message": "Reminder added"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/reminders/<int:rid>/mark-paid', methods=['POST'])
def mark_reminder_paid(rid):
    r = PaymentReminder.query.get_or_404(rid)
    r.status = 'paid'
    try:
        db.session.commit()
        return jsonify({"success": True, "message": "Marked as paid"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


# ============================================================
# REST API — Deadlines (data API only — no separate page)
# ============================================================

@app.route('/api/deadlines', methods=['GET'])
def get_deadlines():
    deadlines = Deadline.query.all()
    return jsonify({"success": True, "deadlines": [
        {"return_name": d.return_name, "applicable_to": d.applies_to,
         "frequency": d.frequency, "due_day": d.due_day} for d in deadlines
    ]}), 200


# ============================================================
# Init
# ============================================================

with app.app_context():
    db.create_all()
    seed_data()


if __name__ == '__main__':
    app.run(debug=True, port=5000)
