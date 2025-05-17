import subprocess
import wmi
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox

# Стиль Custom Tequinta (чёрно-красно-белый)
BG_COLOR = "#121212"
FG_COLOR = "#FFFFFF"
ACCENT_COLOR = "#E10600"
FONT_NAME = "Segoe UI"

def get_wifi_adapters():
    try:
        result = subprocess.check_output("netsh wlan show drivers", shell=True, encoding="utf-8")
        return result
    except Exception as e:
        return f"Ошибка при получении Wi-Fi адаптеров: {e}"

def check_drivers():
    drivers_info = []
    try:
        c = wmi.WMI()
        for item in c.Win32_PnPSignedDriver():
            if item.DeviceName and ("Wi-Fi" in item.DeviceName or "Wireless" in item.DeviceName):
                drivers_info.append({
                    "device": item.DeviceName,
                    "version": item.DriverVersion,
                    "needs_update": False  # Пока все False, потом можно логику добавить
                })
    except Exception as e:
        messagebox.showerror("Ошибка", f"Ошибка при проверке драйверов: {e}")
    return drivers_info

def search_driver(adapter_name):
    query = f"{adapter_name} driver download"
    url = f"https://www.google.com/search?q={query}"
    webbrowser.open(url)

class DriverApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Custom Tequinta Wi-Fi Driver Checker")
        self.geometry("700x400")
        self.configure(bg=BG_COLOR)

        self.drivers = []

        self.create_widgets()
        self.load_drivers()

    def create_widgets(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure("Treeview",
                        background=BG_COLOR,
                        foreground=FG_COLOR,
                        fieldbackground=BG_COLOR,
                        font=(FONT_NAME, 12))
        style.map('Treeview', background=[('selected', ACCENT_COLOR)])

        # Таблица драйверов
        self.tree = ttk.Treeview(self, columns=("device", "version", "update"), show="headings", selectmode="browse")
        self.tree.heading("device", text="Устройство")
        self.tree.heading("version", text="Версия драйвера")
        self.tree.heading("update", text="Нужно обновить")

        self.tree.column("device", anchor="w", width=350)
        self.tree.column("version", anchor="center", width=150)
        self.tree.column("update", anchor="center", width=120)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Кнопка обновления
        self.btn_search = tk.Button(self, text="Искать драйвер для выделенного", command=self.open_driver_link,
                                    bg=ACCENT_COLOR, fg=FG_COLOR, font=(FONT_NAME, 12, "bold"), relief="flat")
        self.btn_search.pack(pady=5)

    def load_drivers(self):
        self.drivers = check_drivers()
        for d in self.drivers:
            update_str = "Нет"
            # Простая логика: если версия меньше 10.0.0.0 — считаем, что надо обновлять (пример)
            try:
                ver_nums = list(map(int, d["version"].split('.')))
                if ver_nums[0] < 10:
                    d["needs_update"] = True
                    update_str = "Да"
            except:
                update_str = "Неизвестно"
            self.tree.insert("", tk.END, values=(d["device"], d["version"], update_str))

    def open_driver_link(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите устройство в списке!")
            return
        item = self.tree.item(selected)
        device_name = item["values"][0]
        search_driver(device_name)

if __name__ == "__main__":
    app = DriverApp()
    app.mainloop()
