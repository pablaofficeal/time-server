import customtkinter as ctk
from tkinter import filedialog
import json
import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import datetime
import os

HISTORY_FILE = "history.json"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def log_event(event_type, details=""):
    event = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "event": event_type,
        "details": details
    }

    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
    else:
        history = []

    history.append(event)

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)


class TimeTrackerVisualizer(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("⏱️ Time Tracker Visualizer")
        self.geometry("600x350")

        self.label = ctk.CTkLabel(self, text="Загрузите JSON-файл со статистикой по приложениям:")
        self.label.pack(pady=15)

        self.select_button = ctk.CTkButton(self, text="Выбрать JSON", command=self.load_json)
        self.select_button.pack(pady=10)

        self.status_label = ctk.CTkLabel(self, text="", text_color="orange")
        self.status_label.pack(pady=10)

        log_event("AppStarted", "Программа запущена")

    def load_json(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if not file_path:
            self.status_label.configure(text="Файл не выбран")
            log_event("FileOpenCanceled")
            return

        log_event("FileOpened", f"Открыт файл: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.parse_and_visualize(data, file_path)

        except Exception as e:
            self.status_label.configure(text=f"Ошибка: {e}")
            log_event("FileOpenError", str(e))

    def parse_and_visualize(self, data, path):
        program_times = defaultdict(int)

        for record in data:
            app = record.get("app_name", "Unknown")
            dur = record.get("duration", 0)
            program_times[app] += dur

        filtered = {k: v for k, v in program_times.items() if v > 0 and k != "Unknown"}

        if not filtered:
            self.status_label.configure(text="Нет данных для отображения")
            log_event("GraphSkipped", "Нет данных после фильтрации")
            return

        total = sum(filtered.values())
        threshold = total * 0.02
        major_apps = {k: v for k, v in filtered.items() if v >= threshold}

        if not major_apps:
            self.status_label.configure(text="Нет приложений, превышающих 2% активности")
            log_event("GraphSkipped", "Все данные < 2%")
            return

        apps = list(major_apps.keys())
        durations_min = [round(v / 60, 2) for v in major_apps.values()]

        plt.figure(figsize=(8, 6))
        plt.pie(durations_min, labels=apps, autopct="%1.1f%%", startangle=140)
        plt.axis("equal")
        plt.tight_layout()

        plt.show()

        self.status_label.configure(text="График построен! 🎯")
        log_event("GraphBuilt", f"График по файлу: {os.path.basename(path)}")


if __name__ == "__main__":
    app = TimeTrackerVisualizer()
    app.mainloop()
