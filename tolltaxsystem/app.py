# app.py
from flask import Flask, render_template, request, redirect, url_for, session
import csv
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "replace_this_with_a_strong_secret"  # <- change this in production!

# Admin credentials (change these before deploying)
ADMIN_USER = "admin"
ADMIN_PASS = "1234"

# CSV file for records
FILE_NAME = "toll_records.csv"

# Toll rates (editable)
TOLL_RATES = {
    "Car": 50,
    "Truck": 100,
    "Bike": 20,
    "Bus": 80
}

# Ensure CSV exists with header
if not os.path.exists(FILE_NAME):
    with open(FILE_NAME, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Time", "Vehicle Number", "Vehicle Type", "Toll Amount"])

# --- Protect routes: require login for pages except login & static ---
@app.before_request
def require_login():
    allowed = {"login", "static"}  # route endpoint names that don't require login
    endpoint = (request.endpoint or "")
    if endpoint not in allowed and not session.get("admin"):
        return redirect(url_for("login"))

# --- Login ---
@app.route("/", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == ADMIN_USER and password == ADMIN_PASS:
            session["admin"] = True
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid username or password!"
    return render_template("login.html", error=error)

# --- Dashboard (links to other pages) ---
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# --- Add Vehicle Entry ---
@app.route("/add", methods=["GET", "POST"])
def add_entry():
    if request.method == "POST":
        vehicle_number = request.form.get("vehicle_number", "").strip().upper()
        vehicle_type = request.form.get("vehicle_type", "")
        if not vehicle_number:
            return "Vehicle number required", 400
        if vehicle_type not in TOLL_RATES:
            return "Invalid vehicle type", 400

        toll_amount = TOLL_RATES[vehicle_type]
        now = datetime.now()
        date = now.strftime("%Y-%m-%d")
        time = now.strftime("%H:%M:%S")

        with open(FILE_NAME, mode="a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([date, time, vehicle_number, vehicle_type, toll_amount])

        return redirect(url_for("transactions"))

    return render_template("add_entry.html", toll_rates=TOLL_RATES)

# --- View All Transactions ---
@app.route("/transactions")
def transactions():
    records = []
    total_toll = 0
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r") as f:
            reader = csv.reader(f)
            next(reader, None)  # skip header if present
            for row in reader:
                if not row:
                    continue
                records.append(row)
                try:
                    total_toll += int(row[4])
                except Exception:
                    pass
    return render_template("transactions.html", records=records, total_toll=total_toll)

# --- Daily Report ---
@app.route("/daily")
def daily_report():
    today_date = datetime.now().strftime("%Y-%m-%d")
    today_records = []
    today_toll = 0
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if not row:
                    continue
                if row[0] == today_date:
                    today_records.append(row)
                    try:
                        today_toll += int(row[4])
                    except Exception:
                        pass
    return render_template("daily_report.html", today_records=today_records, today_toll=today_toll, today_date=today_date)

# --- Search Vehicle ---
@app.route("/search", methods=["GET", "POST"])
def search():
    results = []
    if request.method == "POST":
        query = request.form.get("vehicle_number", "").strip().upper()
        if query and os.path.exists(FILE_NAME):
            with open(FILE_NAME, "r") as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    if query in row[2].upper():
                        results.append(row)
    return render_template("search.html", results=results)

# --- Logout ---
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# --- Run ---
if __name__ == "__main__":
    app.run(debug=True)
