import os
import json
from datetime import datetime
from flask import Flask, send_from_directory, jsonify, render_template, request
import matplotlib
matplotlib.use('Agg')  # ФИКС: Отключаем GUI-рендеринг
import matplotlib.pyplot as plt
import pandas as pd
import subprocess
import threading  # Импортируем threading для многозадачности

app = Flask(__name__, static_folder='static')

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

@app.route("/")
def index():
    return render_template("index.html")

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

# Функция для запуска бота
def run_bot():
    subprocess.call(["python", "C:\\time server\\tg_bots.py"])

# Запускаем бота в отдельном потоке
threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1356, debug=True, threaded=False)  # Потоки отключены для matplotlib