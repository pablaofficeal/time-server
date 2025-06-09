import os
import json
from datetime import datetime
from flask import Flask, send_from_directory, jsonify, render_template, request
import matplotlib
matplotlib.use('Agg')  # <-- Должен быть ДО import pyplot
import matplotlib.pyplot as plt
import pandas as pd
import subprocess
import threading  # Импортируем threading для многозадачности
from flask_sqlalchemy import SQLAlchemy
from flask import session

if not os.path.exists('database'):
    os.makedirs('database')

app = Flask(__name__, static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database/TimeTracker.db'
app.secret_key = os.urandom(24)  # Это нужно для работы session
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    tasks = db.relationship('Task', backref='user', lazy=True)
    
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Абсолютные пути
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
JSON_PATH = r"C:\Users\pavlo\AppData\Roaming\TimeTracker\usage.json"

def load_data():
    """Загружает JSON с проверкой кодировки"""
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка загрузки JSON: {e}")
        return []

def generate_plot():
    """Генерирует график без ошибок потоков"""
    data = load_data()
    if not data:
        return None

    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["start_time"]).dt.date
    df["hours"] = df["duration"] / 3600
    daily_usage = df.groupby("date")["hours"].sum().reset_index()

    plt.figure(figsize=(12, 6))
    plt.bar(daily_usage["date"], daily_usage["hours"], color="#4CAF50")
    plt.title("Computer Usage (Hours per Day)")
    plt.xlabel("Date")
    plt.ylabel("Hours")
    plt.xticks(rotation=45)
    plt.tight_layout()

    os.makedirs(STATIC_DIR, exist_ok=True)
    plot_path = os.path.join(STATIC_DIR, "usage_plot.png")
    plt.savefig(plot_path)
    plt.close()
    return plot_path

with app.app_context():
    db.create_all()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()

        return render_template("home.html", username=username)
    
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['username'] = user.username  # <--- сохраняем имя в сессию
            return render_template("home.html", username=user.username)
        else:
            return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")


@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/profile")
def profile():
    username = session.get('username')  # <-- берём из сессии
    if not username:
        return render_template("login.html", error="Вы не авторизованы")  # или редирект
    current_user = User.query.filter_by(username=username).first()
    if not current_user:
        return "User not found", 404
    return render_template("profile.html", username=current_user.username)

@app.route("/logout")
def logout():
    session.pop('username', None)
    return render_template("login.html", message="Вы вышли из аккаунта")


@app.route("/api/data")
def api_data():
    return jsonify(load_data())

@app.route("/api/plot")
def api_plot():
    range_days = request.args.get("range", default=1, type=int)
    data = load_data()

    if not data:
        return jsonify({"error": "No data"}), 500

    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["start_time"]).dt.date
    df["hours"] = df["duration"] / 3600

    if range_days > 0:
        cutoff_date = datetime.now().date() - pd.Timedelta(days=range_days)
        df = df[df["date"] >= cutoff_date]

    daily_usage = df.groupby("date")["hours"].sum().reset_index()

    plt.figure(figsize=(12, 6))
    plt.bar(daily_usage["date"], daily_usage["hours"], color="#4CAF50")
    plt.title(f"Computer Usage (Last {range_days} Days)" if range_days > 0 else "All Time Usage")
    plt.xlabel("Date")
    plt.ylabel("Hours")
    plt.xticks(rotation=45)
    plt.tight_layout()

    plot_path = os.path.join(STATIC_DIR, "usage_plot.png")
    plt.savefig(plot_path)
    plt.close()
    return send_from_directory(STATIC_DIR, "usage_plot.png")

@app.route("/api/apps_plot")
def api_apps_plot():
    data = load_data()
    df = pd.DataFrame(data)

    app_usage = df.groupby("app_name")["duration"].sum().reset_index()
    app_usage["hours"] = app_usage["duration"] / 3600
    app_usage = app_usage.sort_values("hours", ascending=False).head(10)

    plt.figure(figsize=(12, 6))
    plt.barh(app_usage["app_name"], app_usage["hours"], color="#2196F3")
    plt.title("Top Apps by Usage Time")
    plt.xlabel("Hours")
    plt.tight_layout()

    plot_path = os.path.join(STATIC_DIR, "apps_plot.png")
    plt.savefig(plot_path)
    plt.close()
    return send_from_directory(STATIC_DIR, "apps_plot.png")

@app.route("/api/online")
def api_online():
    data = load_data()
    if not data:
        return jsonify({"online_apps": 0, "error": "Нет данных"}), 200

    df = pd.DataFrame(data)
    online_apps = df["app_name"].nunique()  # Считаем уникальные приложения
    return jsonify({"online_apps": online_apps})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1356, debug=False, threaded=False)