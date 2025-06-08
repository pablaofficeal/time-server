from plyer import notification

class Plugin:
    def __init__(self, app, config):
        self.app = app
        self.current_app = None
        self.current_duration = 0
        self.notification_interval = config.get("interval_minutes", 30) * 60  # Интервал в секундах
        self.app.save_log_data("Plugin", f"Push Notifications Plugin initialized with interval {self.notification_interval/60} minutes")

    def handle_event(self, event, data):
        if event == "tracking_started":
            self.current_app = None
            self.current_duration = 0
        elif event == "app_switched":
            if self.current_app and self.current_duration >= self.notification_interval:
                self.send_notification(self.current_app, self.current_duration)
            self.current_app = data["app_name"]
            self.current_duration = data["duration"]
        elif event == "tracking_stopped":
            if self.current_app and self.current_duration >= self.notification_interval:
                self.send_notification(self.current_app, self.current_duration)
            self.current_app = None
            self.current_duration = 0

    def send_notification(self, app_name, duration):
        minutes = duration // 60
        notification.notify(
            title="Time Tracker: Long Session Alert",
            message=f"You have been using {app_name} for {minutes} minutes!",
            timeout=10
        )
from plyer import notification

class Plugin:
    def __init__(self, app, config):
        self.app = app
        self.current_app = None
        self.current_duration = 0
        self.notification_interval = config.get("interval_minutes", 30) * 60  # Интервал в секундах
        self.app.save_log_data("Plugin", f"Push Notifications Plugin initialized with interval {self.notification_interval/60} minutes")

    def handle_event(self, event, data):
        if event == "tracking_started":
            self.current_app = None
            self.current_duration = 0
        elif event == "app_switched":
            if self.current_app and self.current_duration >= self.notification_interval:
                self.send_notification(self.current_app, self.current_duration)
            self.current_app = data["app_name"]
            self.current_duration = data["duration"]
        elif event == "tracking_stopped":
            if self.current_app and self.current_duration >= self.notification_interval:
                self.send_notification(self.current_app, self.current_duration)
            self.current_app = None
            self.current_duration = 0

    def send_notification(self, app_name, duration):
        minutes = duration // 60
        notification.notify(
            title="Time Tracker: Long Session Alert",
            message=f"You have been using {app_name} for {minutes} minutes!",
            timeout=10
        )
        self.app.save_log_data("Plugin Notification", f"Sent notification for {app_name} after {minutes} minutes")
