from plyer import notification

class Plugin:
    def __init__(self, app, config=None):
        self.app = app
        self.config = config or {}
        self.current_app = None
        self.current_duration = 0
        self.app.save_log_data("Plugin", "Long Session Alert Plugin initialized")

    def handle_event(self, event, data):
        if event == "app_switched":
            if self.current_app and self.current_duration >= 1800:
                notification.notify(
                    title="Long Session Alert",
                    message=f"You have used {self.current_app} for more than 30 minutes.",
                    timeout=10
                )
                self.app.save_log_data("Plugin Notification", f"Sent long session alert for {self.current_app}")
            self.current_app = data.get("app_name")
            self.current_duration = data.get("duration", 0)
        elif event == "time_update":
            if self.current_app:
                self.current_duration += data.get("elapsed_seconds", 0)