from plyer import notification

class Plugin:
    def __init__(self, app):
        self.app = app
        self.current_app = None
        self.current_duration = 0

    def handle_event(self, event, data):
        if event == "app_switched":
            if self.current_app and self.current_duration >= 1800:  /
from plyer import notification

class Plugin:
    def __init__(self, app):
        self.app = app
        self.current_app = None
        self.current_duration = 0

    def handle_event(self, event, data):
        if event == "app_switched":
            if self.current_app and self.current_duration >= 1800:  /
System: * Today's date and time is 09:13 AM CEST on Saturday, June 14, 2025.
