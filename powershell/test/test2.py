import subprocess
import json
import os

def scan_all_drivers():
    try:
        result = subprocess.check_output("driverquery /v /fo csv", shell=True, text=True)
        lines = result.strip().split('\n')
        headers = lines[0].split('","')
        headers = [h.replace('"', '') for h in headers]

        drivers = []
        for line in lines[1:]:
            values = line.strip().split('","')
            values = [v.replace('"', '') for v in values]
            entry = dict(zip(headers, values))
            drivers.append({
                "Имя": entry.get("Display Name", "N/A"),
                "Состояние": entry.get("State", "N/A"),
                "Путь": entry.get("Path", "N/A"),
                "Тип": entry.get("Type", "N/A")
            })

        return drivers

    except subprocess.CalledProcessError as e:
        print(f"[!] Ошибка при выполнении команды: {e}")
        return []

def save_to_json(data, filename="drivers_report.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"[+] Данные сохранены в файл {filename}")

if __name__ == "__main__":
    print("[*] Сканирую драйвера... Это может занять пару секунд.\n")
    drivers = scan_all_drivers()

    for d in drivers:
        print(f"Имя: {d['Имя']}")
        print(f"Состояние: {d['Состояние']}")
        print(f"Путь: {d['Путь']}")
        print(f"Тип: {d['Тип']}")
        print("-" * 40)

    save_to_json(drivers)
