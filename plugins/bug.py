# plugin.py
def on_tick(data):
    # вызывается каждую минуту, например
    print("Текущее приложение:", data['active_app'])

def on_start():
    print("Плагин запущен!")
