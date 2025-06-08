from plyer import notification

class Plugin:
    def __init__(self, app):
        self.app = app
        self.current_app = None
        self.current_duration = 0

    def handle_event(self, event, data):
        if event == "app_switched":
            if self.current_app and self.current_duration >= 1800:
                # Add your notification logic here
                notification.notify(
                    title="Long Session Alert",
                    message=f"You have used {self.current_app} for more than 30 minutes.",
                    timeout=10
                )
            self.current_app = data.get("app_name")
            self.current_duration = 0