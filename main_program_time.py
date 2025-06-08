import customtkinter as ctk
import psutil
import win32gui
import win32process
import time
import json
import os
from datetime import datetime, timedelta
import threading
from pathlib import Path
from plyer import notification
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import importlib.util
import sys

# Настройка темы CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class PluginManager:
    def __init__(self, app):
        self.app = app
        self.plugins_path = self.app.appdata_path / "plugins"
        self.plugins_path.mkdir(exist_ok=True)
        self.plugins_config_file = self.app.appdata_path / "plugins.json"
        self.plugins = self.load_plugins_config()
        self.loaded_plugins = {}

    def load_plugins_config(self):
        if self.plugins_config_file.exists():
            with open(self.plugins_config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_plugins_config(self):
        with open(self.plugins_config_file, "w", encoding="utf-8") as f:
            json.dump(self.plugins, f, indent=4, ensure_ascii=False)

    def load_plugin(self, plugin_name):
        if plugin_name in self.plugins and self.plugins[plugin_name]["enabled"]:
            try:
                plugin_path = self.plugins_path / f"{plugin_name}.py"
                spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[plugin_name] = module
                spec.loader.exec_module(module)
                self.loaded_plugins[plugin_name] = module.Plugin(self.app, self.plugins[plugin_name].get("config", {}))
                self.app.save_log_data("Plugin", f"Loaded plugin {plugin_name}")
            except Exception as e:
                self.app.save_log_data("Plugin Error", f"Failed to load plugin {plugin_name}: {str(e)}")

    def unload_plugin(self, plugin_name):
        if plugin_name in self.loaded_plugins:
            del self.loaded_plugins[plugin_name]
            if plugin_name in sys.modules:
                del sys.modules[plugin_name]
            self.app.save_log_data("Plugin", f"Unloaded plugin {plugin_name}")

    def run_plugins(self, event, data):
        for plugin_name, plugin in self.loaded_plugins.items():
            try:
                plugin.handle_event(event, data)
            except Exception as e:
                self.app.save_log_data("Plugin Error", f"Plugin {plugin_name} failed on event {event}: {str(e)}")

class TimeTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Computer Time Tracker")
        self.root.geometry("1000x800")

        # Путь к папке AppData
        self.appdata_path = Path(os.getenv("APPDATA")) / "TimeTracker"
        self.appdata_path.mkdir(exist_ok=True)
        self.json_file = self.appdata_path / "usage.json"
        self.log_file = self.appdata_path / "logs.json"

        # Инициализация данных
        self.usage_data = self.load_usage_data()
        self.log_data = self.load_log_data()

        # Переменные для отслеживания
        self.is_tracking = False
        self.current_app = ""
        self.start_time = None
        self.total_time = 0
        self.last_app = ""
        self.last_file = ""
        self.last_time = None
        self.max_hours = 0
        self.app_times = {}
        self.notification_thread = None

        # Инициализация менеджера плагинов
        self.plugin_manager = PluginManager(self)

        # Создание интерфейса
        self.create_widgets()

        # Загрузка плагинов после создания интерфейса
        self.load_plugins()

        # Запуск проверки уведомлений
        self.notification_thread = threading.Thread(target=self.check_notifications, daemon=True)
        self.notification_thread.start()

    def load_usage_data(self):
        if self.json_file.exists():
            with open(self.json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                valid_data = [
                    entry for entry in data
                    if isinstance(entry, dict) and all(key in entry for key in ["app_name", "file_name", "start_time", "duration"])
                ]
                if len(data) != len(valid_data):
                    self.save_log_data("Data Validation", f"Filtered {len(data) - len(valid_data)} invalid entries from usage data")
                return valid_data
        return []

    def load_log_data(self):
        if self.log_file.exists():
            with open(self.log_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def save_usage_data(self):
        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump(self.usage_data, f, indent=4, ensure_ascii=False)

    def save_log_data(self, action, details):
        self.log_data.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
            "details": details
        })
        with open(self.log_file, "w", encoding="utf-8") as f:
            json.dump(self.log_data, f, indent=4, ensure_ascii=False)
        self.update_logs()

    def create_widgets(self):
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.label = ctk.CTkLabel(
            self.main_frame,
            text="Computer Time Tracker",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.label.pack(pady=10)

        self.tab_view = ctk.CTkTabview(self.main_frame)
        self.tab_view.pack(pady=10, padx=10, fill="both", expand=True)

        tracker_tab = self.tab_view.add("Tracker")
        stats_tab = self.tab_view.add("Statistics")
        graphs_tab = self.tab_view.add("Graphs")
        settings_tab = self.tab_view.add("Settings")
        logs_tab = self.tab_view.add("Logs")
        plugins_tab = self.tab_view.add("Plugins")

        self.create_tracker_tab(tracker_tab)
        self.create_stats_tab(stats_tab)
        self.create_graphs_tab(graphs_tab)
        self.create_settings_tab(settings_tab)
        self.create_logs_tab(logs_tab)
        self.create_plugins_tab(plugins_tab)

    def create_tracker_tab(self, tab):
        self.toggle_button = ctk.CTkButton(
            tab,
            text="Start Tracking",
            command=self.toggle_tracking,
            width=200,
            height=40,
            font=ctk.CTkFont(size=16)
        )
        self.toggle_button.pack(pady=20)

        self.current_app_label = ctk.CTkLabel(
            tab,
            text="Current: None",
            font=ctk.CTkFont(size=14)
        )
        self.current_app_label.pack(pady=10)

        self.total_time_label = ctk.CTkLabel(
            tab,
            text="Total time: 0h 0m 0s",
            font=ctk.CTkFont(size=14)
        )
        self.total_time_label.pack(pady=10)

    def create_stats_tab(self, tab):
        self.stats_text = ctk.CTkTextbox(tab, height=400, width=600, font=ctk.CTkFont(size=12))
        self.stats_text.pack(pady=10)

        filter_frame = ctk.CTkFrame(tab)
        filter_frame.pack(pady=10)
        ctk.CTkLabel(filter_frame, text="Filter by days:").pack(side="left", padx=5)
        self.filter_days = ctk.CTkOptionMenu(
            filter_frame,
            values=["1", "3", "7", "30", "All"],
            command=self.update_stats
        )
        self.filter_days.pack(side="left", padx=5)

        refresh_button = ctk.CTkButton(
            tab,
            text="Refresh Stats",
            command=lambda: self.update_stats(self.filter_days.get()),
            width=150
        )
        refresh_button.pack(pady=10)

        self.update_stats("All")

    def create_graphs_tab(self, tab):
        self.figure, self.ax = plt.subplots(figsize=(8, 4))
        self.canvas = FigureCanvasTkAgg(self.figure, master=tab)
        self.canvas.get_tk_widget().pack(pady=10)

        filter_frame = ctk.CTkFrame(tab)
        filter_frame.pack(pady=10)
        ctk.CTkLabel(filter_frame, text="Graph period (days):").pack(side="left", padx=5)
        self.graph_days = ctk.CTkOptionMenu(
            filter_frame,
            values=["1", "3", "7", "30"],
            command=self.update_graph
        )
        self.graph_days.pack(side="left", padx=5)

        self.update_graph("7")

    def create_settings_tab(self, tab):
        ctk.CTkLabel(
            tab,
            text="Settings",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)

        ctk.CTkLabel(
            tab,
            text=f"Data storage: {self.json_file}"
        ).pack(pady=5)

        ctk.CTkLabel(
            tab,
            text="Max hours per app:"
        ).pack(pady=5)
        self.max_hours_entry = ctk.CTkEntry(tab, width=100)
        self.max_hours_entry.pack(pady=5)
        self.max_hours_entry.insert(0, "6")

        ctk.CTkButton(
            tab,
            text="Apply Max Hours",
            command=self.apply_max_hours,
            width=150
        ).pack(pady=10)

        ctk.CTkButton(
            tab,
            text="Clear All Data",
            command=self.clear_data,
            fg_color="red",
            hover_color="darkred",
            width=150
        ).pack(pady=10)

    def create_logs_tab(self, tab):
        self.logs_text = ctk.CTkTextbox(tab, height=400, width=600, font=ctk.CTkFont(size=12))
        self.logs_text.pack(pady=10)
        self.update_logs()

    def create_plugins_tab(self, tab):
        ctk.CTkLabel(
            tab,
            text="Plugins",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)

        self.plugins_frame = ctk.CTkFrame(tab)
        self.plugins_frame.pack(pady=10, fill="both", expand=True)

        self.update_plugins_list()

        ctk.CTkButton(
            tab,
            text="Install Plugin",
            command=self.install_plugin,
            width=150
        ).pack(pady=10)

    def install_plugin(self):
        file_path = ctk.filedialog.askopenfilename(
            filetypes=[("Python files", "*.py")],
            initialdir=str(self.plugin_manager.plugins_path)
        )
        if file_path:
            plugin_name = Path(file_path).stem
            destination = self.plugin_manager.plugins_path / f"{plugin_name}.py"
            if not destination.exists():
                with open(file_path, "rb") as src, open(destination, "wb") as dst:
                    dst.write(src.read())
                self.plugin_manager.plugins[plugin_name] = {"enabled": True, "config": {}}
                self.plugin_manager.save_plugins_config()
                self.plugin_manager.load_plugin(plugin_name)
                self.update_plugins_list()
                self.save_log_data("Plugin", f"Installed plugin {plugin_name}")

    def update_plugins_list(self):
        for widget in self.plugins_frame.winfo_children():
            widget.destroy()

        for plugin_name, config in self.plugin_manager.plugins.items():
            frame = ctk.CTkFrame(self.plugins_frame)
            frame.pack(fill="x", pady=5, padx=5)

    def load_log_data(self):
        if self.log_file.exists():
            with open(self.log_file, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            return []

    def save_usage_data(self):
        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump(self.usage_data, f, indent=4, ensure_ascii=False)

    def save_log_data(self, action, details):
        self.log_data.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
            "details": details
        })
        with open(self.log_file, "w", encoding="utf-8") as f:
            json.dump(self.log_data, f, indent=4, ensure_ascii=False)
        self.update_logs()

    def create_widgets(self):
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.label = ctk.CTkLabel(
            self.main_frame,
            text="Computer Time Tracker",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.label.pack(pady=10)

        self.tab_view = ctk.CTkTabview(self.main_frame)
        self.tab_view.pack(pady=10, padx=10, fill="both", expand=True)

        tracker_tab = self.tab_view.add("Tracker")
        stats_tab = self.tab_view.add("Statistics")
        graphs_tab = self.tab_view.add("Graphs")
        settings_tab = self.tab_view.add("Settings")
        logs_tab = self.tab_view.add("Logs")
        plugins_tab = self.tab_view.add("Plugins")

        self.create_tracker_tab(tracker_tab)
        self.create_stats_tab(stats_tab)
        self.create_graphs_tab(graphs_tab)
        self.create_settings_tab(settings_tab)
        self.create_logs_tab(logs_tab)
        self.create_plugins_tab(plugins_tab)

    def create_tracker_tab(self, tab):
        self.toggle_button = ctk.CTkButton(
            tab,
            text="Start Tracking",
            command=self.toggle_tracking,
            width=200,
            height=40,
            font=ctk.CTkFont(size=16)
        )
        self.toggle_button.pack(pady=20)

        self.current_app_label = ctk.CTkLabel(
            tab,
            text="Current: None",
            font=ctk.CTkFont(size=14)
        )
        self.current_app_label.pack(pady=10)

        self.total_time_label = ctk.CTkLabel(
            tab,
            text="Total time: 0h 0m 0s",
            font=ctk.CTkFont(size=14)
        )
        self.total_time_label.pack(pady=10)

    def create_stats_tab(self, tab):
        self.stats_text = ctk.CTkTextbox(tab, height=400, width=600, font=ctk.CTkFont(size=12))
        self.stats_text.pack(pady=10)

        filter_frame = ctk.CTkFrame(tab)
        filter_frame.pack(pady=10)
        ctk.CTkLabel(filter_frame, text="Filter by days:").pack(side="left", padx=5)
        self.filter_days = ctk.CTkOptionMenu(
            filter_frame,
            values=["1", "3", "7", "30", "All"],
            command=self.update_stats
        )
        self.filter_days.pack(side="left", padx=5)

        refresh_button = ctk.CTkButton(
            tab,
            text="Refresh Stats",
            command=lambda: self.update_stats(self.filter_days.get()),
            width=150
        )
        refresh_button.pack(pady=10)

        self.update_stats("All")

    def create_graphs_tab(self, tab):
        self.figure, self.ax = plt.subplots(figsize=(8, 4))
        self.canvas = FigureCanvasTkAgg(self.figure, master=tab)
        self.canvas.get_tk_widget().pack(pady=10)

        filter_frame = ctk.CTkFrame(tab)
        filter_frame.pack(pady=10)
        ctk.CTkLabel(filter_frame, text="Graph period (days):").pack(side="left", padx=5)
        self.graph_days = ctk.CTkOptionMenu(
            filter_frame,
            values=["1", "3", "7", "30"],
            command=self.update_graph
        )
        self.graph_days.pack(side="left", padx=5)

        self.update_graph("7")

    def create_settings_tab(self, tab):
        ctk.CTkLabel(
            tab,
            text="Settings",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)

        ctk.CTkLabel(
            tab,
            text=f"Data storage: {self.json_file}"
        ).pack(pady=5)

        ctk.CTkLabel(
            tab,
            text="Max hours per app:"
        ).pack(pady=5)
        self.max_hours_entry = ctk.CTkEntry(tab, width=100)
        self.max_hours_entry.pack(pady=5)
        self.max_hours_entry.insert(0, "6")

        ctk.CTkButton(
            tab,
            text="Apply Max Hours",
            command=self.apply_max_hours,
            width=150
        ).pack(pady=10)

        ctk.CTkButton(
            tab,
            text="Clear All Data",
            command=self.clear_data,
            fg_color="red",
            hover_color="darkred",
            width=150
        ).pack(pady=10)

    def create_logs_tab(self, tab):
        self.logs_text = ctk.CTkTextbox(tab, height=400, width=600, font=ctk.CTkFont(size=12))
        self.logs_text.pack(pady=10)
        self.update_logs()

    def create_plugins_tab(self, tab):
        ctk.CTkLabel(
            tab,
            text="Plugins",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)

        self.plugins_frame = ctk.CTkFrame(tab)
        self.plugins_frame.pack(pady=10, fill="both", expand=True)

        self.update_plugins_list()

        ctk.CTkButton(
            tab,
            text="Install Plugin",
            command=self.install_plugin,
            width=150
        ).pack(pady=10)

    def install_plugin(self):
        file_path = ctk.filedialog.askopenfilename(
            filetypes=[("Python files", "*.py")],
            initialdir=str(self.plugin_manager.plugins_path)
        )
        if file_path:
            plugin_name = Path(file_path).stem
            destination = self.plugin_manager.plugins_path / f"{plugin_name}.py"
            if not destination.exists():
                with open(file_path, "rb") as src, open(destination, "wb") as dst:
                    dst.write(src.read())
                self.plugin_manager.plugins[plugin_name] = {"enabled": True, "config": {}}
                self.plugin_manager.save_plugins_config()
                self.plugin_manager.load_plugin(plugin_name)
                self.update_plugins_list()
                self.save_log_data("Plugin", f"Installed plugin {plugin_name}")

    def update_plugins_list(self):
        for widget in self.plugins_frame.winfo_children():
            widget.destroy()

        for plugin_name, config in self.plugin_manager.plugins.items():
            frame = ctk.CTkFrame(self.plugins_frame)
            frame.pack(fill="x", pady=5, padx=5)

            ctk.CTkLabel(frame, text=plugin_name).pack(side="left", padx=5)
            switch = ctk.CTkSwitch(
                frame,
                text="Enabled",
                command=lambda pn=plugin_name: self.toggle_plugin(pn),
                onvalue=1,
                offvalue=0
            )
            switch.pack(side="left", padx=5)
            if config["enabled"]:
                switch.select()

            ctk.CTkButton(
                frame,
                text="Remove",
                command=lambda pn=plugin_name: self.remove_plugin(pn),
                fg_color="red",
                hover_color="darkred",
                width=100
            ).pack(side="right", padx=5)

    def toggle_plugin(self, plugin_name):
        self.plugin_manager.plugins[plugin_name]["enabled"] = not self.plugin_manager.plugins[plugin_name]["enabled"]
        self.plugin_manager.save_plugins_config()
        if self.plugin_manager.plugins[plugin_name]["enabled"]:
            self.plugin_manager.load_plugin(plugin_name)
        else:
            self.plugin_manager.unload_plugin(plugin_name)
        self.save_log_data("Plugin", f"Plugin {plugin_name} {'enabled' if self.plugin_manager.plugins[plugin_name]['enabled'] else 'disabled'}")

    def remove_plugin(self, plugin_name):
        self.plugin_manager.unload_plugin(plugin_name)
        os.remove(self.plugin_manager.plugins_path / f"{plugin_name}.py")
        del self.plugin_manager.plugins[plugin_name]
        self.plugin_manager.save_plugins_config()
        self.update_plugins_list()
        self.save_log_data("Plugin", f"Removed plugin {plugin_name}")

    def load_plugins(self):
        for plugin_name in self.plugin_manager.plugins:
            if self.plugin_manager.plugins[plugin_name]["enabled"]:
                self.plugin_manager.load_plugin(plugin_name)

    def apply_max_hours(self):
        try:
            self.max_hours = float(self.max_hours_entry.get())
            self.save_log_data("Settings", f"Set max hours to {self.max_hours}")
        except ValueError:
            self.max_hours = 0

    def clear_data(self):
        self.usage_data = []
        self.save_usage_data()
        self.update_stats("All")
        self.update_graph(self.graph_days.get())
        self.save_log_data("Clear Data", "All usage data cleared")

    def toggle_tracking(self):
        if not self.is_tracking:
            self.is_tracking = True
            self.toggle_button.configure(text="Stop Tracking")
            self.start_time = time.time()
            self.last_time = datetime.now()
            self.tracker_thread = threading.Thread(target=self.track_usage, daemon=True)
            self.tracker_thread.start()
            self.save_log_data("Tracking", "Started tracking")
            self.plugin_manager.run_plugins("tracking_started", {})
        else:
            self.is_tracking = False
            self.toggle_button.configure(text="Start Tracking")
            self.current_app_label.configure(text="Current: None")
            if self.last_app and self.last_time:
                duration = int((datetime.now() - self.last_time).total_seconds())
                self.save_usage(self.last_app, self.last_file, self.last_time, duration)
                self.update_stats("All")
            self.save_log_data("Tracking", "Stopped tracking")
            self.plugin_manager.run_plugins("tracking_stopped", {})

    def get_active_window_info(self):
        try:
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            app_name = process.name()
            window_title = win32gui.GetWindowText(hwnd)

            file_name = "Unknown"
            if "notepad" in app_name.lower() or "code" in app_name.lower():
                file_name = window_title.split(" - ")[0] if " - " in window_title else window_title

            return app_name, file_name
        except:
            return "Unknown", "Unknown"

    def track_usage(self):
        while self.is_tracking:
            current_time = datetime.now()
            app_name, file_name = self.get_active_window_info()

            self.current_app_label.configure(text=f"Current: {app_name} ({file_name})")

            if app_name != self.last_app or file_name != self.last_file:
                if self.last_app and self.last_time:
                    duration = int((current_time - self.last_time).total_seconds())
                    self.save_usage(self.last_app, self.last_file, self.last_time, duration)
                    self.update_stats("All")
                    if self.last_app not in self.app_times:
                        self.app_times[self.last_app] = 0
                    self.app_times[self.last_app] += duration
                    self.plugin_manager.run_plugins("app_switched", {
                        "app_name": self.last_app,
                        "file_name": self.last_file,
                        "duration": duration
                    })

                self.last_app = app_name
                self.last_file = file_name
                self.last_time = current_time

            self.total_time = int(time.time() - self.start_time)
            hours, remainder = divmod(self.total_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.total_time_label.configure(
                text=f"Total time: {hours}h {minutes}m {seconds}s"
            )

            time.sleep(1)

    def save_usage(self, app_name, file_name, start_time, duration):
        self.usage_data.append({
            "app_name": app_name,
            "file_name": file_name,
            "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": duration
        })
        self.save_usage_data()

    def check_notifications(self):
        while True:
            if self.is_tracking and self.max_hours > 0:
                for app, total_seconds in self.app_times.items():
                    total_hours = total_seconds / 3600
                    if total_hours >= self.max_hours:
                        self.terminate_process(app)
                    elif total_hours >= self.max_hours - 0.25:
                        remaining = (self.max_hours * 3600 - total_seconds) / 60
                        notification.notify(
                            title="Time Tracker Warning",
                            message=f"App {app} will be closed in {int(remaining)} minutes!",
                            timeout=10
                        )
            time.sleep(300)

    def terminate_process(self, app_name):
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'].lower() == app_name.lower():
                    proc.terminate()
                    self.save_log_data("Process Terminated", f"Terminated {app_name} after reaching {self.max_hours} hours")
                    self.plugin_manager.run_plugins("process_terminated", {"app_name": app_name})
        except Exception as e:
            self.save_log_data("Error", f"Failed to terminate {app_name}: {str(e)}")

    def update_stats(self, days):
        self.stats_text.delete("1.0", "end")
        stats_dict = {}
        cutoff_date = datetime.now() - timedelta(days=int(days)) if days != "All" else datetime.min

        for entry in self.usage_data:
            try:
                entry_time = datetime.strptime(entry["start_time"], "%Y-%m-%d %H:%M:%S")
                if entry_time >= cutoff_date:
                    key = (entry["app_name"], entry["file_name"])
                    if key not in stats_dict:
                        stats_dict[key] = 0
                    stats_dict[key] += entry["duration"]
            except (KeyError, ValueError) as e:
                self.save_log_data("Stats Error", f"Invalid entry in usage data: {str(e)}")

        stats = f"Statistics ({days} days):\n\n"
        for (app_name, file_name), duration in sorted(stats_dict.items(), key=lambda x: x[1], reverse=True):
            hours, remainder = divmod(duration, 3600)
            minutes, seconds = divmod(remainder, 60)
            stats += f"App: {app_name}\n"
            stats += f"File: {file_name}\n"
            stats += f"Time: {hours}h {minutes}m {seconds}s\n\n"

        self.stats_text.insert("1.0", stats)

    def update_graph(self, days):
        self.ax.clear()
        stats_dict = {}
        cutoff_date = datetime.now() - timedelta(days=int(days))

        for entry in self.usage_data:
            try:
                entry_time = datetime.strptime(entry["start_time"], "%Y-%m-%d %H:%M:%S")
                if entry_time >= cutoff_date:
                    app_name = entry["app_name"]
                    if app_name not in stats_dict:
                        stats_dict[app_name] = 0
                    stats_dict[app_name] += entry["duration"] / 3600
            except (KeyError, ValueError) as e:
                self.save_log_data("Graph Error", f"Invalid entry in usage data: {str(e)}")

        apps = list(stats_dict.keys())[:5]
        hours = [stats_dict[app] for app in apps]

        self.ax.bar(apps, hours, color="skyblue")
        self.ax.set_title(f"App Usage (Last {days} Days)")
        self.ax.set_xlabel("Applications")
        self.ax.set_ylabel("Hours")
        self.ax.tick_params(axis='x', rotation=45)
        self.figure.tight_layout()
        self.canvas.draw()

    def update_logs(self):
        self.logs_text.delete("1.0", "end")
        logs = "Logs:\n\n"
        for entry in self.log_data[-50:]:
            logs += f"[{entry['timestamp']}] {entry['action']}: {entry['details']}\n"
        self.logs_text.insert("1.0", logs)

if __name__ == "__main__":
    root = ctk.CTk()
    app = TimeTrackerApp(root)
    root.mainloop()
